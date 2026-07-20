# -*- coding: utf-8 -*-
"""
beneficios_inss_corrigido.py
=============================
ETAPA 1: Converte XLSX → CSV (preservando todos os dados)
ETAPA 2: Filtra Campos dos Goytacazes + especies acidentarias (B91-B94)
ETAPA 3: Consolida com dados ja processados de 2018-2022

Fluxo correto: XLSX → CSV → filtro → consolidado
Fonte: Portal de Dados Abertos do INSS
"""
import os, re, csv, zipfile, tempfile, pandas as pd
from collections import defaultdict, Counter

DIR_BEN = os.path.join("banco de dados", "beneficios-inss")
DIR_PROC = os.path.join("dados", "processados")
DIR_SAIDAS = os.path.join("saidas", "tabelas")
for d in [DIR_PROC, DIR_SAIDAS]:
    os.makedirs(d, exist_ok=True)

MUN = "CAMPOS DOS GOYTACAZES"

ESPECIES_TRAB = [
    "auxilio doenca por acidente do trabalho",
    "auxílio doença por acidente do trabalho",
    "aposent. invalidez acidente trabalho",
    "aposentadoria invalidez acidente trabalho",
    "pensao por morte por acidente do trabalho",
    "pensão por morte por acidente do trabalho",
    "auxilio acidente",
    "auxílio acidente",
]

MESES_NOME = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}


def extrair_ano_mes(nome):
    """Extrai ano e mes do nome do arquivo."""
    n = nome.upper().replace("+", " ").replace("_", " ")

    m = re.search(r"CON[.\s]*(\d{4})(\d{2})", n)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.search(r"(\d{2})-(\d{4})", nome)
    if m:
        return int(m.group(2)), int(m.group(1))

    m = re.search(r"(\d{2})(\d{4})", n)
    if m and int(m.group(1)) <= 12:
        return int(m.group(2)), int(m.group(1))

    for mes_nome, mes_num in MESES_NOME.items():
        if mes_nome.upper() in n:
            m = re.search(r"(20\d{2})", n)
            if m:
                return int(m.group(1)), mes_num

    m = re.search(r"(201[89]|202[0-5])", n)
    if m:
        return int(m.group(1)), None

    return None, None


def converter_xlsx_para_csv(path_xlsx, path_csv):
    """Converte XLSX para CSV preservando todos os dados."""
    try:
        df = pd.read_excel(path_xlsx, header=1, dtype=str, engine="openpyxl")
        df.to_csv(path_csv, sep=";", index=False, encoding="utf-8")
        return True
    except Exception as e:
        print(f"    ERRO conversao: {e}")
        return False


def filtrar_csv(path_csv, ano, mes):
    """Filtra CSV para Campos + especies acidentarias."""
    registros = []
    try:
        with open(path_csv, "r", encoding="latin-1", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=";")
            if reader.fieldnames is None:
                return registros

            # Mapear colunas
            col_mun = None
            col_esp = None
            for c in reader.fieldnames:
                cs = str(c).strip()
                if cs == "Mun Resid":
                    col_mun = c
                if cs in ("Espécie", "Especie"):
                    col_esp = c

            if not col_mun:
                return registros

            for row in reader:
                mun_val = str(row.get(col_mun, ""))
                if MUN not in mun_val.upper():
                    continue

                if col_esp:
                    esp_val = str(row.get(col_esp, "")).lower()
                    if not any(et in esp_val for et in ["acidente"]):
                        continue

                row["_ano"] = ano
                row["_mes"] = mes
                row["_arquivo"] = os.path.basename(path_csv)
                registros.append(row)

    except Exception as e:
        print(f"    ERRO filtro: {e}")

    return registros


def main():
    print("=" * 70)
    print("BENEFICIOS CONCEDIDOS INSS - CAMPOS DOS GOYTACAZES")
    print("Portal de Dados Abertos do INSS | 2018-2025")
    print("=" * 70)

    # === ETAPA 1: Converter XLSX → CSV ===
    arquivos = sorted(os.listdir(DIR_BEN))
    xlsx_files = [f for f in arquivos if f.lower().endswith(".xlsx") and "Gloss" not in f]

    if xlsx_files:
        print(f"\nETAPA 1: Convertendo {len(xlsx_files)} XLSX para CSV...\n")
        for nome in xlsx_files:
            path_xlsx = os.path.join(DIR_BEN, nome)
            ano, mes = extrair_ano_mes(nome)
            nome_csv = f"beneficios_{ano}_{mes:02d}.csv" if (ano and mes) else nome.replace(".xlsx", ".csv")
            path_csv = os.path.join(DIR_BEN, nome_csv)

            if os.path.exists(path_csv):
                print(f"  {nome_csv}: ja existe")
                continue

            mb = os.path.getsize(path_xlsx) / 1e6
            print(f"  {nome[:60]} ({mb:.0f}MB) -> {nome_csv}...", end=" ", flush=True)
            if converter_xlsx_para_csv(path_xlsx, path_csv):
                print("OK")
                os.remove(path_xlsx)  # Apagar XLSX apos conversao
            else:
                print("FALHOU")
    else:
        print("\nNenhum XLSX encontrado para converter.")

    # === ETAPA 2: Filtrar todos os CSVs ===
    print(f"\nETAPA 2: Filtrando CSVs para Campos + acidentarios...\n")

    todos = []
    resumo = defaultdict(lambda: defaultdict(int))

    for nome in sorted(os.listdir(DIR_BEN)):
        if not (nome.lower().endswith(".csv") or nome.lower().endswith(".txt")):
            continue
        if "Gloss" in nome:
            continue

        path = os.path.join(DIR_BEN, nome)

        # Pular CSVs de conversao pendentes
        if nome.startswith("beneficios_202") and "_" in nome:
            ano_m = re.search(r"beneficios_(\d{4})_(\d{2})", nome)
            ano, mes = int(ano_m.group(1)), int(ano_m.group(2)) if ano_m else (0, 0)
        else:
            ano, mes = extrair_ano_mes(nome)
            if not ano:
                ano = 0

        # Processar ZIPs internamente
        if nome.lower().endswith(".zip"):
            print(f"  {nome}: extraindo ZIP...")
            try:
                with tempfile.TemporaryDirectory() as td:
                    with zipfile.ZipFile(path, "r") as z:
                        z.extractall(td)
                    for f in sorted(os.listdir(td)):
                        fp = os.path.join(td, f)
                        if f.lower().endswith((".csv", ".txt")):
                            regs = filtrar_csv(fp, ano, mes)
                            if regs:
                                for r in regs:
                                    r["_arquivo"] = f"{nome}/{f}"
                                todos.extend(regs)
                                for r in regs:
                                    resumo[ano]["_".join(r.get("Especie", r.get("especie", "?"))[:40])] += 1
                            print(f"    {f}: {len(regs)}")
            except Exception as e:
                print(f"    ERRO ZIP: {e}")
            continue

        # CSV direto
        mb = os.path.getsize(path) / 1e6 if os.path.exists(path) else 0
        regs = filtrar_csv(path, ano, mes)
        print(f"  {nome} ({mb:.0f}MB): {len(regs)} acidentarios Campos")
        todos.extend(regs)
        for r in regs:
            esp = str(r.get("Espécie", r.get("especie", "?")))[:40]
            resumo[ano][esp] += 1

    # === ETAPA 3: Salvar consolidado ===
    if todos:
        path_final = os.path.join(DIR_PROC, "beneficios_inss_campos_2018_2025.csv")
        if todos:
            cols = list(todos[0].keys())
            with open(path_final, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
                w.writeheader()
                w.writerows(todos)
            mb = os.path.getsize(path_final) / 1e6
            print(f"\nFINAL: {path_final} ({mb:.1f} MB, {len(todos)} registros)")

        # Resumo
        print(f"\n{'='*70}")
        print("RESUMO - Beneficios Acidentarios em Campos")
        print(f"{'='*70}")
        for ano in sorted(a for a in resumo if a):
            total = sum(resumo[ano].values())
            print(f"\n  {ano}: {total} beneficios")
            for esp, n in sorted(resumo[ano].items(), key=lambda x: -x[1])[:5]:
                print(f"    {esp[:60]}: {n}")

        total_geral = sum(sum(r.values()) for r in resumo.values())
        print(f"\n  TOTAL GERAL: {total_geral}")
    else:
        print("\nNENHUM registro encontrado.")


if __name__ == "__main__":
    main()
