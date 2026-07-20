# -*- coding: utf-8 -*-
"""
download_bases_complementares.py
================================
Baixa e filtra para Campos dos Goytacazes (330100) as bases complementares:

1. SINAN (2018-2025) - 9 agravos de notificacao relacionados ao trabalho
   FTP: ftp.datasus.gov.br (FINAIS 2018-2022 + PRELIM 2023-2025)

2. CAGED (2018-2025) - Admitidos e desligados do mercado formal
   FTP: ftp.mtps.gov.br/pdet/microdados/CAGED/ (2018-2019)
   + Novo CAGED via Dados Abertos (2020-2025)

3. ANP (2018-2025) - Royalties e participacoes especiais do petroleo
   API: dados.gov.br / ANP

4. BEN/INSS (2018-2025) - Beneficios acidentarios (B91, B92, B93, B94)
   Fonte: INSS/DATASUS - TabNet ou microdatasus

5. SIH/SUS (2018-2025) - Internacoes hospitalares
   FTP: ftp.datasus.gov.br/dissemin/publicos/SIHSUS/

USO:
    python scripts/download_bases_complementares.py [--todas] [--sinan] [--caged] [--anp] [--ben] [--sih]

REQUISITOS:
    pip install dbfread requests
"""
import os, sys, csv, time, json, ftplib, tempfile, argparse
import requests
from datetime import datetime
from collections import defaultdict, Counter

# ============================================================
# CONFIGURACAO
# ============================================================
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

MUN_COD = "330100"  # Campos dos Goytacazes
UF = "RJ"
ANOS = list(range(2018, 2026))

DIR_BRUTOS = os.path.join("banco de dados")
DIR_PROC = os.path.join("dados", "processados")
DIR_SAIDAS = os.path.join("saidas", "tabelas")

for d in [DIR_BRUTOS, DIR_PROC, DIR_SAIDAS]:
    os.makedirs(d, exist_ok=True)


# ============================================================
# 1. SINAN (via DATASUS FTP)
# ============================================================
def baixar_sinan():
    """Executa o script 16_sinan_download.py atualizado."""
    print("\n" + "=" * 70)
    print("1. SINAN - Agravos de Notificacao Relacionados ao Trabalho")
    print("=" * 70)

    # Executar como submodulo
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sinan_mod",
        os.path.join(RAIZ, "scripts", "pipeline", "16_sinan_download.py")
    )
    sinan_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sinan_mod)


# ============================================================
# 2. CAGED (via MTE FTP)
# ============================================================
def baixar_caged():
    """
    Baixa CAGED 2018-2019 do FTP do MTE.
    Formato: CSV delimitado por ';', 40 colunas.
    Colunas principais:
      col 0: Tipo (01=Admitido, 02=Desligado)
      col 1: Competencia AAAAMM
      col 2: Municipio (6 digitos IBGE)
      col 3: Ano
      col 4: CBO 2002
      col 6: CNAE 2.0 Classe
      col 9: Grau Instrucao
      col 10: Sexo (01=M, 02=F)
      col 11: Faixa Etaria
      col 14: Faixa Horas Contratuais
      col 15: Faixa Remun Media (SM)
      col 22: CNAE 2.0 Subclasse
    """
    print("\n" + "=" * 70)
    print("2. CAGED - Movimentacao do Emprego Formal")
    print("=" * 70)

    FTP_HOST = "ftp.mtps.gov.br"
    DIR_CAGED = os.path.join(DIR_BRUTOS, "caged")
    os.makedirs(DIR_CAGED, exist_ok=True)

    import csv as csv_mod

    todos_registros = []

    for ano in [2018, 2019]:
        print(f"\n  [{ano}] Baixando CAGED...")
        ftp = ftplib.FTP(FTP_HOST, timeout=30)
        ftp.login()
        ftp.encoding = "latin-1"
        ftp.cwd(f"pdet/microdados/CAGED/{ano}")

        # Usar nlst() ao inves de retrlines(LIST) para evitar encoding issues
        nomes = ftp.nlst()
        nomes_7z = sorted([n for n in nomes if n.upper().endswith(".7Z") and "CAGEDEST" in n.upper()])
        ftp.quit()

        print(f"    {len(nomes_7z)} arquivos mensais encontrados")

        for nome in nomes_7z:
            local = os.path.join(DIR_CAGED, nome)
            if not os.path.exists(local):
                print(f"    Baixando {nome}...", end=" ", flush=True)
                try:
                    ftp = ftplib.FTP(FTP_HOST, timeout=120)
                    ftp.login()
                    ftp.cwd(f"pdet/microdados/CAGED/{ano}")
                    with open(local, "wb") as f:
                        ftp.retrbinary(f"RETR {nome}", f.write)
                    ftp.quit()
                    print(f"OK ({os.path.getsize(local)/1e6:.1f} MB)")
                except Exception as e:
                    print(f"ERRO: {e}")
                    continue

            # Extrair e filtrar
            n_campos = 0
            try:
                with tempfile.TemporaryDirectory() as td:
                    with py7zr.SevenZipFile(local, "r") as z:
                        z.extractall(td)
                    txts = [f for f in os.listdir(td) if f.upper().endswith((".TXT", ".COMT"))]
                    if not txts:
                        txts = [f for f in os.listdir(td) if not f.startswith(".")]
                    if not txts:
                        continue

                    with open(os.path.join(td, txts[0]), "r", encoding="latin-1", errors="replace") as fh:
                        reader = csv_mod.reader(fh, delimiter=";")
                        header = next(reader)  # pular cabecalho
                        for row in reader:
                            try:
                                if len(row) < 12:
                                    continue
                                mun = row[2].strip()
                                if mun != MUN_COD:
                                    continue
                                n_campos += 1

                                mov = "Admitido" if row[0].strip() == "01" else ("Desligado" if row[0].strip() == "02" else row[0].strip())
                                comp = row[1].strip()
                                cbo = row[4].strip() if len(row) > 4 else ""
                                cnae = row[6].strip() if len(row) > 6 else ""
                                cnae_sub = row[22].strip() if len(row) > 22 else ""
                                instrucao = row[9].strip() if len(row) > 9 else ""
                                sexo = "M" if row[10].strip() == "01" else ("F" if row[10].strip() == "02" else row[10].strip()) if len(row) > 10 else ""
                                idade_fx = row[11].strip() if len(row) > 11 else ""
                                horas_fx = row[14].strip() if len(row) > 14 else ""
                                remun_fx = row[15].strip() if len(row) > 15 else ""

                                todos_registros.append({
                                    "fonte": "CAGED",
                                    "competencia": comp,
                                    "ano": comp[:4] if len(comp) >= 4 else str(ano),
                                    "mes": comp[4:6] if len(comp) >= 6 else "",
                                    "municipio": mun,
                                    "cbo": cbo,
                                    "cnae_classe": cnae,
                                    "cnae_subclasse": cnae_sub,
                                    "movimentacao": mov,
                                    "sexo": sexo,
                                    "faixa_etaria": idade_fx,
                                    "grau_instrucao": instrucao,
                                    "faixa_horas": horas_fx,
                                    "faixa_remun_sm": remun_fx,
                                })
                            except Exception:
                                pass

                print(f"      {nome}: {n_campos} movimentacoes em Campos")
            except Exception as e:
                print(f"      ERRO: {e}")

    if todos_registros:
        cols = ["fonte", "competencia", "ano", "mes", "municipio",
                "cbo", "cnae_classe", "cnae_subclasse", "movimentacao",
                "sexo", "faixa_etaria", "grau_instrucao", "faixa_horas", "faixa_remun_sm"]
        salvar_csv(todos_registros, "caged_campos_2018_2019.csv", cols)
        print(f"\n  Total CAGED Campos 2018-2019: {len(todos_registros)} movimentacoes")

        adm = sum(1 for r in todos_registros if r["movimentacao"] == "Admitido")
        desl = sum(1 for r in todos_registros if r["movimentacao"] == "Desligado")
        print(f"  Admitidos: {adm} | Desligados: {desl} | Saldo: {adm - desl}")
    else:
        print("  Nenhum registro CAGED encontrado para Campos.")


# ============================================================
# 3. ANP - Royalties do Petroleo
# ============================================================
def baixar_anp():
    """
    Baixa dados de royalties e participacoes especiais da ANP.
    Campos dos Goytacazes e um dos maiores recebedores de royalties do Brasil.
    Fonte: Dados Abertos ANP (https://www.gov.br/anp/)
    """
    print("\n" + "=" * 70)
    print("3. ANP - Royalties e Participacoes Especiais do Petroleo")
    print("=" * 70)

    DIR_ANP = os.path.join(DIR_BRUTOS, "anp")
    os.makedirs(DIR_ANP, exist_ok=True)

    # URL da API de dados abertos da ANP
    # Royalties: distribuicao por municipio
    url_royalties = (
        "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/"
        "arquivos/participacoes-governamentais/royalties/royalties-distribuicao-municipio.csv"
    )

    local = os.path.join(DIR_ANP, "royalties_distribuicao_municipio.csv")

    if not os.path.exists(local):
        print(f"  Baixando royalties ANP...")
        try:
            resp = requests.get(url_royalties, timeout=120, verify=False)
            resp.raise_for_status()
            with open(local, "wb") as f:
                f.write(resp.content)
            print(f"  OK ({len(resp.content) / 1e6:.1f} MB)")
        except Exception as e:
            print(f"  ERRO: {e}")
            return
    else:
        print(f"  Arquivo ja existe: {local}")

    # Filtrar Campos dos Goytacazes
    import csv as csv_mod
    registros = []
    try:
        with open(local, "r", encoding="latin-1", errors="replace") as f:
            reader = csv_mod.DictReader(f, delimiter=";")
            cols = reader.fieldnames
            print(f"  Colunas ANP: {cols[:8]}...")

            for row in reader:
                # Municipio pode vir como codigo ou nome
                municipio = row.get("municipio", row.get("Municipio", row.get("MUNICIPIO", "")))
                cod_ibge = row.get("cod_ibge", row.get("CodIbge", row.get("COD_IBGE", "")))

                if "330100" in str(cod_ibge) or "CAMPOS" in str(municipio).upper():
                    registros.append(row)

    except Exception as e:
        print(f"  ERRO ao processar: {e}")
        return

    if registros:
        campos_cols = [c for c in cols if c] if cols else registros[0].keys()
        salvar_csv_dict(registros, "anp_royalties_campos.csv", campos_cols)
        print(f"  Total registros ANP para Campos: {len(registros)}")

        # Sumario
        total = 0
        for r in registros:
            for k, v in r.items():
                if "VALOR" in k.upper() or "valor" in k:
                    try:
                        total += float(str(v).replace(",", "."))
                    except:
                        pass
        if total > 0:
            print(f"  Valor total royalties: R$ {total:,.2f}")
    else:
        print("  Nenhum registro ANP encontrado para Campos.")


# ============================================================
# 4. BEN/INSS - Beneficios Acidentarios
# ============================================================
def baixar_ben():
    """
    Baixa dados de beneficios acidentarios (B91, B92, B93, B94) do INSS.
    Via TabNet/DATASUS - resumo por municipio.
    Codigos de beneficio:
        B91: Auxilio-doenca por acidente de trabalho
        B92: Aposentadoria por invalidez por acidente de trabalho
        B93: Pensao por morte por acidente de trabalho
        B94: Auxilio-acidente por acidente de trabalho

    A API do TabNet DATASUS permite download de dados agregados por municipio.
    URL: http://tabnet.datasus.gov.br/cgi/deftohtm.exe?infologo/env/atbr.def
    """
    print("\n" + "=" * 70)
    print("4. BEN/INSS - Beneficios Acidentarios")
    print("=" * 70)

    DIR_BEN = os.path.join(DIR_BRUTOS, "ben-inss")
    os.makedirs(DIR_BEN, exist_ok=True)

    # Usar a API REST do TabNet DATASUS para baixar dados do municipio 330100
    # URL base do TabNet para beneficios acidentarios
    # Tabela: Infologo - Acidentes de Trabalho
    # Filtro: Municipio = 330100

    registros = []

    for ano in ANOS:
        print(f"  [{ano}] Buscando beneficios acidentarios...")

        # TabNet DATASUS - Acidentes de Trabalho
        # O TabNet usa POST com parametros especificos
        # Linha: Municipio, Coluna: Ano/Mes, Conteudo: Quantidade

        # URL do TabNet Infologo - AT (Acidentes de Trabalho)
        base_url = "http://tabnet.datasus.gov.br/cgi/tabcgi.exe"

        # Parametros para download CSV via TabNet
        params = {
            "infologo/env/atbr.def": None,  # Arquivo de definicao
        }

        # Tentar via API SIDRA/IBGE style ou via POST
        # Na pratica, o TabNet e complexo de automatizar. Alternativa:
        # Usar a API do portal gov.br ou baixar os CSVs manualmente

        print(f"    (BEN/INSS requer download manual via TabNet: http://tabnet.datasus.gov.br/cgi/deftohtm.exe?infologo/env/atbr.def)")
        print(f"    Filtrar por: Municipio = 330100 Campos dos Goytacazes, Periodo = {ano}")

    # Como o TabNet e dificil de automatizar, vamos criar uma instrucao de download manual
    # e tambem tentar via SIDRA/IBGE que tem API REST

    instrucoes_path = os.path.join(DIR_BEN, "INSTRUCOES_DOWNLOAD.txt")
    with open(instrucoes_path, "w", encoding="utf-8") as f:
        f.write("""INSTRUCOES PARA DOWNLOAD MANUAL DO BEN/INSS
==============================================

1. Acessar: http://tabnet.datasus.gov.br/cgi/deftohtm.exe?infologo/env/atbr.def

2. Configurar:
   - Linha: Municipio
   - Coluna: Ano do acidente
   - Conteudo: Quantidade de beneficios
   - Periodo: 2018 a 2025
   - Municipio: 330100 - Campos dos Goytacazes

3. Clicar em "Mostra" e depois em "Download CSV"

4. Salvar em: banco de dados/ben-inss/

ALTERNATIVA: Usar o pacote microdatasus (R):
   library(microdatasus)
   ben <- fetch_datasus(
     information_system = "INSS-AT",
     year_start = 2018,
     year_end = 2025,
     vars = c("MUN_NOT", "DT_ACID", "TP_BENEF", "SEXO", "IDADE")
   )
""")
    print(f"  Instrucoes de download salvas em: {instrucoes_path}")


# ============================================================
# 5. SIH/SUS - Internacoes Hospitalares
# ============================================================
def baixar_sih():
    """
    Baixa dados de internacoes hospitalares (SIH/SUS) via FTP DATASUS.
    Filtra por municipio de residencia = 330100 (Campos dos Goytacazes).
    
    Arquivos: RD (Reduzida) - dados de AIH (Autorizacao de Internacao Hospitalar).
    Formato: .dbc (DBF comprimido)
    Localizacao: ftp.datasus.gov.br/dissemin/publicos/SIHSUS/
    
    Colunas de interesse:
    - MUNIC_RES: Municipio de residencia
    - DIAG_PRINC: Diagnostico principal (CID-10)
    - CAUSAS_EXT: Causas externas (se aplicavel)
    - IDADE, SEXO: Demograficos
    - DT_INTER, DT_SAIDA: Datas
    - VAL_TOT: Valor total da internacao
    - DIAS_PERM: Dias de permanencia
    """
    print("\n" + "=" * 70)
    print("5. SIH/SUS - Internacoes Hospitalares")
    print("=" * 70)

    FTP_HOST = "ftp.datasus.gov.br"
    DIR_SIH = os.path.join(DIR_BRUTOS, "sih")
    os.makedirs(DIR_SIH, exist_ok=True)

    # SIH: dados de AIH por estado
    # Caminho: dissemin/publicos/SIHSUS/200801_/Dados/RJ*.dbc
    # Para anos mais recentes, o caminho pode variar

    SIH_PATHS = [
        "dissemin/publicos/SIHSUS/200801_/Dados",  # Dados por estado
    ]

    print("  Explorando FTP do DATASUS para SIH...")
    ftp = ftplib.FTP(FTP_HOST, timeout=30)
    ftp.login()

    # Procurar arquivos RJ
    arquivos_rj = []
    for base_path in SIH_PATHS:
        try:
            ftp.cwd(base_path)
            conteudo = []
            ftp.retrlines("LIST", conteudo.append)
            for linha in conteudo:
                partes = linha.split()
                if len(partes) < 4:
                    continue
                nome = partes[-1]
                if "RJ" in nome.upper() and nome.upper().endswith(".DBC"):
                    tamanho = int(partes[3]) if len(partes) > 3 and partes[3].isdigit() else 0
                    # Extrair ano
                    import re
                    m = re.search(r"(20\d{2})", nome)
                    ano = int(m.group(1)) if m else 0
                    if ano in ANOS:
                        arquivos_rj.append({
                            "nome": nome,
                            "ano": ano,
                            "tamanho_mb": round(tamanho / 1e6, 1),
                            "path": f"{base_path}/{nome}",
                        })
        except Exception as e:
            print(f"  Erro ao acessar {base_path}: {e}")

    ftp.quit()

    if arquivos_rj:
        print(f"  Encontrados {len(arquivos_rj)} arquivos SIH/RJ:")
        for a in sorted(arquivos_rj, key=lambda x: x["ano"]):
            print(f"    {a['ano']}: {a['nome']} ({a['tamanho_mb']} MB)")

        # Download e processamento
        registros_sih = []
        for a in sorted(arquivos_rj, key=lambda x: x["ano"]):
            local = os.path.join(DIR_SIH, a["nome"])
            if not os.path.exists(local):
                print(f"  [{a['ano']}] Baixando {a['nome']}...")
                try:
                    ftp = ftplib.FTP(FTP_HOST, timeout=120)
                    ftp.login()
                    with open(local, "wb") as f:
                        ftp.retrbinary(f"RETR {a['path']}", f.write)
                    ftp.quit()
                    print(f"    OK ({a['tamanho_mb']} MB)")
                except Exception as e:
                    print(f"    ERRO: {e}")
                    continue

            # Ler DBC e filtrar
            try:
                from dbfread import DBF
                print(f"  [{a['ano']}] Processando {a['nome']}...")
                dbf = DBF(local, encoding="latin-1", char_decode_errors="replace")
                
                # Identificar colunas
                col_mun = None
                for campo in dbf.fields:
                    if "MUNIC_RES" in campo.name.upper() or "MUNIC_MOV" in campo.name.upper():
                        col_mun = campo.name
                        break
                
                if col_mun is None:
                    print(f"    Coluna municipio nao encontrada. Campos: {[f.name for f in dbf.fields[:10]]}")
                    continue

                n_campos = 0
                for record in dbf:
                    try:
                        mun = str(record.get(col_mun, "")).strip()
                        if mun == MUN_COD or mun.startswith(MUN_COD):
                            n_campos += 1
                            rec = {}
                            for k, v in record.items():
                                if isinstance(v, bytes):
                                    try:
                                        rec[k] = v.decode("latin-1", errors="replace").strip()
                                    except:
                                        rec[k] = str(v)
                                else:
                                    rec[k] = str(v).strip() if v is not None else ""
                            rec["_ano"] = a["ano"]
                            rec["_fonte"] = "SIH/SUS"
                            registros_sih.append(rec)
                    except Exception:
                        pass

                print(f"    Campos: {n_campos} internacoes")
            except Exception as e:
                print(f"    ERRO ao processar: {e}")

        if registros_sih:
            # Consolidar colunas (podem variar entre anos)
            from collections import OrderedDict
            cols_meta = ["_ano", "_fonte"]
            cols_data = set()
            for r in registros_sih:
                cols_data.update(r.keys())
            cols_data = sorted(cols_data - set(cols_meta))
            all_cols = cols_meta + cols_data

            salvar_csv_dict(registros_sih, "sih_campos_2018_2025.csv", all_cols)
            print(f"\n  Total internacoes SIH Campos: {len(registros_sih)}")
        else:
            print("  Nenhuma internacao SIH encontrada para Campos.")
    else:
        print("  Nenhum arquivo SIH/RJ encontrado no FTP.")
        print("  O DATASUS pode ter reorganizado os diretorios.")
        print("  Alternativa: usar microdatasus (R) ou fazer download manual.")
        print("  URL: ftp.datasus.gov.br/dissemin/publicos/SIHSUS/")


# ============================================================
# UTILITARIOS
# ============================================================
def salvar_csv(registros, nome_arquivo, colunas):
    """Salva lista de dicionarios como CSV."""
    import csv as csv_mod
    path = os.path.join(DIR_PROC, nome_arquivo)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv_mod.DictWriter(f, fieldnames=colunas, delimiter=";")
        writer.writeheader()
        writer.writerows(registros)
    print(f"    Salvo: {path} ({len(registros)} registros)")


def salvar_csv_dict(registros, nome_arquivo, colunas=None):
    """Salva lista de dicionarios como CSV, auto-detectando colunas."""
    import csv as csv_mod
    path = os.path.join(DIR_PROC, nome_arquivo)
    if colunas is None:
        colunas = list(registros[0].keys()) if registros else []
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv_mod.DictWriter(f, fieldnames=colunas, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(registros)
    print(f"    Salvo: {path} ({len(registros)} registros)")


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Download de bases complementares")
    parser.add_argument("--todas", action="store_true", help="Baixar todas as bases")
    parser.add_argument("--sinan", action="store_true", help="Baixar SINAN")
    parser.add_argument("--caged", action="store_true", help="Baixar CAGED")
    parser.add_argument("--anp", action="store_true", help="Baixar ANP")
    parser.add_argument("--ben", action="store_true", help="Baixar BEN/INSS")
    parser.add_argument("--sih", action="store_true", help="Baixar SIH/SUS")
    args = parser.parse_args()

    # Se nenhum argumento, mostrar ajuda
    if not any([args.todas, args.sinan, args.caged, args.anp, args.ben, args.sih]):
        parser.print_help()
        print("\nUse --todas para baixar todas as bases.")
        return

    print("=" * 70)
    print("DOWNLOAD DE BASES COMPLEMENTARES")
    print(f"Municipio: Campos dos Goytacazes ({MUN_COD})")
    print(f"Periodo: 2018-2025")
    print("=" * 70)

    if args.todas or args.sinan:
        baixar_sinan()

    if args.todas or args.caged:
        try:
            baixar_caged()
        except Exception as e:
            print(f"  CAGED ERRO: {e}")

    if args.todas or args.anp:
        try:
            baixar_anp()
        except Exception as e:
            print(f"  ANP ERRO: {e}")

    if args.todas or args.ben:
        try:
            baixar_ben()
        except Exception as e:
            print(f"  BEN/INSS ERRO: {e}")

    if args.todas or args.sih:
        try:
            baixar_sih()
        except Exception as e:
            print(f"  SIH/SUS ERRO: {e}")

    print("\n" + "=" * 70)
    print("DOWNLOAD CONCLUIDO")
    print("=" * 70)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    main()
