# -*- coding: utf-8 -*-
"""Baixa SIM (mortalidade) do FTP DATASUS para RJ, filtra Campos 2015-2018 e 2025."""
import os, sys, ftplib, csv, hashlib
from dbfread import DBF

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "dissemin/publicos/SIM/CID10/DORES"
MUN_COD = "330100"
UF = "RJ"
ANOS = [2015, 2016, 2017, 2018]  # 2025 ainda nao disponivel no FTP DATASUS

DIR_OUT = os.path.join("banco de dados", "sim")
os.makedirs(DIR_OUT, exist_ok=True)

print("=" * 60)
print("DOWNLOAD SIM — Campos dos Goytacazes (330100)")
print(f"Anos: {ANOS}")
print("=" * 60)

ftp = ftplib.FTP(FTP_HOST, timeout=120)
ftp.login()
ftp.cwd(FTP_DIR)

baixados = 0
for ano in ANOS:
    nome_ftp = f"DO{UF}{ano}.dbc"
    nome_dbc = os.path.join(DIR_OUT, nome_ftp)
    nome_csv = os.path.join(DIR_OUT, f"SIM_Campos_{ano}.csv")

    if os.path.exists(nome_csv) and os.path.getsize(nome_csv) > 100:
        print(f"  [{ano}] Já existe CSV filtrado, pulando")
        continue

    # Baixar .dbc
    if not os.path.exists(nome_dbc):
        try:
            sz = ftp.size(nome_ftp)
            print(f"  [{ano}] Baixando {nome_ftp} ({sz/1e6:.1f} MB)...")
            with open(nome_dbc, "wb") as f:
                ftp.retrbinary(f"RETR {nome_ftp}", f.write)
        except Exception as e:
            print(f"  [{ano}] ERRO FTP: {e}")
            continue

    # Filtrar Campos
    print(f"  [{ano}] Filtrando Campos...")
    try:
        dbf = DBF(nome_dbc, encoding="latin-1")
        n_total = 0
        n_campos = 0
        with open(nome_csv, "w", newline="", encoding="utf-8-sig") as out:
            writer = csv.writer(out, delimiter=";")
            cabecalho_escrito = False
            for record in dbf:
                n_total += 1
                codmun = str(record.get("CODMUNRES", record.get("CODMUNOCOR", ""))).strip()
                if codmun == MUN_COD:
                    if not cabecalho_escrito:
                        writer.writerow(record.keys())
                        cabecalho_escrito = True
                    writer.writerow(record.values())
                    n_campos += 1
        print(f"    {n_campos} óbitos em Campos (de {n_total} no RJ)")

        # Remover .dbc bruto (só guardamos o CSV filtrado)
        os.remove(nome_dbc)
        baixados += 1
    except Exception as e:
        print(f"  [{ano}] ERRO ao filtrar: {e}")
        if os.path.exists(nome_dbc):
            os.remove(nome_dbc)

ftp.quit()

# Manifesto
manifesto = os.path.join("dados", "manifesto", "manifesto_sim_2015_2018.csv")
with open(manifesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["arquivo", "sha256", "tamanho_bytes", "registros"])
    for ano in ANOS:
        csv_file = os.path.join(DIR_OUT, f"SIM_Campos_{ano}.csv")
        if os.path.exists(csv_file):
            sha = hashlib.sha256()
            with open(csv_file, "rb") as bf:
                for chunk in iter(lambda: bf.read(8192), b""):
                    sha.update(chunk)
            sz = os.path.getsize(csv_file)
            with open(csv_file, "r", encoding="utf-8-sig") as cf:
                n = sum(1 for _ in cf) - 1  # menos cabeçalho
            w.writerow([f"SIM_Campos_{ano}.csv", sha.hexdigest(), sz, n])

print(f"\n[DONE] {baixados} arquivos baixados e filtrados.")
