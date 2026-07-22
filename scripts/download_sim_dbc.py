# -*- coding: utf-8 -*-
"""Baixa SIM 2015-2018 do FTP DATASUS como .dbc brutos (LFS)."""
import os, sys, ftplib, hashlib, csv

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "dissemin/publicos/SIM/CID10/DORES"
UF = "RJ"
ANOS = [2015, 2016, 2017, 2018]

DIR_OUT = os.path.join("banco de dados", "sim")
os.makedirs(DIR_OUT, exist_ok=True)

print("=" * 60)
print("DOWNLOAD SIM 2015-2018 — .dbc brutos (RJ)")
print("=" * 60)

ftp = ftplib.FTP(FTP_HOST, timeout=120)
ftp.login()
ftp.cwd(FTP_DIR)

baixados = 0
for ano in ANOS:
    nome = f"DO{UF}{ano}.dbc"
    caminho = os.path.join(DIR_OUT, nome)
    if os.path.exists(caminho):
        sz = os.path.getsize(caminho)
        print(f"  [{ano}] Já existe ({sz/1e6:.1f} MB)")
        baixados += 1
        continue
    try:
        sz = ftp.size(nome)
        print(f"  [{ano}] Baixando {nome} ({sz/1e6:.1f} MB)...")
        with open(caminho, "wb") as f:
            ftp.retrbinary(f"RETR {nome}", f.write)
        baixados += 1
    except Exception as e:
        print(f"  [{ano}] ERRO: {e}")

ftp.quit()

# Manifesto
manifesto = os.path.join("dados", "manifesto", "manifesto_sim_dbc_2015_2018.csv")
with open(manifesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["arquivo", "sha256", "tamanho_bytes"])
    for ano in ANOS:
        nome = f"DO{UF}{ano}.dbc"
        caminho = os.path.join(DIR_OUT, nome)
        if os.path.exists(caminho):
            sha = hashlib.sha256()
            with open(caminho, "rb") as bf:
                for chunk in iter(lambda: bf.read(8192), b""):
                    sha.update(chunk)
            sz = os.path.getsize(caminho)
            w.writerow([nome, sha.hexdigest(), sz])

print(f"\n[DONE] {baixados} arquivos baixados.")
