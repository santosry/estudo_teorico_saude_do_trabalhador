# -*- coding: utf-8 -*-
"""
download_rais_campos.py
======================
Baixa os microdados da RAIS (Vinculos) do FTP do MTE e extrai APENAS os
registros de Campos dos Goytacazes (codigo IBGE 330100), filtrando pelas
profissoes da saude.

COMO FUNCIONA A EXTRACAO (explicacao passo a passo):
=====================================================

1. FONTE: FTP oficial do Ministerio do Trabalho e Emprego
   ftp.mtps.gov.br/pdet/microdados/RAIS/{ANO}/

2. A RAIS e dividida em pacotes REGIONAIS. Cada ano tem estes arquivos:
   - RAIS_VINC_PUB_CENTRO_OESTE.7z
   - RAIS_VINC_PUB_MG_ES_RJ.7z       <-- ESTE contem Campos (RJ)
   - RAIS_VINC_PUB_NORDESTE.7z
   - RAIS_VINC_PUB_NORTE.7z
   - RAIS_VINC_PUB_SP.7z
   - RAIS_VINC_PUB_SUL.7z
   - RAIS_VINC_PUB_NI.7z             (nao identificado)

   Campos dos Goytacazes (RJ) esta no pacote MG_ES_RJ.
   NAO e preciso baixar o Brasil inteiro!

3. CADA .7z CONTEM UM UNICO ARQUIVO .TXT gigante (~7-10 GB descompactado):
   - RAIS_VINC_PUB_MG_ES_RJ.txt
   - Delimitador: ";" (2018-2022) ou "," (2023+)
   - Encoding: Latin-1 (ISO-8859-1)
   - Cabecalho com ~25-27 colunas que variam entre anos

4. COLUNAS PRINCIPAIS USADAS NO FILTRO (posicoes aproximadas, variam por ano):
   - Municipio (6 digitos): codigo IBGE. Campos = "330100"
   - CBO 2002: Classificacao Brasileira de Ocupacoes (6 digitos)
   - CNAE 2.0 Classe: Classificacao Nacional de Atividades Economicas
   - Vinculo Ativo em 31/12: "1" = ativo, "0" = inativo
   - Sexo do Trabalhador: "1"=M, "2"=F
   - Natureza Juridica
   - Remuneracao em Dezembro (valor nominal em R$)

5. EXTRACAO DO .7z: usa py7zr (Python). Cada arquivo .7z e extraido para
   uma pasta TEMPORARIA, o .txt e lido em streaming (linha a linha) e os
   registros de Campos sao filtrados. Depois o .txt temporario e apagado.

6. CLASSIFICACAO DAS PROFISSOES DE SAUDE (por familia CBO):
   - 2235: Enfermeiros
   - 3222: Tecnicos e auxiliares de enfermagem
   - 2251, 2252, 2253, 2231: Medicina
   - 2236: Fisioterapia
   - 2234: Farmacia
   - 3251: Tecnicos e auxiliares de farmacia
   - 2237: Nutricao
   - 2238: Fonoaudiologia
   - 2232, 3224: Odontologia e saude bucal
   - 3241, 3242, 5152: Diagnostico e laboratorio
   - 5151: Agentes comunitarios de saude
   - 3226: Instrumentacao cirurgica
   - 2515: Psicologia
   - 2516: Servico social
   - 2241: Educacao fisica
   - 2211: Biologia
   - 2212: Biomedicina

7. SAIDA: arquivo CSV contendo APENAS os vinculos de saude em Campos,
   bem menor que o arquivo original (de ~7 GB para alguns MB).

REQUISITOS:
    pip install py7zr

USO:
    python scripts/download_rais_campos.py
"""
import os
import csv
import sys
import time
import ftplib
import tempfile
import py7zr
from collections import defaultdict, Counter

# ============================================================
# CONFIGURACAO
# ============================================================
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

# Codigo IBGE de Campos dos Goytacazes
MUN_COD = "330100"

# Anos para baixar
ANOS = list(range(2018, 2026))

# FTP do MTE
FTP_HOST = "ftp.mtps.gov.br"
FTP_DIR = "/pdet/microdados/RAIS"

# Pastas onde procurar os .7z (ja existentes ou onde serao baixados)
DIR_7Z = os.path.join("dados", "brutos", "banco de dados/rais")
DIR_RAIS_EXISTENTE = os.path.join(RAIZ, "banco de dados", "banco de dados/rais")  # Pasta onde ja estao os .7z
os.makedirs(DIR_7Z, exist_ok=True)

# Pasta de destino para o CSV filtrado
DIR_SAIDA = os.path.join("saidas", "tabelas")
os.makedirs(DIR_SAIDA, exist_ok=True)

# Se False, remove o .7z apos extrair (economiza espaco)
MANTER_7Z = True

# Arquivo remoto (so MG_ES_RJ, onde esta Campos)
ARQ_REMOTO = "RAIS_VINC_PUB_MG_ES_RJ.7z"

# ============================================================
# CLASSIFICACAO CBO > categoria da saude
# ============================================================
def classificar_cbo(cbo: str):
    """Classifica um codigo CBO de 6 digitos em uma categoria da saude."""
    if not cbo or len(cbo) < 4:
        return None
    fam = cbo[:4]

    # Mapa familias CBO > categoria
    mapa_familias = {
        "2235": "Enfermagem - enfermeiros",
        "3222": "Enfermagem - tecnicos e auxiliares",
        "2251": "Medicina",
        "2252": "Medicina",
        "2253": "Medicina",
        "2231": "Medicina",
        "2236": "Fisioterapia",
        "2234": "Farmacia",
        "3251": "Farmacia - tecnicos e auxiliares",
        "2237": "Nutricao",
        "2238": "Fonoaudiologia",
        "2232": "Odontologia e saude bucal",
        "3224": "Odontologia e saude bucal",
        "3241": "Diagnostico e laboratorio - tecnicos e auxiliares",
        "3242": "Diagnostico e laboratorio - tecnicos e auxiliares",
        "5152": "Diagnostico e laboratorio - tecnicos e auxiliares",
        "5151": "Agentes comunitarios de saude e afins",
        "3226": "Instrumentacao cirurgica",
        "2515": "Psicologia",
        "2516": "Servico social",
        "2241": "Educacao fisica",
        "2211": "Biologia",
        "2212": "Biomedicina",
    }

    # Overrides para CBOs especificos que tem familia ambigua
    overrides = {
        "322225": "Instrumentacao cirurgica",
        "515140": "Agentes de combate às endemias",
        "515210": "Farmacia - tecnicos e auxiliares",
        "223305": "Medicina veterinaria",
    }

    if cbo in overrides:
        return overrides[cbo]
    return mapa_familias.get(fam)


# ============================================================
# DOWNLOAD via FTP
# ============================================================
def baixar_arquivo_ftp(ano: int) -> str:
    """
    Baixa o arquivo RAIS_VINC_PUB_MG_ES_RJ.7z do FTP do MTE.
    Primeiro procura na pasta banco de dados/rais/ (arquivos ja existentes),
    depois em dados/brutos/rais/, depois baixa do FTP.
    Retorna o caminho local do arquivo.
    """
    nome_local = f"RAIS_{ano}_MG_ES_RJ.7z"

    # 1. Procurar na pasta rais/ (arquivos que ja estao no projeto)
    caminho_existente = os.path.join(DIR_RAIS_EXISTENTE, nome_local)
    if os.path.exists(caminho_existente):
        tamanho_mb = os.path.getsize(caminho_existente) / (1024**2)
        print(f"  [{ano}] Ja existe em rais/ ({tamanho_mb:.0f} MB) - pulando download.")
        return caminho_existente

    # 2. Procurar em dados/brutos/rais/
    caminho_local = os.path.join(DIR_7Z, nome_local)
    if os.path.exists(caminho_local):
        tamanho_mb = os.path.getsize(caminho_local) / (1024**2)
        print(f"  [{ano}] Ja existe em dados/brutos/rais/ ({tamanho_mb:.0f} MB) - pulando download.")
        return caminho_local

    print(f"  [{ano}] Conectando ao FTP {FTP_HOST}...")
    ftp = ftplib.FTP(FTP_HOST, timeout=120)
    ftp.login()
    ftp.cwd(f"{FTP_DIR}/{ano}")

    # Ver tamanho remoto
    try:
        tamanho_remoto = ftp.size(ARQ_REMOTO)
        print(f"  [{ano}] Tamanho remoto: {tamanho_remoto / (1024**2):.0f} MB")
    except Exception:
        tamanho_remoto = None
        print(f"  [{ano}] Nao foi possivel obter tamanho remoto.")

    # Download com barra de progresso
    print(f"  [{ano}] Baixando {ARQ_REMOTO}...")
    caminho_tmp = caminho_local + ".part"

    baixado = [0]

    def callback_bloco(data):
        baixado[0] += len(data)
        if tamanho_remoto:
            pct = baixado[0] / tamanho_remoto * 100
            mb = baixado[0] / (1024**2)
            print(f"\r  [{ano}] Progresso: {pct:.1f}% ({mb:.1f} MB)", end="")
        else:
            mb = baixado[0] / (1024**2)
            print(f"\r  [{ano}] Baixado: {mb:.1f} MB", end="")

    try:
        with open(caminho_tmp, "wb") as f:
            ftp.retrbinary(f"RETR {ARQ_REMOTO}", f.write, blocksize=1 << 20,
                           callback=callback_bloco)
        ftp.quit()
    except Exception as e:
        ftp.quit()
        print(f"\n  [{ano}] ERRO NO DOWNLOAD: {e}")
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)
        raise

    # Renomear .part > final
    os.rename(caminho_tmp, caminho_local)
    tamanho_final = os.path.getsize(caminho_local) / (1024**2)
    print(f"\n  [{ano}] Download concluido! ({tamanho_final:.0f} MB)")
    print(f"  [{ano}] Salvo em: {caminho_local}")
    return caminho_local


# ============================================================
# EXTRACAO: descompactar .7z e filtrar Campos + saude
# ============================================================
def extrair_e_filtrar(ano: int, caminho_7z: str):
    """
    Extrai o .7z, le o .txt linha a linha e filtra:
    - Municipio == 330100 (Campos dos Goytacazes)
    - Vinculo ativo em 31/12
    - CBO de profissao da saude
    Retorna lista de dicionarios com os registros filtrados.
    """
    print(f"  [{ano}] Extraindo .7z com py7zr...")
    inicio = time.time()

    registros = []

    with tempfile.TemporaryDirectory() as pasta_temp:
        # 1. Extrair o .7z para pasta temporaria
        with py7zr.SevenZipFile(caminho_7z, "r") as z:
            z.extractall(pasta_temp)

        # 2. Encontrar o .txt extraido
        arquivos = os.listdir(pasta_temp)
        txts = [f for f in arquivos if f.upper().endswith((".TXT", ".COMT"))]
        if not txts:
            # Fallback: pegar o primeiro arquivo que nao seja oculto
            txts = [f for f in arquivos if not f.startswith(".")]
        if not txts:
            print(f"  [{ano}] ERRO: Nenhum arquivo encontrado no .7z!")
            print(f"  [{ano}] Conteudo: {arquivos[:10]}")
            return registros

        caminho_txt = os.path.join(pasta_temp, txts[0])
        tamanho_txt = os.path.getsize(caminho_txt) / (1024**3)
        print(f"  [{ano}] Arquivo extraido: {txts[0]} ({tamanho_txt:.1f} GB)")

        # 3. Ler o cabecalho e detectar delimitador
        with open(caminho_txt, "r", encoding="latin-1", errors="replace") as f:
            header_line = f.readline().rstrip("\n")

            # 2018-2022 usa ";", 2023+ usa ","
            delim = ";" if header_line.count(";") > header_line.count(",") else ","
            colunas = [c.strip().strip('"') for c in header_line.split(delim)]

            print(f"  [{ano}] Delimitador='{delim}', {len(colunas)} colunas detectadas")

            # 4. Detectar POSICOES das colunas pelo nome
            idx = {}
            for i, nome in enumerate(colunas):
                n = nome.upper()
                # CBO 2002
                if "CBO" in n and ("2002" in n or "OCUPA" in n):
                    idx["cbo"] = i
                # CNAE 2.0
                if ("CNAE" in n and ("20" in n or "CLASSE" in n)) or "CNAE 2.0" in n:
                    idx["cnae"] = i
                # Municipio
                if ("MUNICIPIO" == n.strip().upper() or
                    ("MUNIC" in n and "IBGE" not in n)):
                    idx["mun"] = i
                # Vinculo ativo 31/12
                if ("ATIVO" in n and "31" in n) or "VINCULO ATIVO" in n:
                    idx["ativo"] = i
                # Sexo
                if "SEXO" in n and "TRAB" in n:
                    idx["sexo"] = i
                # Natureza Juridica
                if "NATUREZA" in n and "JUR" in n:
                    idx["natjur"] = i
                # Remuneracao Dezembro
                if ("VL REMUN" in n or "VALOR REMUN" in n or "REMUNERACAO" in n):
                    if ("MEDIA" in n or "DEZEM" in n) and "remun_dez" not in idx:
                        idx["remun_dez"] = i
                # Faixa Remuneracao (SM) - pre-2023
                if "FAIXA REMUN" in n and "DEZEM" in n:
                    idx["faixa_remun"] = i
                # Horas contratadas
                if ("HORA" in n and "CONTR" in n) or "HORAS CONTRATUAIS" in n:
                    idx["horas"] = i
                # Faixa etaria
                if "FAIXA ET" in n or "IDADE" in n:
                    idx["idade"] = i
                # Escolaridade
                if "ESCOLARIDADE" in n or "GRAU INSTRU" in n:
                    idx["escolaridade"] = i

            # Fallback: se nao achou CBO, procura qualquer coluna com "CBO"
            if "cbo" not in idx:
                for i, nome in enumerate(colunas):
                    if "CBO" in nome.upper():
                        idx["cbo"] = i
                        break
            if "mun" not in idx:
                for i, nome in enumerate(colunas):
                    if "MUNIC" in nome.upper():
                        idx["mun"] = i
                        break

            print(f"  [{ano}] Indices: cbo={idx.get('cbo')}, mun={idx.get('mun')}, "
                  f"ativo={idx.get('ativo')}, sexo={idx.get('sexo')}, "
                  f"remun_dez={idx.get('remun_dez')}")

            # Verificar colunas criticas
            if "cbo" not in idx or "mun" not in idx:
                print(f"  [{ano}] ERRO: Nao foi possivel identificar colunas CBO/Municipio.")
                print(f"  [{ano}] Cabecalho: {colunas}")
                return registros

            max_col = max(idx.values())

            # 5. Ler linha a linha e filtrar
            n_lido = 0
            n_campos = 0
            n_saude = 0
            reader = csv.reader(f, delimiter=delim, quotechar='"')

            for row in reader:
                n_lido += 1
                if n_lido % 500000 == 0:
                    print(f"\r  [{ano}] Lidas {n_lido/1e6:.1f}M linhas... "
                          f"Campos={n_campos}, Saude={n_saude}", end="")

                try:
                    if len(row) <= max_col:
                        continue

                    # Filtro 1: Municipio
                    mun_val = row[idx["mun"]].strip()
                    if mun_val != MUN_COD:
                        # So conta Campos para mostrar no log
                        if mun_val == MUN_COD:
                            n_campos += 1
                        continue
                    n_campos += 1

                    # Filtro 2: Vinculo ativo em 31/12
                    if "ativo" in idx:
                        if row[idx["ativo"]].strip() != "1":
                            continue

                    # Filtro 3: CBO da saude
                    cbo_val = row[idx["cbo"]].strip()
                    if not cbo_val[:1].isdigit():
                        continue
                    cat = classificar_cbo(cbo_val)
                    if not cat:
                        continue
                    n_saude += 1

                    # Extrair campos de interesse
                    cnae_val = row[idx["cnae"]].strip() if "cnae" in idx else ""

                    # Sexo
                    sx_val = row[idx["sexo"]].strip() if "sexo" in idx else ""
                    if sx_val in ("1", "M", "MASCULINO"):
                        sexo = "M"
                    elif sx_val in ("2", "F", "FEMININO"):
                        sexo = "F"
                    else:
                        sexo = "NI"

                    # Natureza juridica
                    natjur = row[idx["natjur"]].strip() if "natjur" in idx else ""

                    # Remuneracao
                    remun = ""
                    if "remun_dez" in idx:
                        try:
                            v = row[idx["remun_dez"]].strip().replace(",", ".")
                            if v:
                                remun = str(float(v))
                        except ValueError:
                            remun = row[idx["remun_dez"]].strip()

                    # Horas
                    horas = row[idx["horas"]].strip() if "horas" in idx else ""

                    registros.append({
                        "ano": ano,
                        "cbo": cbo_val,
                        "categoria": cat,
                        "sexo": sexo,
                        "natjur": natjur,
                        "remuneracao_dez": remun,
                        "horas_contratuais": horas,
                        "cnae_classe": cnae_val,
                        "municipio": MUN_COD,
                    })

                except Exception:
                    pass  # Linha malformada, ignorar

    # Fim da extracao
    tempo = time.time() - inicio
    print(f"\n  [{ano}] TOTAL: {n_lido/1e6:.1f}M linhas lidas | "
          f"Campos={n_campos} | Saude ativa={n_saude} | "
          f"Tempo={tempo/60:.1f} min")

    return registros


# ============================================================
# SALVAR RESULTADOS
# ============================================================
def salvar_resultados(todos_registros: list[dict]):
    """Salva os registros filtrados em CSV e gera sumario."""

    if not todos_registros:
        print("\n!! Nenhum registro encontrado!")
        return

    # 1. CSV completo com todos os registros
    csv_path = os.path.join(DIR_SAIDA, "RAIS_campos_saude_2018_2025.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        colunas = ["ano", "cbo", "categoria", "sexo", "natjur",
                    "remuneracao_dez", "horas_contratuais", "cnae_classe",
                    "municipio"]
        writer = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        writer.writeheader()
        writer.writerows(todos_registros)

    tamanho_mb = os.path.getsize(csv_path) / (1024**2)
    print(f"\n[OK] CSV salvo: {csv_path} ({tamanho_mb:.1f} MB, {len(todos_registros)} registros)")

    # 2. Sumario por ano e categoria
    sumario = defaultdict(lambda: defaultdict(int))
    for r in todos_registros:
        sumario[r["ano"]][r["categoria"]] += 1

    sumario_path = os.path.join(DIR_SAIDA, "RAIS_campos_saude_sumario.csv")
    with open(sumario_path, "w", newline="", encoding="utf-8-sig") as f:
        cats = sorted(set(r["categoria"] for r in todos_registros))
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Categoria"] + [str(a) for a in ANOS] + ["Total"])
        for cat in cats:
            total = sum(sumario[ano].get(cat, 0) for ano in ANOS)
            writer.writerow([cat] + [sumario[ano].get(cat, 0) for ano in ANOS] + [total])

    print(f"[OK] Sumario salvo: {sumario_path}")

    # 3. Imprimir sumario no terminal
    print("\n" + "=" * 70)
    print("RESUMO: Vinculos ativos de saude em Campos dos Goytacazes (RAIS)")
    print("=" * 70)
    print(f"{'Categoria':<45} Total 2018-2025")
    print("-" * 70)
    for cat in cats:
        total = sum(sumario[ano].get(cat, 0) for ano in ANOS)
        print(f"  {cat:<43} {total}")
    print("-" * 70)
    geral = sum(sum(sumario[ano].values()) for ano in ANOS)
    print(f"  {'TOTAL':<43} {geral}")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("DOWNLOAD E EXTRACAO DA RAIS - CAMPOS DOS GOYTACAZES (330100)")
    print("Profissoes da saude | 2018-2025 | Vinculos formais (celetistas)")
    print("=" * 70)
    print(f"FTP: {FTP_HOST}{FTP_DIR}")
    print(f"Arquivo: {ARQ_REMOTO} (apenas MG_ES_RJ)")
    print(f"Municipio: {MUN_COD} (Campos dos Goytacazes, RJ)")
    print(f"Anos: {ANOS[0]}–{ANOS[-1]}")
    print(f"Destino .7z: {DIR_7Z}")
    print(f"Destino CSV: {DIR_SAIDA}")
    print(f"Manter .7z apos extracao: {MANTER_7Z}")
    print("=" * 70)

    todos_registros = []

    for ano in ANOS:
        print(f"\n{'-'*60}")
        print(f">>> PROCESSANDO {ano}")
        print(f"{'-'*60}")

        try:
            # Etapa 1: Download
            caminho_7z = baixar_arquivo_ftp(ano)

            # Etapa 2: Extrair e filtrar
            registros_ano = extrair_e_filtrar(ano, caminho_7z)
            todos_registros.extend(registros_ano)

            # Etapa 3: Remover .7z (se configurado)
            if not MANTER_7Z:
                os.remove(caminho_7z)
                print(f"  [{ano}] .7z removido para economizar espaco.")

        except ftplib.error_perm as e:
            print(f"\n  [{ano}] !! ERRO FTP (permissao): {e}")
            print(f"  [{ano}] Verifique se o ano {ano} esta disponivel em "
                  f"ftp://{FTP_HOST}{FTP_DIR}/{ano}/")
            continue
        except ftplib.error_temp as e:
            print(f"\n  [{ano}] !! ERRO FTP (temporario): {e}")
            print(f"  [{ano}] O servidor pode estar sobrecarregado. Tente novamente.")
            continue
        except Exception as e:
            print(f"\n  [{ano}] !! ERRO: {type(e).__name__}: {e}")
            continue

        # Pequena pausa entre anos para nao sobrecarregar o FTP
        if ano != ANOS[-1]:
            time.sleep(2)

    # Salvar resultados finais
    print(f"\n{'='*60}")
    print(f"CONCLUIDO! Total de registros extraidos: {len(todos_registros)}")
    print(f"{'='*60}")
    salvar_resultados(todos_registros)


if __name__ == "__main__":
    main()
