# -*- coding: utf-8 -*-
"""
16_sinan_download.py - Download e processamento de dados SINAN via FTP do DATASUS
para Campos dos Goytacazes (RJ), periodo 2018-2025.

Agravos (9):
  ACGR = Acidente de Trabalho Grave
  ANIM = Acidente por Animais Peconhentos
  ACBI = Acidente de Trabalho com Exposicao a Material Biologico
  CANC = Cancer Relacionado ao Trabalho
  DERM = Dermatose Relacionada ao Trabalho
  LERD = LER/DORT
  PNEU = Pneumoconiose Relacionada ao Trabalho
  PAIR = PAIR Relacionado ao Trabalho
  MENT = Transtorno Mental Relacionado ao Trabalho

FTP: ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/
Formato: .dbc (arquivos nacionais BR, sao DBF nao comprimidos)
Filtro: ID_MN_RESI = '330100' OU SG_UF = 'RJ'
"""
import os, sys, ftplib, time, csv, json
from collections import defaultdict
from dbfread import DBF

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "dissemin/publicos/SINAN/DADOS/FINAIS"
MUN_COD = "330100"
UF = "RJ"
ANOS = list(range(2018, 2026))

AGRAVOS = {
    "ACGR": "Acidente de Trabalho Grave",
    "ANIM": "Acidente por Animais Peconhentos",
    "ACBI": "Acid Trab Exposicao Material Biologico",
    "CANC": "Cancer Relacionado ao Trabalho",
    "DERM": "Dermatose Relacionada ao Trabalho",
    "LERD": "LER/DORT",
    "PNEU": "Pneumoconiose Relacionada ao Trabalho",
    "PAIR": "PAIR Relacionado ao Trabalho",
    "MENT": "Transtorno Mental Relacionado ao Trabalho",
}

DIR_SINAN = os.path.join("dados", "brutos", "sinan")
DIR_PROC = os.path.join("dados", "processados")
os.makedirs(DIR_SINAN, exist_ok=True)
os.makedirs(DIR_PROC, exist_ok=True)

# ========== ETAPA 1: Inventariar arquivos no FTP ==========
print("=" * 60)
print("ETAPA 1: Inventariando arquivos SINAN no FTP DATASUS...")
print("=" * 60)

ftp = ftplib.FTP(FTP_HOST, timeout=30)
ftp.login()
ftp.cwd(FTP_DIR)

todos_arquivos = []
ftp.retrlines("LIST", lambda line: todos_arquivos.append(line))

arquivos_baixar = []
for linha in todos_arquivos:
    partes = linha.split()
    if len(partes) < 4:
        continue
    nome = partes[-1]
    if not nome.upper().endswith(".DBC"):
        continue
    
    prefixo = nome[:4].upper()
    if prefixo not in AGRAVOS:
        continue
    
    # Extrair ano do nome: prefixoBRAA.dbc onde AA = 06-25
    try:
        ano_sufix = int(nome[6:8]) if len(nome) >= 8 and nome[6:8].isdigit() else None
    except:
        ano_sufix = None
    
    if ano_sufix is None:
        continue
    
    ano = 2000 + ano_sufix if ano_sufix < 50 else 1900 + ano_sufix
    
    if ano not in ANOS:
        continue
    
    tamanho = int(partes[3]) if len(partes) > 3 and partes[3].isdigit() else 0
    arquivos_baixar.append({
        "agravo": prefixo,
        "agravo_nome": AGRAVOS[prefixo],
        "ano": ano,
        "arquivo": nome,
        "tamanho_mb": round(tamanho / 1e6, 1),
    })

ftp.quit()

arquivos_baixar.sort(key=lambda x: (x["agravo"], x["ano"]))
print(f"\nTotal: {len(arquivos_baixar)} arquivos de {len(AGRAVOS)} agravos, {len(ANOS)} anos")
for a in arquivos_baixar:
    print(f"  [{a['agravo']}] {a['ano']}: {a['arquivo']} ({a['tamanho_mb']} MB)")

# Salvar inventario
with open(os.path.join(DIR_SINAN, "inventario_sinan.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["agravo", "agravo_nome", "ano", "arquivo", "tamanho_mb"], delimiter=";")
    w.writeheader()
    w.writerows(arquivos_baixar)

# ========== ETAPA 2: Download ==========
print("\n" + "=" * 60)
print("ETAPA 2: Baixando arquivos...")
print("=" * 60)

ftp = ftplib.FTP(FTP_HOST, timeout=120)
ftp.login()
ftp.cwd(FTP_DIR)

baixados = []
for i, a in enumerate(arquivos_baixar):
    local = os.path.join(DIR_SINAN, a["arquivo"])
    
    if os.path.exists(local) and os.path.getsize(local) > 1000:
        print(f"  [{i+1}/{len(arquivos_baixar)}] {a['arquivo']} - ja existe ({a['tamanho_mb']} MB)")
        baixados.append({"path": local, **a})
        continue
    
    try:
        print(f"  [{i+1}/{len(arquivos_baixar)}] Baixando {a['arquivo']} ({a['tamanho_mb']} MB)...", end=" ", flush=True)
        with open(local, "wb") as f:
            ftp.retrbinary(f"RETR {a['arquivo']}", f.write)
        real = round(os.path.getsize(local) / 1e6, 1)
        print(f"OK ({real} MB)")
        baixados.append({"path": local, **a})
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(0.3)

ftp.quit()
print(f"\nBaixados: {len(baixados)}/{len(arquivos_baixar)}")

if not baixados:
    print("Nenhum arquivo baixado. Abortando.")
    sys.exit(1)

# ========== ETAPA 3: Filtrar Campos dos Goytacazes ==========
print("\n" + "=" * 60)
print("ETAPA 3: Lendo DBFs e filtrando Campos dos Goytacazes (330100 / RJ)...")
print("=" * 60)

todos_registros = []
estatisticas_agravo = defaultdict(lambda: defaultdict(int))
colunas_comuns = set()

for i, a in enumerate(baixados):
    print(f"  [{i+1}/{len(baixados)}] {a['agravo']} {a['ano']} ({a['arquivo']})...", end=" ", flush=True)
    
    try:
        dbf = DBF(a["path"], encoding="latin-1", char_decode_errors="replace",
                  ignore_missing_memofile=True)
        
        # Identificar coluna de municipio
        col_mun = None
        col_uf = None
        for campo in dbf.fields:
            if "ID_MN_RESI" in campo.name.upper():
                col_mun = campo.name
            elif "ID_MUNICIP" in campo.name.upper() and col_mun is None:
                col_mun = campo.name
            if "SG_UF" in campo.name.upper():
                col_uf = campo.name
        
        if col_mun is None:
            print(f"COLUNA MUN NAO ENCONTRADA. Campos: {[f.name for f in dbf.fields[:8]]}")
            continue
        
        total = 0
        campos_count = 0
        for record in dbf:
            total += 1
            try:
                mun = str(record.get(col_mun, "")).strip()
                uf_val = str(record.get(col_uf, "")).strip() if col_uf else ""
            except:
                continue
            
            # Filtrar: municipio 330100 OU (UF=RJ e municipio comeca com 330100)
            if mun == MUN_COD or mun.startswith(MUN_COD):
                campos_count += 1
                rec_clean = {}
                for k, v in record.items():
                    if isinstance(v, bytes):
                        try:
                            rec_clean[k] = v.decode("latin-1", errors="replace").strip()
                        except:
                            rec_clean[k] = str(v)
                    else:
                        rec_clean[k] = str(v).strip() if v is not None else ""
                
                rec_clean["_agravo_cod"] = a["agravo"]
                rec_clean["_agravo_nome"] = a["agravo_nome"]
                rec_clean["_ano_arquivo"] = a["ano"]
                rec_clean["_arquivo_fonte"] = a["arquivo"]
                todos_registros.append(rec_clean)
                colunas_comuns.update(rec_clean.keys())
        
        estatisticas_agravo[a["agravo"]][a["ano"]] = campos_count
        print(f"{campos_count} registros (total BR: {total})")
        
    except Exception as e:
        print(f"ERRO: {e}")

# ========== ETAPA 4: Consolidar e salvar ==========
print("\n" + "=" * 60)
print("ETAPA 4: Consolidando e salvando...")
print("=" * 60)

if not todos_registros:
    print("AVISO: Nenhum registro de Campos encontrado nos arquivos SINAN!")
    print("Possiveis causas: periodo sem notificacoes, codigo municipal diferente, ou dados nao disponiveis.")
    sys.exit(0)

import pandas as pd

# Garantir colunas consistentes
colunas_ordenadas = sorted(colunas_comuns)
df = pd.DataFrame(todos_registros)
# Reordenar colunas com prefixo _ primeiro
cols_meta = [c for c in df.columns if c.startswith("_")]
cols_data = [c for c in df.columns if not c.startswith("_")]
df = df[cols_meta + sorted(cols_data)]

path_out = os.path.join(DIR_PROC, "sinan_campos_2018_2025.csv")
df.to_csv(path_out, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
print(f"Total registros SINAN Campos 2018-2025: {len(df)}")
print(f"Arquivo: {path_out}")
print(f"Dimensoes: {df.shape[0]} linhas x {df.shape[1]} colunas")

# Resumo por agravo e ano
print("\nResumo SINAN Campos dos Goytacazes (RJ), 2018-2025:")
print(f"{'Agravo':<45} {'2018':>6} {'2019':>6} {'2020':>6} {'2021':>6} {'2022':>6} {'2023':>6} {'2024':>6} {'2025':>6} {'Total':>6}")
print("-" * 105)

total_geral = 0
for agravo_cod, agravo_nome in sorted(AGRAVOS.items()):
    total_agravo = 0
    row = f"  {agravo_nome[:43]:<43}"
    for ano in ANOS:
        n = estatisticas_agravo[agravo_cod].get(ano, 0)
        row += f" {n:>6}"
        total_agravo += n
        total_geral += n
    row += f" {total_agravo:>6}"
    print(row)

print("-" * 105)
print(f"{'TOTAL':<45}", end="")
for ano in ANOS:
    s = sum(estatisticas_agravo[ag].get(ano, 0) for ag in AGRAVOS)
    print(f" {s:>6}", end="")
print(f" {total_geral:>6}")

# Salvar tabela de resumo
resumo_rows = []
for agravo_cod, agravo_nome in sorted(AGRAVOS.items()):
    row = {"agravo": agravo_nome}
    for ano in ANOS:
        row[str(ano)] = estatisticas_agravo[agravo_cod].get(ano, 0)
    row["total"] = sum(row[str(a)] for a in ANOS)
    resumo_rows.append(row)

pd.DataFrame(resumo_rows).to_csv(
    "saidas/tabelas/T39_sinan_resumo_agravo_ano.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# Log
log = {
    "fonte": "SINAN/DATASUS via FTP",
    "ftp": f"ftp://{FTP_HOST}/{FTP_DIR}",
    "periodo": f"{min(ANOS)}-{max(ANOS)}",
    "municipio": "Campos dos Goytacazes (330100)",
    "arquivos_baixados": len(baixados),
    "total_registros_campos": int(len(df)),
    "agravos_encontrados": list(estatisticas_agravo.keys()),
    "execucao": pd.Timestamp.now().isoformat(),
}
os.makedirs("logs", exist_ok=True)
json.dump(log, open("logs/log_16_sinan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"\nArquivos gerados:")
print(f"  {path_out}")
print(f"  saidas/tabelas/T39_sinan_resumo_agravo_ano.csv")
print(f"  logs/log_16_sinan.json")
print(f"  dados/brutos/sinan/inventario_sinan.csv")
print("\nOK Script 16 concluido.")
