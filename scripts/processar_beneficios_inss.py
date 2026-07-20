# -*- coding: utf-8 -*-
"""
processar_beneficios_inss.py
=============================
Processa os arquivos de beneficios concedidos do INSS (2018-2025).
Filtra: Campos dos Goytacazes + especies de acidente/doenca do trabalho.
Fonte: Dados Abertos INSS (download manual pelo usuario).

Formatos: CSV (;), XLSX, ZIP (contendo CSV)
Codigo Campos no INSS: 17010-RJ-Campos dos Goytacazes

Especies de trabalho (codigos B91, B92, B93, B94):
  - Auxilio Doenca por Acidente do Trabalho (B91)
  - Aposent. Invalidez Acidente Trabalho (B92)
  - Pensao por Morte por Acidente do Trabalho (B93)
  - Auxilio Acidente (B94)

NOTA: Nao ha coluna CBO nos dados de beneficios. A analise e feita por
      especie de beneficio e CID-10, nao por ocupacao.
"""
import os, csv, zipfile, tempfile, re
import pandas as pd
from collections import defaultdict, Counter

DIR_BEN = os.path.join("banco de dados", "beneficios-inss")
DIR_PROC = os.path.join("dados", "processados")
DIR_SAIDAS = os.path.join("saidas", "tabelas")
os.makedirs(DIR_PROC, exist_ok=True)
os.makedirs(DIR_SAIDAS, exist_ok=True)

# Municipio no formato do INSS
MUN_CAMPOS = "Campos dos Goytacazes"

# Especies de beneficios acidentarios (B91, B92, B93, B94)
ESPECIES_TRABALHO = [
    "Auxilio Doenca por Acidente do Trabalho",
    "Auxílio Doença por Acidente do Trabalho",
    "Aposent. Invalidez Acidente Trabalho",
    "Aposentadoria Invalidez Acidente Trabalho",
    "Pensao por Morte por Acidente do Trabalho",
    "Pensão por Morte por Acidente do Trabalho",
    "Auxilio Acidente",
    "Auxílio Acidente",
]

COLUNAS_CANONICAS = [
    "competencia", "especie", "cid_codigo", "cid_nome",
    "despacho", "dt_nascimento", "sexo", "clientela",
    "mun_resid", "vinculo_dependentes", "forma_filiacao",
    "uf", "qt_sm_rmi", "arquivo_origem"
]


def normalizar_especie(especie):
    """Remove acentos e padroniza nome da especie."""
    if not isinstance(especie, str):
        return str(especie)
    # Mapear variacoes para nomes canonicos
    e = especie.strip().lower()
    e = e.replace("�", "a").replace("�", "e").replace("�", "i")
    e = e.replace("�", "o").replace("�", "u").replace("�", "c")
    e = e.replace("�", "a").replace("�", "o").replace("�", "a")
    e = e.replace("é", "e").replace("á", "a").replace("í", "i")
    e = e.replace("ó", "o").replace("ú", "u").replace("ã", "a")
    e = e.replace("õ", "o").replace("â", "a").replace("ê", "e")
    e = e.replace("ô", "o").replace("ç", "c")

    if "auxilio doenca" in e and "acidente" in e:
        return "Auxilio Doenca por Acidente do Trabalho (B91)"
    elif "aposent" in e and "invalidez" in e and "acidente" in e:
        return "Aposent. Invalidez Acidente Trabalho (B92)"
    elif "pensao" in e and "morte" in e and "acidente" in e:
        return "Pensao por Morte por Acidente do Trabalho (B93)"
    elif "auxilio acidente" in e and "previdenciario" not in e and "doenca" not in e:
        return "Auxilio Acidente (B94)"
    else:
        return especie.strip()


def processar_csv(path, nome_arquivo):
    """Le um CSV de beneficios e retorna registros de Campos + trabalho."""
    registros = []
    try:
        for enc in ["latin-1", "utf-8", "cp1252"]:
            try:
                df = pd.read_csv(path, sep=";", encoding=enc, dtype=str)
                break
            except:
                continue

        if df is None or len(df) == 0:
            return registros

        # Normalizar nomes de colunas
        col_map = {}
        for c in df.columns:
            cl = c.strip().lower()
            if "compet" in cl:
                col_map[c] = "competencia"
            elif "espec" in cl or "esp�c" in cl:
                col_map[c] = "especie"
            elif "cid" in cl and "nome" not in cl and "descr" not in cl:
                col_map[c] = "cid_codigo"
            elif ("cid" in cl and ("nome" in cl or "descr" in cl or "." in c)):
                col_map[c] = "cid_nome"
            elif "despacho" in cl:
                col_map[c] = "despacho"
            elif "nasc" in cl:
                col_map[c] = "dt_nascimento"
            elif cl in ("sexo", "sexo."):
                col_map[c] = "sexo"
            elif "client" in cl:
                col_map[c] = "clientela"
            elif "mun" in cl and "resid" in cl:
                col_map[c] = "mun_resid"
            elif "vinculo" in cl or "v�nculo" in cl:
                col_map[c] = "vinculo_dependentes"
            elif "filia" in cl:
                col_map[c] = "forma_filiacao"
            elif cl == "uf":
                col_map[c] = "uf"
            elif "sm" in cl or "rmi" in cl:
                col_map[c] = "qt_sm_rmi"

        df = df.rename(columns=col_map)

        # Filtrar Campos
        if "mun_resid" not in df.columns:
            return registros

        mask_campos = df["mun_resid"].astype(str).str.upper().str.contains(
            "CAMPOS DOS GOYTACAZES", na=False
        )
        df = df[mask_campos]

        if len(df) == 0:
            return registros

        # Filtrar especies de trabalho
        if "especie" in df.columns:
            especie_str = df["especie"].astype(str).str.lower()
            mask_trab = especie_str.str.contains("acidente", na=False)
            df = df[mask_trab]

        if len(df) == 0:
            return registros

        # Normalizar e selecionar colunas
        for col in COLUNAS_CANONICAS:
            if col not in df.columns:
                df[col] = ""

        df["arquivo_origem"] = nome_arquivo
        df["especie"] = df["especie"].apply(normalizar_especie)

        # Selecionar apenas colunas canonicas
        cols_present = [c for c in COLUNAS_CANONICAS if c in df.columns]
        registros = df[cols_present].to_dict("records")

    except Exception as e:
        print(f"  ERRO CSV {nome_arquivo}: {e}")

    return registros


def processar_xlsx(path, nome_arquivo):
    """Le um XLSX de beneficios."""
    registros = []
    try:
        df = pd.read_excel(path, dtype=str)
        if df is None or len(df) == 0:
            return registros

        # Salvar como CSV temporario e reusar processar_csv
        tmp = os.path.join(tempfile.gettempdir(), f"_ben_{os.path.basename(path)}.csv")
        df.to_csv(tmp, sep=";", index=False, encoding="utf-8")
        registros = processar_csv(tmp, nome_arquivo)
        if os.path.exists(tmp):
            os.remove(tmp)

    except Exception as e:
        print(f"  ERRO XLSX {nome_arquivo}: {e}")

    return registros


def processar_zip(path, nome_arquivo):
    """Extrai ZIP e processa arquivos dentro."""
    registros = []
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(path, "r") as z:
                z.extractall(td)

            for f in os.listdir(td):
                full = os.path.join(td, f)
                if f.lower().endswith(".csv"):
                    regs = processar_csv(full, f"{nome_arquivo}/{f}")
                    registros.extend(regs)
                elif f.lower().endswith(".xlsx"):
                    regs = processar_xlsx(full, f"{nome_arquivo}/{f}")
                    registros.extend(regs)
    except Exception as e:
        print(f"  ERRO ZIP {nome_arquivo}: {e}")

    return registros


def extrair_ano_mes(nome):
    """Extrai ano e mes do nome do arquivo."""
    # Padroes: concedidos-MM-AAAA.csv, BEN_CONCEDIDOS_MMAAAA.xlsx,
    #          CONCEDIDOS_*MES*AAAA*.xlsx, D.SDA.PDA.001.CON.AAAAMM.*
    nome_clean = nome.upper()

    # D.SDA.PDA.001.CON.202108
    m = re.search(r"CON[\.\s]*(\d{4})(\d{2})", nome_clean)
    if m:
        return int(m.group(1)), int(m.group(2))

    # concedidos-MM-AAAA
    m = re.search(r"(\d{2})-(\d{4})", nome)
    if m:
        return int(m.group(2)), int(m.group(1))

    # BEN_CONCEDIDOS_MMAAAA
    m = re.search(r"(\d{2})(\d{4})", nome_clean)
    if m:
        return int(m.group(2)), int(m.group(1))

    # JANEIRO+2025, MÊS+DE+JULHO+2024
    meses = {
        "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "MARÇO": 3,
        "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7,
        "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10,
        "NOVEMBRO": 11, "DEZEMBRO": 12
    }
    for mes_nome, mes_num in meses.items():
        if mes_nome in nome_clean:
            m = re.search(r"(\d{4})", nome_clean)
            if m:
                return int(m.group(1)), mes_num

    # ZIP 2018: concedidos_2018.zip
    m = re.search(r"(\d{4})", nome_clean)
    if m:
        ano = int(m.group(1))
        if ano >= 2018 and ano <= 2025:
            return ano, None  # Ano completo

    return None, None


def main():
    print("=" * 70)
    print("PROCESSAMENTO BENEFICIOS CONCEDIDOS INSS")
    print("Campos dos Goytacazes | 2018-2025")
    print("Especies acidentarias: B91, B92, B93, B94")
    print("=" * 70)

    arquivos = sorted(os.listdir(DIR_BEN))
    todos_registros = []
    resumo_mensal = defaultdict(lambda: defaultdict(int))

    for nome in arquivos:
        if nome.startswith("Gloss") or nome.startswith("~"):
            continue

        path = os.path.join(DIR_BEN, nome)
        ext = nome.lower()

        print(f"\nProcessando: {nome}")

        if ext.endswith(".csv"):
            regs = processar_csv(path, nome)
        elif ext.endswith(".xlsx"):
            regs = processar_xlsx(path, nome)
        elif ext.endswith(".zip"):
            regs = processar_zip(path, nome)
        else:
            print(f"  Formato ignorado: {ext}")
            continue

        if regs:
            print(f"  {len(regs)} beneficios acidentarios em Campos")
        else:
            print(f"  0 beneficios acidentarios em Campos")

        # Extrair ano/mes para resumo
        ano, mes = extrair_ano_mes(nome)

        for r in regs:
            r["_ano"] = ano if ano else ""
            r["_mes"] = mes if mes else ""
            todos_registros.append(r)
            especie = r.get("especie", "")
            if ano:
                resumo_mensal[ano][especie] += 1

    # Salvar CSV consolidado
    if todos_registros:
        # Adicionar _ano e _mes as colunas
        cols_final = COLUNAS_CANONICAS + ["_ano", "_mes"]

        path_csv = os.path.join(DIR_PROC, "beneficios_inss_campos_2018_2025.csv")
        with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=cols_final, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(todos_registros)

        mb = os.path.getsize(path_csv) / 1e6
        print(f"\n{'='*70}")
        print(f"CSV salvo: {path_csv} ({mb:.1f} MB)")
        print(f"Total beneficios acidentarios em Campos: {len(todos_registros)}")
    else:
        print("\nNENHUM registro encontrado.")
        return

    # === RESUMO ===
    print(f"\n{'='*70}")
    print("RESUMO - Beneficios Acidentarios em Campos dos Goytacazes")
    print(f"{'='*70}")

    anos_ord = sorted([a for a in resumo_mensal if a])
    especies_set = set()
    for a in anos_ord:
        especies_set.update(resumo_mensal[a].keys())
    especies_ord = sorted(especies_set)

    # Cabecalho
    print(f"{'Especie':<52}", end="")
    for a in anos_ord:
        print(f" {a:>6}", end="")
    print(f" {'Total':>7}")
    print("-" * 90)

    totais_ano = defaultdict(int)
    for esp in especies_ord:
        print(f"  {esp[:50]:<50}", end="")
        total_esp = 0
        for a in anos_ord:
            n = resumo_mensal[a].get(esp, 0)
            print(f" {n:>6}", end="")
            total_esp += n
            totais_ano[a] += n
        print(f" {total_esp:>7}")

    print("-" * 90)
    print(f"  {'TOTAL':<50}", end="")
    total_geral = 0
    for a in anos_ord:
        print(f" {totais_ano[a]:>6}", end="")
        total_geral += totais_ano[a]
    print(f" {total_geral:>7}")

    # Salvar tabela resumo
    t_resumo = [{"especie": esp} for esp in especies_ord]
    for row, esp in zip(t_resumo, especies_ord):
        for a in anos_ord:
            row[str(a)] = resumo_mensal[a].get(esp, 0)
        row["total"] = sum(row[str(a)] for a in anos_ord)

    path_resumo = os.path.join(DIR_SAIDAS, "T40_beneficios_inss_resumo.csv")
    with open(path_resumo, "w", newline="", encoding="utf-8-sig") as f:
        cols = ["especie"] + [str(a) for a in anos_ord] + ["total"]
        writer = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        writer.writeheader()
        writer.writerows(t_resumo)
    print(f"\nTabela resumo: {path_resumo}")

    print("\nOK Script concluido.")


if __name__ == "__main__":
    main()
