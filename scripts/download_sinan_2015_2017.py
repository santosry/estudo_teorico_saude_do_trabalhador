# -*- coding: utf-8 -*-
"""Baixa SINAN 2015-2017 do FTP DATASUS e salva .dbc brutos no LFS."""
import os, sys, ftplib, hashlib, csv
from pathlib import Path

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "dissemin/publicos/SINAN/DADOS/FINAIS"
ANOS = [2015, 2016, 2017]
AGRAVOS = ["ACBI","ACGR","ANIM","CANC","DERM","LERD","MENT","PAIR","PNEU"]

DIR_OUT = os.path.join("dados", "brutos", "sinan")
os.makedirs(DIR_OUT, exist_ok=True)

LOG = []

def log(msg):
    print(msg)
    LOG.append(msg)

log("=" * 60)
log("DOWNLOAD SINAN 2015-2017 — .dbc brutos")
log(f"Destino: {DIR_OUT}")
log("=" * 60)

ftp = ftplib.FTP(FTP_HOST, timeout=60)
ftp.login()
ftp.cwd(FTP_DIR)

baixados = 0
for agravo in AGRAVOS:
    for ano in ANOS:
        nome = f"{agravo}BR{str(ano)[-2:]}.dbc"
        caminho = os.path.join(DIR_OUT, nome)
        if os.path.exists(caminho):
            log(f"  [{agravo} {ano}] Já existe")
            continue
        try:
            sz = ftp.size(nome)
            log(f"  [{agravo} {ano}] Baixando {sz/1e6:.1f} MB...")
            with open(caminho, "wb") as f:
                ftp.retrbinary(f"RETR {nome}", f.write)
            baixados += 1
        except Exception as e:
            log(f"  [{agravo} {ano}] ERRO: {e}")

ftp.quit()

# Manifesto SHA-256
manifesto = os.path.join("dados", "manifesto", "manifesto_sinan_2015_2017.csv")
with open(manifesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["arquivo", "sha256", "tamanho_bytes"])
    for agravo in AGRAVOS:
        for ano in ANOS:
            nome = f"{agravo}BR{str(ano)[-2:]}.dbc"
            caminho = os.path.join(DIR_OUT, nome)
            if os.path.exists(caminho):
                sha = hashlib.sha256()
                with open(caminho, "rb") as bf:
                    for chunk in iter(lambda: bf.read(8192), b""):
                        sha.update(chunk)
                sz = os.path.getsize(caminho)
                w.writerow([nome, sha.hexdigest(), sz])

log(f"\n[DONE] {baixados} arquivos baixados.")
log(f"Manifesto: {manifesto}")
