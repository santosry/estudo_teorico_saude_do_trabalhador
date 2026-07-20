# -*- coding: utf-8 -*-
"""
beneficios_inss_completo.py
============================
Processa TODOS os arquivos de beneficios INSS (CSV, XLSX, ZIP).
Filtra Campos dos Goytacazes + especies acidentarias (B91-B94).

XLSX: header na linha 1 (linha 0 = titulo)
CSV:  primeira linha = header
ZIP:  extrai e processa conteudo

Saida: dados/processados/beneficios_inss_campos_2018_2025.csv
"""
import os, csv, tempfile, zipfile, re, pandas as pd
from collections import defaultdict

DIR_BEN = os.path.join("banco de dados", "beneficios-inss")
DIR_PROC = os.path.join("dados", "processados")
DIR_SAIDAS = os.path.join("saidas", "tabelas")
os.makedirs(DIR_PROC, exist_ok=True)
os.makedirs(DIR_SAIDAS, exist_ok=True)

MUN_CAMPOS = "CAMPOS DOS GOYTACAZES"
COLUNAS_FINAL = [
    "comp_concessao", "especie", "cid", "cid_nome", "despacho",
    "dt_nascimento", "sexo", "clientela", "mun_resid",
    "vinculo_dependentes", "forma_filiacao", "uf", "qt_sm_rmi",
    "ramo_atividade", "dt_ddb", "dt_dib",
    "_ano", "_mes", "_arquivo"
]

MESES_NOME = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12
}


def normalizar_df(df):
    """Renomeia colunas do INSS para nomes canonicos."""
    mapa = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "compet" in cl or "concess" in cl:
            mapa[c] = "comp_concessao"
        elif "espécie" in cl or "especie" in cl:
            if "comp" not in cl and "concess" not in cl:
                mapa[c] = "especie"
        elif "cid" in cl and "nome" not in cl and ".1" not in c:
            mapa[c] = "cid"
        elif "cid" in cl and (".1" in c or "nome" in cl):
            mapa[c] = "cid_nome"
        elif "despacho" in cl:
            mapa[c] = "despacho"
        elif "nasc" in cl:
            mapa[c] = "dt_nascimento"
        elif cl == "sexo" or cl == "sexo.":
            mapa[c] = "sexo"
        elif "client" in cl:
            mapa[c] = "clientela"
        elif "mun" in cl and "resid" in cl:
            mapa[c] = "mun_resid"
        elif "vinculo" in cl or "vínculo" in cl:
            mapa[c] = "vinculo_dependentes"
        elif "filia" in cl:
            mapa[c] = "forma_filiacao"
        elif cl == "uf":
            mapa[c] = "uf"
        elif "sm" in cl or "rmi" in cl:
            mapa[c] = "qt_sm_rmi"
        elif "ramo" in cl and "ativid" in cl:
            mapa[c] = "ramo_atividade"
        elif "ddb" in cl:
            mapa[c] = "dt_ddb"
        elif "dib" in cl:
            mapa[c] = "dt_dib"
    df = df.rename(columns=mapa)
    return df


def filtrar_campos_trabalho(df):
    """Filtra df para Campos + especies acidentarias."""
    if "mun_resid" not in df.columns:
        return df.iloc[0:0]

    mask = df["mun_resid"].astype(str).str.upper().str.contains(MUN_CAMPOS, na=False)
    df = df[mask]

    if "especie" in df.columns and len(df) > 0:
        mask = df["especie"].astype(str).str.lower().str.contains("acidente", na=False)
        df = df[mask]

    return df


def extrair_ano_mes(nome):
    """Extrai ano e mes do nome do arquivo."""
    n = nome.upper().replace("+", " ").replace("_", " ")

    # D.SDA.PDA.001.CON.202108
    m = re.search(r"CON[.\s]*(\d{4})(\d{2})", n)
    if m:
        return int(m.group(1)), int(m.group(2))

    # concedidos-MM-AAAA, beneficios-concedidos-MM-AAAA
    m = re.search(r"(\d{2})-(\d{4})", nome)
    if m:
        return int(m.group(2)), int(m.group(1))

    # BEN_CONCEDIDOS_MMAAAA, CONCEDIDOS_MMAAAA
    m = re.search(r"(\d{2})(\d{4})", n)
    if m and int(m.group(1)) <= 12:
        return int(m.group(2)), int(m.group(1))

    # Mes por extenso + ano: JANEIRO 2025, JULHO 2024
    for mes_nome, mes_num in MESES_NOME.items():
        if mes_nome.upper() in n:
            m = re.search(r"(20\d{2})", n)
            if m:
                return int(m.group(1)), mes_num

    # concedidos_2018.zip
    m = re.search(r"(201[89]|202[0-5])", n)
    if m:
        return int(m.group(1)), None

    return None, None


def processar_arquivo(path, nome, header_row=0):
    """Processa um CSV ou XLSX e retorna lista de dicts."""
    is_xlsx = path.lower().endswith(".xlsx")

    try:
        if is_xlsx:
            df = pd.read_excel(path, header=header_row, dtype=str, engine="openpyxl")
        else:
            for enc in ["latin-1", "utf-8", "cp1252"]:
                try:
                    df = pd.read_csv(path, sep=";", encoding=enc, dtype=str)
                    break
                except:
                    continue

        if df is None or len(df) == 0:
            return []

        df = normalizar_df(df)
        df = filtrar_campos_trabalho(df)

        if len(df) == 0:
            return []

        # Selecionar colunas finais
        for c in COLUNAS_FINAL:
            if c not in df.columns:
                df[c] = ""

        df["_arquivo"] = nome
        registros = df[COLUNAS_FINAL].to_dict("records")
        return registros

    except Exception as e:
        print(f"  ERRO: {type(e).__name__}: {str(e)[:80]}")
        return []


def main():
    print("=" * 70)
    print("BENEFICIOS CONCEDIDOS INSS - CAMPOS DOS GOYTACAZES")
    print("Especies acidentarias (B91, B92, B93, B94) | 2018-2025")
    print("=" * 70)

    arquivos = sorted(os.listdir(DIR_BEN))
    todos = []
    resumo = defaultdict(lambda: defaultdict(int))

    for nome in arquivos:
        if nome.startswith("Gloss") or nome.startswith("~"):
            continue

        path = os.path.join(DIR_BEN, nome)
        ext = nome.lower()
        ano, mes = extrair_ano_mes(nome)

        if ext.endswith(".csv"):
            regs = processar_arquivo(path, nome, header_row=0)
        elif ext.endswith(".xlsx"):
            regs = processar_arquivo(path, nome, header_row=1)
        elif ext.endswith(".zip"):
            regs = []
            try:
                with tempfile.TemporaryDirectory() as td:
                    with zipfile.ZipFile(path, "r") as z:
                        z.extractall(td)
                    for f in sorted(os.listdir(td)):
                        fp = os.path.join(td, f)
                        fext = f.lower()
                        if fext.endswith(".csv"):
                            sub = processar_arquivo(fp, f"{nome}/{f}", header_row=0)
                        elif fext.endswith(".xlsx"):
                            sub = processar_arquivo(fp, f"{nome}/{f}", header_row=1)
                        else:
                            continue
                        if sub:
                            for r in sub:
                                r["_ano"] = ano if ano else ""
                                r["_mes"] = mes if mes else ""
                            regs.extend(sub)
            except Exception as e:
                print(f"  ZIP ERRO: {e}")
                continue
        else:
            continue

        if regs and ano:
            for r in regs:
                r["_ano"] = ano
                r["_mes"] = mes if mes else ""
                todos.append(r)
                esp = r.get("especie", "")
                resumo[ano][esp] += 1
            print(f"  {nome}: {len(regs)} registros")
        elif regs:
            for r in regs:
                todos.append(r)
            print(f"  {nome}: {len(regs)} (ano nao identificado)")
        else:
            print(f"  {nome}: 0")

    # Salvar
    if todos:
        path_csv = os.path.join(DIR_PROC, "beneficios_inss_campos_2018_2025.csv")
        with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLUNAS_FINAL, delimiter=";", extrasaction="ignore")
            w.writeheader()
            w.writerows(todos)
        mb = os.path.getsize(path_csv) / 1e6
        print(f"\n{'='*70}")
        print(f"CSV: {path_csv} ({mb:.1f} MB, {len(todos)} registros)")
    else:
        print("\nNENHUM registro.")
        return

    # Resumo
    print(f"\n{'='*70}")
    print(f"RESUMO - Beneficios Acidentarios em Campos")
    print(f"{'='*70}")
    anos_ord = sorted(a for a in resumo if a)
    especies_todas = set()
    for a in anos_ord:
        especies_todas.update(resumo[a].keys())

    for esp in sorted(especies_todas):
        total = sum(resumo[a].get(esp, 0) for a in anos_ord)
        print(f"  {esp[:70]}: {total}")

    total_geral = sum(sum(resumo[a].values()) for a in anos_ord)
    print(f"\n  TOTAL GERAL: {total_geral}")
    print(f"  Arquivo: {path_csv}")

    for a in anos_ord:
        ta = sum(resumo[a].values())
        print(f"  {a}: {ta}")


if __name__ == "__main__":
    main()
