# -*- coding: utf-8 -*-
"""
download_caged_campos.py
========================
Baixa todos os arquivos CAGED 2018-2019 do FTP do MTE e extrai APENAS as
movimentacoes de admissao/desligamento de Campos dos Goytacazes (330100).

Formato CAGEDEST: CSV delimitado por ';', 40 colunas.
  col 0: Tipo (01=Admitido, 02=Desligado)
  col 1: Competencia (AAAAMM)
  col 2: Municipio (6 digitos IBGE)  <-- FILTRO
  col 4: CBO 2002
  col 6: CNAE 2.0 Classe
  col 10: Sexo
  col 11: Faixa Etaria

USO:
    python scripts/download_caged_campos.py
"""
import os
import csv
import ftplib
import tempfile
import time
import py7zr
from datetime import datetime

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

MUN_COD = "330100"
ANOS = [2018, 2019]
FTP_HOST = "ftp.mtps.gov.br"
DIR_CAGED = os.path.join("banco de dados", "caged")
DIR_PROC = os.path.join("dados", "processados")
os.makedirs(DIR_CAGED, exist_ok=True)
os.makedirs(DIR_PROC, exist_ok=True)

COLS_SAIDA = [
    "fonte", "competencia", "ano", "mes", "municipio",
    "cbo", "cnae_classe", "cnae_subclasse", "movimentacao",
    "sexo", "faixa_etaria", "grau_instrucao", "faixa_horas", "faixa_remun_sm"
]


def baixar_arquivo(ftp, nome, local):
    """Baixa um arquivo com retry."""
    if os.path.exists(local):
        return True
    for tentativa in range(3):
        try:
            with open(local, "wb") as f:
                ftp.retrbinary(f"RETR {nome}", f.write, blocksize=1 << 20)
            return True
        except Exception as e:
            print(f"      Retry {tentativa+1}/3: {e}")
            if tentativa < 2:
                time.sleep(10)
    return False


def processar_arquivo(local):
    """Extrai e filtra um .7z do CAGED para Campos."""
    registros = []
    try:
        with tempfile.TemporaryDirectory() as td:
            with py7zr.SevenZipFile(local, "r") as z:
                z.extractall(td)

            txts = [f for f in os.listdir(td) if f.upper().endswith((".TXT", ".COMT"))]
            if not txts:
                txts = [f for f in os.listdir(td) if not f.startswith(".")]
            if not txts:
                return registros

            with open(os.path.join(td, txts[0]), "r", encoding="latin-1", errors="replace") as fh:
                reader = csv.reader(fh, delimiter=";")
                next(reader)  # pular cabecalho

                for row in reader:
                    try:
                        if len(row) < 12:
                            continue
                        mun = row[2].strip()
                        if mun != MUN_COD:
                            continue

                        mov = row[0].strip()
                        mov = "Admitido" if mov == "01" else ("Desligado" if mov == "02" else mov)
                        comp = row[1].strip()
                        cbo = row[4].strip() if len(row) > 4 else ""
                        cnae = row[6].strip() if len(row) > 6 else ""
                        cnae_sub = row[22].strip() if len(row) > 22 else ""
                        instrucao = row[9].strip() if len(row) > 9 else ""

                        sx = row[10].strip() if len(row) > 10 else ""
                        sexo = "M" if sx == "01" else ("F" if sx == "02" else sx)

                        idade_fx = row[11].strip() if len(row) > 11 else ""
                        horas_fx = row[14].strip() if len(row) > 14 else ""
                        remun_fx = row[15].strip() if len(row) > 15 else ""

                        registros.append({
                            "fonte": "CAGED",
                            "competencia": comp,
                            "ano": comp[:4] if len(comp) >= 4 else "",
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
    except Exception as e:
        print(f"      ERRO extracao: {e}")

    return registros


def main():
    print("=" * 70)
    print("DOWNLOAD CAGED - CAMPOS DOS GOYTACAZES (330100)")
    print(f"Periodo: {ANOS[0]}-{ANOS[-1]}")
    print("=" * 70)

    todos_registros = []

    for ano in ANOS:
        print(f"\n{'='*60}")
        print(f"  ANO {ano}")
        print(f"{'='*60}")

        # Conectar ao FTP
        ftp = ftplib.FTP(FTP_HOST, timeout=60)
        ftp.login()
        ftp.encoding = "latin-1"
        ftp.cwd(f"pdet/microdados/CAGED/{ano}")

        nomes = ftp.nlst()
        nomes_7z = sorted([n for n in nomes if n.upper().endswith(".7Z") and "CAGEDEST" in n.upper()])
        print(f"  {len(nomes_7z)} arquivos mensais encontrados")

        for nome in nomes_7z:
            print(f"\n  >> {nome}")
            local = os.path.join(DIR_CAGED, nome)

            # Download
            if not os.path.exists(local):
                print(f"    Baixando...", end=" ", flush=True)
                if baixar_arquivo(ftp, nome, local):
                    mb = os.path.getsize(local) / 1e6
                    print(f"OK ({mb:.1f} MB)")
                else:
                    print("FALHOU")
                    continue
            else:
                mb = os.path.getsize(local) / 1e6
                print(f"    Ja existe ({mb:.1f} MB)")

            # Processar
            print(f"    Processando...", end=" ", flush=True)
            regs = processar_arquivo(local)
            print(f"{len(regs)} movimentacoes em Campos")
            todos_registros.extend(regs)

        ftp.quit()

    # Salvar resultados
    if todos_registros:
        path = os.path.join(DIR_PROC, "caged_campos_2018_2019.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=COLS_SAIDA, delimiter=";")
            writer.writeheader()
            writer.writerows(todos_registros)
        mb = os.path.getsize(path) / 1e6
        print(f"\n{'='*70}")
        print(f"CSV salvo: {path} ({mb:.1f} MB, {len(todos_registros):,} registros)")

        # Resumo
        adm = sum(1 for r in todos_registros if r["movimentacao"] == "Admitido")
        desl = sum(1 for r in todos_registros if r["movimentacao"] == "Desligado")
        print(f"Admitidos: {adm:,} | Desligados: {desl:,} | Saldo: {adm-desl:,}")

        # Por ano
        from collections import Counter
        por_ano = Counter(r["ano"] for r in todos_registros)
        for a in sorted(por_ano):
            print(f"  {a}: {por_ano[a]:,} movimentacoes")
    else:
        print("\nNenhum registro encontrado.")


if __name__ == "__main__":
    main()
