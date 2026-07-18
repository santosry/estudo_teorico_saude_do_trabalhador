# -*- coding: utf-8 -*-
"""
02_ingestao_cat.py — Leitura posicional dos 58 CSV CAT/INSS (2018–2025).
- Importação POR POSIÇÃO (cabeçalhos duplicados NÃO são renomeados/sobrescritos);
- Detecção de codificação por arquivo (UTF-8-BOM vs Latin-1) e separador ';' com QUOTE_NONE;
- 4 esquemas estruturais mapeados explicitamente (24a, 24b, 25, 27 colunas);
- Estatísticas por arquivo: linhas, distribuição mensal da emissão e da data do acidente;
- Tabela de controle de TODAS as localidades contendo 'campo' no nome;
- Extração de candidatos: código municipal 330100 OU nome contendo 'campos' (para auditoria
  da exclusão dos demais municípios); o filtro definitivo (330100 + UF RJ) ocorre no script 03;
- Identificador técnico de linha (arquivo:n) e hash SHA-256 do registro bruto;
- Duplicidades exatas de linha bruta entre arquivos (hash) são contadas.
Saídas em dados_processados/ e logs/.
"""
import os, csv, io, json, hashlib, unicodedata, re
from collections import Counter, defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
DIR_DADOS = os.path.join("dados", "brutos", "cat-inss")
DIR_OUT = os.path.join("dados", "processados")
DIR_LOG = "logs"
os.makedirs(DIR_OUT, exist_ok=True); os.makedirs(DIR_LOG, exist_ok=True)

CAMPOS_CANONICOS = [
    "agente_causador", "mes_referencia_acidente", "cbo_bruto_codigo", "cbo_bruto_descricao",
    "cid_bruto_codigo", "cid_bruto_descricao", "cnae_codigo", "cnae_descricao",
    "emitente_cat", "especie_beneficio", "filiacao_segurado", "indica_obito_acidente",
    "municipio_empregador_bruto", "natureza_lesao", "origem_cadastramento_cat",
    "parte_corpo_atingida", "sexo", "tipo_acidente", "uf_municipio_acidente",
    "uf_municipio_empregador", "data_afastamento_bruta", "data_despacho_beneficio_bruta",
    "data_acidente_bruta", "data_nascimento_bruta", "data_emissao_cat_bruta",
    "tipo_empregador", "cnpj_cei_empregador",
]

# Mapeamento POSIÇÃO(0-based) -> campo canônico, por esquema.
MAPA_25 = {0:"agente_causador",1:"mes_referencia_acidente",2:"cbo_bruto_codigo",3:"cbo_bruto_descricao",
 4:"cid_bruto_codigo",5:"cid_bruto_descricao",6:"cnae_codigo",7:"cnae_descricao",8:"emitente_cat",
 9:"especie_beneficio",10:"filiacao_segurado",11:"indica_obito_acidente",12:"municipio_empregador_bruto",
 13:"natureza_lesao",14:"origem_cadastramento_cat",15:"parte_corpo_atingida",16:"sexo",17:"tipo_acidente",
 18:"uf_municipio_acidente",19:"uf_municipio_empregador",20:"data_afastamento_bruta",
 21:"data_despacho_beneficio_bruta",22:"data_acidente_bruta",23:"data_nascimento_bruta",24:"data_emissao_cat_bruta"}
MAPA_24A = {0:"agente_causador",1:"mes_referencia_acidente",2:"cbo_bruto_codigo",3:"cid_bruto_codigo",
 4:"cnae_codigo",5:"cnae_descricao",6:"emitente_cat",7:"especie_beneficio",8:"filiacao_segurado",
 9:"indica_obito_acidente",10:"municipio_empregador_bruto",11:"natureza_lesao",12:"origem_cadastramento_cat",
 13:"parte_corpo_atingida",14:"sexo",15:"tipo_acidente",16:"uf_municipio_acidente",17:"uf_municipio_empregador",
 18:"__mes_ref_dup",19:"data_despacho_beneficio_bruta",20:"data_acidente_bruta",21:"data_nascimento_bruta",
 22:"data_emissao_cat_bruta",23:"cnpj_cei_empregador"}     # CBO e CID vêm combinados "código-descrição"
MAPA_24B = {0:"agente_causador",1:"__data_acid_pos2",2:"cbo_bruto_codigo",3:"cbo_bruto_descricao",
 4:"cid_bruto_codigo",5:"cid_bruto_descricao",6:"cnae_codigo",7:"cnae_descricao",8:"emitente_cat",
 9:"especie_beneficio",10:"filiacao_segurado",11:"indica_obito_acidente",12:"municipio_empregador_bruto",
 13:"natureza_lesao",14:"origem_cadastramento_cat",15:"parte_corpo_atingida",16:"sexo",17:"tipo_acidente",
 18:"uf_municipio_acidente",19:"uf_municipio_empregador",20:"data_afastamento_bruta",
 21:"data_acidente_bruta",22:"data_nascimento_bruta",23:"__data_acid_dup"}   # sem emissão/despacho/CNPJ
MAPA_27 = {0:"agente_causador",1:"__data_acid_pos2",2:"cbo_bruto_codigo",3:"cbo_bruto_descricao",
 4:"cid_bruto_codigo",5:"cid_bruto_descricao",6:"cnae_codigo",7:"cnae_descricao",8:"emitente_cat",
 9:"especie_beneficio",10:"filiacao_segurado",11:"indica_obito_acidente",12:"municipio_empregador_bruto",
 13:"natureza_lesao",14:"origem_cadastramento_cat",15:"parte_corpo_atingida",16:"sexo",17:"tipo_acidente",
 18:"uf_municipio_acidente",19:"uf_municipio_empregador",20:"data_afastamento_bruta",
 21:"data_despacho_beneficio_bruta",22:"data_acidente_bruta",23:"data_nascimento_bruta",
 24:"data_emissao_cat_bruta",25:"tipo_empregador",26:"cnpj_cei_empregador"}

def normaliza(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()

def detecta_encoding(path):
    with open(path, "rb") as f:
        ini = f.read(4)
    return "utf-8-sig" if ini.startswith(b"\xef\xbb\xbf") else "latin-1"

def esquema_do_arquivo(header):
    n = len(header)
    if n == 25: return "S25", MAPA_25
    if n == 27: return "S27", MAPA_27
    if n == 24:
        # posição 4 (índice 3): 'CID-10' => CBO/CID combinados (S24A); 'CBO' => separados (S24B)
        return ("S24A", MAPA_24A) if header[3].strip().upper().startswith("CID") else ("S24B", MAPA_24B)
    raise ValueError(f"Esquema não previsto: {n} colunas")

def mes_de_data(d):  # dd/mm/aaaa -> aaaa-mm
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", d or "")
    return f"{m.group(3)}-{m.group(2)}" if m else None

arquivos = sorted(f for f in os.listdir(DIR_DADOS) if f.lower().endswith(".csv"))
stats_arquivos, candidatos, controle_campos = [], [], Counter()
hash_linhas = defaultdict(list)  # hash -> [(arquivo, n_linha)]
esquemas_por_arquivo = {}

for nome in arquivos:
    path = os.path.join(DIR_DADOS, nome)
    enc = detecta_encoding(path)
    with open(path, encoding=enc, errors="replace", newline="") as f:
        rd = csv.reader(f, delimiter=";", quoting=csv.QUOTE_NONE)
        header = next(rd)
        esq, mapa = esquema_do_arquivo(header)
        esquemas_por_arquivo[nome] = {"esquema": esq, "n_colunas": len(header), "codificacao": enc,
                                      "cabecalho": header}
        n_lin = n_malformada = 0
        meses_emissao, meses_acidente = Counter(), Counter()
        for i, row in enumerate(rd, start=2):
            n_lin += 1
            if len(row) != len(header):
                n_malformada += 1
                continue
            reg = {c: "" for c in CAMPOS_CANONICOS}
            for pos, campo in mapa.items():
                if not campo.startswith("__"):
                    reg[campo] = row[pos].strip()
            if esq in ("S24B", "S27"):  # posição 2 traz a data completa do acidente (dupla checagem)
                if not reg["data_acidente_bruta"]:
                    reg["data_acidente_bruta"] = row[1].strip()
            me = mes_de_data(reg["data_emissao_cat_bruta"]); ma = mes_de_data(reg["data_acidente_bruta"])
            if me: meses_emissao[me] += 1
            if ma: meses_acidente[ma] += 1
            mun = reg["municipio_empregador_bruto"]
            mun_norm = normaliza(mun)
            eh_cod = mun[:6] == "330100"
            tem_campos = "campo" in mun_norm
            if tem_campos:
                controle_campos[mun] += 1
            if eh_cod or "campos" in mun_norm:
                linha_bruta = ";".join(row)
                h = hashlib.sha256((esq + "|" + linha_bruta).encode("utf-8")).hexdigest()
                hash_linhas[h].append((nome, i))
                reg.update({"arquivo_origem": nome, "esquema": esq, "id_linha": f"{nome}:{i}",
                            "hash_registro": h})
                candidatos.append(reg)
        stats_arquivos.append({"arquivo": nome, "esquema": esq, "codificacao": enc,
            "n_colunas": len(header), "linhas_dados": n_lin, "linhas_malformadas": n_malformada,
            "meses_emissao": json.dumps(dict(sorted(meses_emissao.items())), ensure_ascii=False),
            "meses_acidente_top": json.dumps(dict(sorted(meses_acidente.items())[-40:]), ensure_ascii=False)})
        print(f"{nome}: {esq} {n_lin} linhas, malformadas={n_malformada}")

# --- saídas -------------------------------------------------------------
cols_saida = ["arquivo_origem", "esquema", "id_linha", "hash_registro"] + CAMPOS_CANONICOS
with open(os.path.join(DIR_OUT, "candidatos_campos_bruto.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols_saida, delimiter=";")
    w.writeheader(); w.writerows(candidatos)

with open(os.path.join(DIR_OUT, "estatisticas_por_arquivo.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(stats_arquivos[0].keys()), delimiter=";")
    w.writeheader(); w.writerows(stats_arquivos)

with open(os.path.join(DIR_OUT, "controle_localidades_campo.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["municipio_empregador_bruto", "n_registros"])
    for k, v in controle_campos.most_common():
        w.writerow([k, v])

dups = {h: locs for h, locs in hash_linhas.items() if len(locs) > 1}
with open(os.path.join(DIR_OUT, "duplicidades_linha_bruta.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["hash_registro", "ocorrencias", "localizacoes"])
    for h, locs in dups.items():
        w.writerow([h, len(locs), " | ".join(f"{a}:{l}" for a, l in locs)])

with open(os.path.join(DIR_LOG, "esquemas_por_arquivo.json"), "w", encoding="utf-8") as f:
    json.dump(esquemas_por_arquivo, f, ensure_ascii=False, indent=1)

tot = sum(s["linhas_dados"] for s in stats_arquivos)
print(f"\nTotal linhas lidas: {tot} | candidatos 'campos/330100': {len(candidatos)} | "
      f"hashes duplicados (subset candidatos): {len(dups)}")
