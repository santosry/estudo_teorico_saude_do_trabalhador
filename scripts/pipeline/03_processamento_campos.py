# -*- coding: utf-8 -*-
"""
03_processamento_campos.py — Do subconjunto candidato à base de Campos dos Goytacazes.
Regras:
- Filtro municipal principal: código 330100 (6 primeiros dígitos antes do hífen) E
  UF do município do EMPREGADOR == 'Rio de Janeiro' (após padronização).
- Duplicidades: linhas brutas idênticas (mesmo esquema) presentes em MAIS DE UM arquivo
  com cobertura sobreposta => mantém a 1ª ocorrência (ordem cronológica de competência
  declarada no nome do arquivo); registra remoções. Duplicatas idênticas DENTRO do mesmo
  arquivo são mantidas (podem ser eventos legítimos) e sinalizadas.
- Datas: data_acidente/nascimento/emissão em DD/MM/AAAA; afastamento pode vir AAAA/MM;
  tokens de ausência padronizados; competência (mês de referência) NÃO substitui a data.
- Idade = (data_acidente - data_nascimento) em anos completos; [14,100] fora => flag.
- Período: mantém acidentes com data entre 2018-01-01 e 2025-12-31 (fora => excluído, contado).
Saídas: dados_processados/base_cat_campos_todas_ocupacoes.csv, tabelas de fluxo e qualidade.
"""
import csv, os, re, sys, unicodedata, datetime, json
from collections import Counter, defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
ENTRADA = "dados/processados/candidatos_campos_bruto.csv"

NA_TOKENS = {"", "na", "n/a", "null", "nan", "nao informado", "não informado",
             "{ñ class}", "{n class}", "0000/00", "00/00/0000", "0000-00-00",
             "000000", "0000/00/00", "{Ñ class}".lower()}

ORDEM_ARQUIVOS = []  # ordem cronológica p/ regra de deduplicação
def chave_ordem(nome):
    n = nome.lower()
    m = re.search(r"(20\d{4})", n)
    if m: return m.group(1)
    mapa = {"cat-jul-ago-set-2018": "201807", "cat-comp-outnovdez-2018": "201810",
            "cat2018-comp01-02-03-2019": "201901", "cat-comp04-05-06-2019": "201904",
            "cat-comp07-08-09-2019": "201907", "cat-comp10-11-12-2019": "201910",
            "cat-comp01-02-03-2020": "202001", "cat-competencia-04-05-06-2020": "202004",
            "cat-competencia-07-08-09-2020": "202007", "cat-comp10-11-12-2020": "202010"}
    return mapa.get(os.path.splitext(nome)[0], "999999")

def limpa(v):
    v = re.sub(r"\s+", " ", (v or "").strip())
    return "" if v.lower() in NA_TOKENS else v

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()

def parse_dmy(v):
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", v or "")
    if not m: return None
    try: return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError: return None


def main():
    regs = list(csv.DictReader(open(ENTRADA, encoding="utf-8-sig"), delimiter=";"))
    fluxo = Counter()
    fluxo["candidatos_lidos"] = len(regs)

    # ---- deduplicação entre arquivos (linha bruta idêntica) ---------------------
    por_hash = defaultdict(list)
    for r in regs:
        por_hash[r["hash_registro"]].append(r)
    mantidos, removidos_log = [], []
    for h, grupo in por_hash.items():
        arquivos = {g["arquivo_origem"] for g in grupo}
        if len(arquivos) == 1:
            mantidos.extend(grupo)          # inclusive duplicatas internas (sinalizadas)
            if len(grupo) > 1:
                for g in grupo: g["duplicata_interna_mesmo_arquivo"] = "sim"
        else:
            grupo_ord = sorted(grupo, key=lambda g: (chave_ordem(g["arquivo_origem"]), g["id_linha"]))
            # mantém 1 por arquivo mais antigo; remove reocorrências em arquivos posteriores
            primeiro_arq = grupo_ord[0]["arquivo_origem"]
            manter = [g for g in grupo_ord if g["arquivo_origem"] == primeiro_arq]
            descartar = [g for g in grupo_ord if g["arquivo_origem"] != primeiro_arq]
            mantidos.extend(manter)
            for g in descartar:
                removidos_log.append({"hash_registro": h, "id_linha_removida": g["id_linha"],
                    "arquivo_removido": g["arquivo_origem"], "mantido_em": primeiro_arq,
                    "regra": "linha_bruta_identica_em_arquivos_sobrepostos"})
    fluxo["duplicidades_entre_arquivos_removidas"] = len(removidos_log)

    # ---- variáveis canônicas -----------------------------------------------------
    saida, problemas = [], Counter()
    controle_uf_divergente = []
    for r in mantidos:
        mun = limpa(r["municipio_empregador_bruto"])
        m = re.match(r"^(\d{6})\s*-?\s*(.*)$", mun)
        cod = m.group(1) if m else ""
        nome_mun = m.group(2).strip() if m else mun
        uf_emp = limpa(r["uf_municipio_empregador"])
        eh_campos = (cod == "330100")
        if not eh_campos:
            fluxo["excluidos_outros_municipios_com_campo_no_nome"] += 1
            continue
        if norm(uf_emp) != "rio de janeiro":
            controle_uf_divergente.append({"id_linha": r["id_linha"], "municipio": mun, "uf": uf_emp})
            fluxo["excluidos_330100_uf_nao_rj"] += 1
            continue
        fluxo["campos_330100_uf_rj"] += 1

        d_acid = parse_dmy(limpa(r["data_acidente_bruta"]))
        d_nasc = parse_dmy(limpa(r["data_nascimento_bruta"]))
        d_emis = parse_dmy(limpa(r["data_emissao_cat_bruta"]))
        if d_acid is None:
            problemas["data_acidente_invalida_ou_ausente"] += 1
            fluxo["excluidos_sem_data_acidente_valida"] += 1
            continue
        if not (datetime.date(2018, 1, 1) <= d_acid <= datetime.date(2025, 12, 31)):
            fluxo["excluidos_fora_periodo_2018_2025"] += 1
            continue
        fluxo["campos_periodo_2018_2025"] += 1

        idade = None
        if d_nasc:
            idade = d_acid.year - d_nasc.year - ((d_acid.month, d_acid.day) < (d_nasc.month, d_nasc.day))
            if idade < 14 or idade > 100:
                problemas["idade_fora_14_100"] += 1
                idade = None
        else:
            problemas["data_nascimento_invalida"] += 1

        # CBO: código = 6 dígitos; descrição = após hífen (no esquema S24A vêm combinados)
        cbo_b = limpa(r["cbo_bruto_codigo"]); cbo_d = limpa(r["cbo_bruto_descricao"])
        mm = re.match(r"^(\d{6})", cbo_b)
        cbo_cod = mm.group(1) if mm else ""
        if not cbo_cod:
            problemas["cbo_sem_codigo_6dig"] += 1
        fonte_desc = cbo_d or cbo_b
        md = re.match(r"^\d{4,6}\s*-\s*(.+)$", fonte_desc)
        cbo_desc = md.group(1).strip() if md else ("" if re.match(r"^\d+$", fonte_desc) else fonte_desc)

        cid_b = limpa(r["cid_bruto_codigo"]); cid_d = limpa(r["cid_bruto_descricao"])
        mc = re.match(r"^([A-Z]\d{2}\d?)", cid_b.replace(".", "").replace(" ", "")[:4].upper() if cid_b else "")
        cid_cod = mc.group(1) if mc else ""
        if not cid_cod and cid_d:
            mc2 = re.match(r"^([A-Z])(\d{2})\.?(\d)?", cid_d.upper())
            if mc2: cid_cod = mc2.group(1) + mc2.group(2) + (mc2.group(3) or "")
        md2 = re.match(r"^[A-Z]\d{2}\.?\d?\s+(.+)$", cid_d) if cid_d else None
        cid_desc = md2.group(1).strip() if md2 else cid_d

        cnae_cod = limpa(r["cnae_codigo"]); cnae_cod = cnae_cod if re.match(r"^\d{4}$", cnae_cod) else ""
        tempo_emissao = (d_emis - d_acid).days if (d_emis and d_emis >= d_acid) else None

        saida.append({
            "id_linha": r["id_linha"], "hash_registro": r["hash_registro"],
            "arquivo_origem": r["arquivo_origem"], "esquema": r["esquema"],
            "duplicata_interna_mesmo_arquivo": r.get("duplicata_interna_mesmo_arquivo", "nao"),
            "competencia_arquivo": chave_ordem(r["arquivo_origem"]),
            "mes_referencia_acidente_bruto": limpa(r["mes_referencia_acidente"]),
            "data_acidente": d_acid.isoformat(), "ano_acidente": d_acid.year,
            "mes_acidente": f"{d_acid.year}-{d_acid.month:02d}",
            "data_nascimento": d_nasc.isoformat() if d_nasc else "",
            "idade": idade if idade is not None else "",
            "data_emissao_cat": d_emis.isoformat() if d_emis else "",
            "tempo_acidente_emissao_dias": tempo_emissao if tempo_emissao is not None else "",
            "municipio_empregador_codigo": cod, "municipio_empregador_nome": nome_mun,
            "uf_municipio_empregador": uf_emp,
            "uf_municipio_acidente": limpa(r["uf_municipio_acidente"]),
            "cbo_codigo": cbo_cod, "cbo_descricao_original": cbo_desc,
            "cbo_bruto": cbo_b if cbo_b != cbo_cod else (cbo_d or cbo_b),
            "cid10_codigo": cid_cod, "cid10_capitulo_letra": cid_cod[:1] if cid_cod else "",
            "cid10_grupo3": cid_cod[:3] if cid_cod else "", "cid10_descricao": cid_desc,
            "cnae_classe": cnae_cod, "cnae_descricao": limpa(r["cnae_descricao"]),
            "sexo": limpa(r["sexo"]), "tipo_acidente": limpa(r["tipo_acidente"]),
            "agente_causador": limpa(r["agente_causador"]), "natureza_lesao": limpa(r["natureza_lesao"]),
            "parte_corpo_atingida": limpa(r["parte_corpo_atingida"]),
            "emitente_cat": limpa(r["emitente_cat"]), "origem_cadastramento_cat": limpa(r["origem_cadastramento_cat"]),
            "filiacao_segurado": limpa(r["filiacao_segurado"]), "especie_beneficio": limpa(r["especie_beneficio"]),
            "indica_obito_acidente": limpa(r["indica_obito_acidente"]),
        })

    os.makedirs("dados/processados", exist_ok=True)
    with open("dados/processados/base_cat_campos_todas_ocupacoes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(saida[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(saida)
    with open("dados/processados/log_duplicidades_removidas.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["hash_registro","id_linha_removida","arquivo_removido","mantido_em","regra"], delimiter=";")
        w.writeheader(); w.writerows(removidos_log)
    with open("dados/processados/controle_330100_uf_divergente.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id_linha","municipio","uf"], delimiter=";")
        w.writeheader(); w.writerows(controle_uf_divergente)
    with open("logs/fluxo_03_processamento.json", "w", encoding="utf-8") as f:
        json.dump({"fluxo": dict(fluxo), "problemas_qualidade": dict(problemas)}, f, ensure_ascii=False, indent=1)
    print(json.dumps({"fluxo": dict(fluxo), "problemas": dict(problemas)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
