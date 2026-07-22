# -*- coding: utf-8 -*-
"""
download_inss_completo.py
=========================
Download COMPLETO dos dados do portal de dados abertos do INSS
via dados.gov.br, com filtro para Campos dos Goytacazes (330100).

Datasets baixados:
  1. CAT (Comunicação de Acidente de Trabalho) — 2012 a 2025
  2. Benefícios Concedidos — 2012 a 2025
  3. Benefícios Mantidos (Ativos, Suspensos, Cessados) — 2021 a 2025
  4. Benefícios Emitidos (folha de pagamento) — 2021 a 2025
  5. Benefícios Indeferidos — 2012 a 2025
  6. Glossários de todas as bases

Datasets NÃO disponíveis como dados abertos (ver README):
  - Reabilitação Profissional
  - Perícias Médicas
  - NTEP (Nexo Técnico Epidemiológico Previdenciário)
  - Segurados por CNAE e Município
  - Cessação de Benefícios (já inclusa nos Mantidos como status "Cessado")

MÉTODO: Playwright (automação de navegador) para acessar a API pública do
dados.gov.br que requer cookies de sessão. Os arquivos são baixados do
bucket S3 armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com.

USO:
    python scripts/download_inss_completo.py [--dataset cat|concedidos|mantidos|emitidos|indeferidos|glossarios|todos]

REQUISITOS:
    pip install playwright openpyxl
    playwright install chromium
"""
import os, sys, csv, json, time, zipfile, tempfile, re, io, hashlib
import requests
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIGURAÇÃO
# ============================================================
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

MUN_COD = "330100"          # Campos dos Goytacazes (IBGE)
MUN_NOME = "CAMPOS DOS GOYTACAZES"
UF = "RJ"

DIR_BASE = os.path.join("banco de dados")
DIR_LOGS = "logs"
DIR_MANIFESTO = os.path.join("dados", "manifesto")
os.makedirs(DIR_BASE, exist_ok=True)
os.makedirs(DIR_LOGS, exist_ok=True)
os.makedirs(DIR_MANIFESTO, exist_ok=True)

ANOS_ALVO = list(range(2015, 2026))  # 2015 a 2025

# ID da organização INSS no dados.gov.br
ORG_ID = "51b6b5ce-16a9-4839-b9f5-af4a6fb34747"

# Datasets relevantes e seus diretórios de destino
DATASETS = {
    "cat": {
        "ids": [
            "inss-comunicacao-de-acidente-de-trabalho-cat1",
            "comunicacoes-de-acidente-de-trabalho-cat-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "cat-inss",
        "prefixo": "cat",
        "descricao": "Comunicação de Acidente de Trabalho (CAT)",
    },
    "concedidos": {
        "ids": [
            "inss-beneficios-concedidos1",
            "beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
            "beneficios-concedidos-dez-2012-a-nov-2018-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-concedidos-inss",
        "prefixo": "benef_concedidos",
        "descricao": "Benefícios Concedidos",
    },
    "mantidos": {
        "ids": [
            "inss-beneficios-mantidos",
            "beneficios-mantidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-mantidos-inss",
        "prefixo": "benef_mantidos",
        "descricao": "Benefícios Mantidos (Ativos + Suspensos + Cessados)",
    },
    "emitidos": {
        "ids": [
            "inss-beneficios-emitidos",
            "beneficios-emitidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-emitidos-inss",
        "prefixo": "benef_emitidos",
        "descricao": "Benefícios Emitidos (folha de pagamento)",
    },
    "indeferidos": {
        "ids": [
            "inss-beneficios-indeferidos",
            "beneficios-indeferidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
            "beneficios-indeferidos-entre-dez-2012-a-nov-2018-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-indeferidos-inss",
        "prefixo": "benef_indeferidos",
        "descricao": "Benefícios Indeferidos",
    },
    "glossarios": {
        "ids": [
            "glossarios-dos-arquivos-de-beneficios-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "glossarios-inss",
        "prefixo": "glossario",
        "descricao": "Glossários (dicionários de variáveis)",
    },
}

# ============================================================
# LOG E MANIFESTO
# ============================================================
log_entries = []
manifesto_entries = []

def log(msg, level="INFO"):
    """Registra mensagem com timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    print(entry)
    log_entries.append(entry)

def salvar_log():
    """Salva log em arquivo."""
    path = os.path.join(DIR_LOGS, "log_download_inss_completo.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_entries))
    log(f"Log salvo: {path}")

def salvar_manifesto():
    """Salva manifesto com SHA-256 dos arquivos baixados."""
    path = os.path.join(DIR_MANIFESTO, "manifesto_inss.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "arquivo", "url", "sha256", "tamanho_bytes", "registros_campos", "data_download"], delimiter=";")
        writer.writeheader()
        writer.writerows(manifesto_entries)
    log(f"Manifesto salvo: {path}")


# ============================================================
# API DO PORTAL DADOS.GOV.BR (via Playwright)
# ============================================================
def obter_recursos_datasets(ids_datasets):
    """
    Usa Playwright para acessar a API pública do dados.gov.br
    e obter a lista de recursos de cada dataset.
    Retorna dict: {dataset_id: [recursos]}
    """
    recursos_por_dataset = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors", "--disable-web-security"],
        )
        page = browser.new_page()

        # Acessar página da organização para obter cookies de sessão
        log("Obtendo sessão no dados.gov.br...")
        page.goto(
            f"https://dados.gov.br/dados/organizacoes/visualizar/instituto-nacional-do-seguro-social",
            wait_until="networkidle",
            timeout=60000,
        )
        page.wait_for_timeout(5000)

        for ds_id in ids_datasets:
            log(f"  Buscando recursos de: {ds_id}")

            # Buscar detalhes do dataset via API
            result = page.evaluate(
                """
                async (id) => {
                    const url = `https://dados.gov.br/api/publico/conjuntos-dados/buscar?offset=0&nome=${id}&titulo=&colunaOrdenacao=dataAtualizacao&direcaoOrdenacao=DESC&idOrganizacao=null&dadosAbertos=true`;
                    const resp = await fetch(url);
                    const data = await resp.json();
                    return data;
                }
            """,
                ds_id,
            )

            registros = result.get("registros", [])
            if registros:
                ds = registros[0]
                recursos = ds.get("resourcesAcessoRapido", [])
                recursos_por_dataset[ds_id] = recursos
                log(f"    {len(recursos)} recursos encontrados")
            else:
                # Tentar buscar por ID exato na lista completa
                result = page.evaluate(
                    """
                    async () => {
                        const url = `https://dados.gov.br/api/publico/conjuntos-dados/buscar?offset=0&nome=&titulo=&colunaOrdenacao=dataAtualizacao&direcaoOrdenacao=DESC&idOrganizacao=%s&dadosAbertos=true`;
                        const resp = await fetch(url);
                        const data = await resp.json();
                        return data;
                    }
                """
                    % ORG_ID,
                )

                # Paginar até encontrar
                all_regs = result.get("registros", [])
                for offset in range(20, 60, 20):
                    result = page.evaluate(
                        """
                        async (off) => {
                            const url = `https://dados.gov.br/api/publico/conjuntos-dados/buscar?offset=${off}&nome=&titulo=&colunaOrdenacao=dataAtualizacao&direcaoOrdenacao=DESC&idOrganizacao=%s&dadosAbertos=true`;
                            const resp = await fetch(url);
                            const data = await resp.json();
                            return data;
                        }
                    """
                        % ORG_ID,
                        offset,
                    )
                    regs = result.get("registros", [])
                    if not regs:
                        break
                    all_regs.extend(regs)

                for ds in all_regs:
                    if ds.get("name") == ds_id:
                        recursos = ds.get("resourcesAcessoRapido", [])
                        recursos_por_dataset[ds_id] = recursos
                        log(f"    {len(recursos)} recursos encontrados (busca completa)")
                        break

            if ds_id not in recursos_por_dataset:
                log(f"    NENHUM recurso encontrado!", "WARN")
                recursos_por_dataset[ds_id] = []

        browser.close()

    return recursos_por_dataset


# ============================================================
# DOWNLOAD DE ARQUIVOS
# ============================================================
def baixar_arquivo(url, destino, max_retries=3):
    """Baixa arquivo com retry e barra de progresso."""
    for tentativa in range(max_retries):
        try:
            resp = requests.get(url, timeout=300, stream=True)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            baixado = 0
            chunk_size = 1024 * 1024  # 1 MB

            with open(destino, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    baixado += len(chunk)
                    if total > 0:
                        pct = baixado / total * 100
                        print(f"\r    Baixando... {pct:.0f}% ({baixado / 1e6:.1f} MB / {total / 1e6:.1f} MB)", end="", flush=True)

            print()  # nova linha
            return True
        except Exception as e:
            log(f"    Tentativa {tentativa + 1} falhou: {e}", "WARN")
            time.sleep(5 * (tentativa + 1))

    return False


# ============================================================
# PROCESSAMENTO E FILTRO POR MUNICÍPIO
# ============================================================
def extrair_ano_mes_cat(nome_arquivo):
    """Extrai ano e mês do nome do arquivo CAT."""
    nome = nome_arquivo.upper()

    # Padrão: CAT-01-2023.csv, cat_202301.csv, D.SDA.PDA.005.CAT.202301.csv
    # competencia 01/2023, janeiro 2023

    # D.SDA.PDA.005.CAT.202301
    m = re.search(r"CAT[\.\-_]?(\d{4})(\d{2})", nome)
    if m:
        return int(m.group(1)), int(m.group(2))

    # comp01-02-03-2020, cat-comp01-02-03-2020
    m = re.search(r"(\d{4})", nome)
    if m:
        ano = int(m.group(1))
        # Tentar mês
        m_mes = re.search(r"comp(\d{2})|_(\d{2})_|\.(\d{2})\.", nome)
        if m_mes:
            mes = int(m_mes.group(1) or m_mes.group(2) or m_mes.group(3))
            return ano, mes
        # Meses por nome
        meses_nome = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
            "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
        }
        for mn, mv in meses_nome.items():
            if mn in nome:
                return ano, mv
        return ano, None

    return None, None


def extrair_ano_mes_benef(nome_arquivo):
    """Extrai ano e mês do nome do arquivo de benefícios."""
    nome = nome_arquivo.upper()

    # Padrão: concedidos-01-2019.csv, D.SDA.PDA.001.CON.202301.csv
    # beneficios-concedidos-competencia-12-2018.csv
    # DADOS ABERTOS_CONCEDIDOS_202306.csv

    # AAAAMM no nome
    m = re.search(r"(\d{4})(\d{2})", nome)
    if m:
        ano = int(m.group(1))
        mes = int(m.group(2))
        if 2012 <= ano <= 2025 and 1 <= mes <= 12:
            return ano, mes

    # MM-AAAA
    m = re.search(r"(\d{2})-(\d{4})", nome)
    if m:
        return int(m.group(2)), int(m.group(1))

    # competencia-MM-AAAA
    m = re.search(r"compet[\.\-_]?(\d{2})[\.\-_]?(\d{4})", nome, re.IGNORECASE)
    if m:
        return int(m.group(2)), int(m.group(1))

    # AAAA no nome
    m = re.search(r"(\d{4})", nome)
    if m:
        ano = int(m.group(1))
        if 2012 <= ano <= 2025:
            return ano, None

    return None, None


def filtrar_csv_campos(path_origem, path_destino, col_municipio="MUNIC_RES"):
    """
    Lê CSV (possivelmente ZIP) e filtra linhas de Campos dos Goytacazes.
    Retorna número de registros filtrados.
    """
    n_filtrados = 0
    n_total = 0

    try:
        # Tentar ler como ZIP primeiro
        if path_origem.lower().endswith(".zip"):
            with zipfile.ZipFile(path_origem, "r") as z:
                # Pegar o primeiro CSV dentro do ZIP
                csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
                if not csv_files:
                    # Tentar XLSX
                    xlsx_files = [f for f in z.namelist() if f.lower().endswith(".xlsx") or f.lower().endswith(".xls")]
                    if xlsx_files:
                        with z.open(xlsx_files[0]) as xf:
                            return filtrar_xlsx_campos(io.BytesIO(xf.read()), path_destino)
                    return 0

                with z.open(csv_files[0]) as f:
                    return _filtrar_csv_stream(f, path_destino, col_municipio)
        else:
            with open(path_origem, "r", encoding="latin-1", errors="replace") as f:
                return _filtrar_csv_stream(f, path_destino, col_municipio)

    except Exception as e:
        log(f"    ERRO ao filtrar CSV: {e}", "ERROR")
        return 0


def _filtrar_csv_stream(file_handle, path_destino, col_municipio):
    """Filtra CSV em streaming, escrevendo linhas de Campos."""
    n_filtrados = 0
    n_total = 0

    # Ler primeira linha para detectar encoding e delimitador
    primeira_linha = file_handle.readline()
    if isinstance(primeira_linha, bytes):
        primeira_linha = primeira_linha.decode("latin-1", errors="replace")

    # Detectar delimitador
    if ";" in primeira_linha:
        delim = ";"
    elif "\t" in primeira_linha:
        delim = "\t"
    else:
        delim = ","

    # Identificar coluna de município
    cabecalho = primeira_linha.strip().split(delim)
    col_idx = None
    for i, col in enumerate(cabecalho):
        col_upper = col.strip().upper().replace('"', "")
        if col_municipio.upper() in col_upper or "MUN_RES" in col_upper or "MUNICIPIO" in col_upper or "MUNIC_RES" in col_upper:
            col_idx = i
            break

    if col_idx is None:
        # Tentar encontrar qualquer coluna com "MUN"
        for i, col in enumerate(cabecalho):
            if "MUN" in col.strip().upper():
                col_idx = i
                break

    with open(path_destino, "w", newline="", encoding="utf-8-sig") as out:
        writer = csv.writer(out, delimiter=";")
        writer.writerow([c.strip().replace('"', "") for c in cabecalho])

        for linha in file_handle:
            if isinstance(linha, bytes):
                linha = linha.decode("latin-1", errors="replace")
            n_total += 1

            if col_idx is not None:
                partes = linha.strip().split(delim)
                if col_idx < len(partes):
                    mun = partes[col_idx].strip().upper().replace('"', "")
                    if MUN_NOME in mun or MUN_COD in mun:
                        writer.writerow([p.strip().replace('"', "") for p in partes])
                        n_filtrados += 1
            else:
                # Sem coluna de município, verificar se aparece em qualquer lugar
                if MUN_NOME in linha.upper() or MUN_COD in linha:
                    partes = linha.strip().split(delim)
                    writer.writerow([p.strip().replace('"', "") for p in partes])
                    n_filtrados += 1

            if n_total % 100000 == 0:
                print(f"\r    Processando... {n_total} linhas, {n_filtrados} em Campos", end="", flush=True)

    print()  # nova linha
    return n_filtrados


def filtrar_xlsx_campos(path_origem, path_destino):
    """Filtra arquivo XLSX para Campos dos Goytacazes."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path_origem, read_only=True, data_only=True)
        ws = wb.active

        n_filtrados = 0
        n_total = 0

        with open(path_destino, "w", newline="", encoding="utf-8-sig") as out:
            writer = csv.writer(out, delimiter=";")

            cabecalho = None
            col_idx = None

            for row in ws.iter_rows(values_only=True):
                if cabecalho is None:
                    cabecalho = [str(c) if c else "" for c in row]
                    writer.writerow(cabecalho)
                    for i, col in enumerate(cabecalho):
                        if "MUN" in col.upper():
                            col_idx = i
                            break
                    continue

                n_total += 1
                row_str = [str(c) if c else "" for c in row]

                if col_idx is not None and col_idx < len(row_str):
                    if MUN_NOME in row_str[col_idx].upper() or MUN_COD in row_str[col_idx]:
                        writer.writerow(row_str)
                        n_filtrados += 1
                else:
                    linha_str = " ".join(row_str).upper()
                    if MUN_NOME in linha_str or MUN_COD in linha_str:
                        writer.writerow(row_str)
                        n_filtrados += 1

                if n_total % 50000 == 0:
                    print(f"\r    Processando... {n_total} linhas, {n_filtrados} em Campos", end="", flush=True)

        wb.close()
        print()
        return n_filtrados

    except Exception as e:
        log(f"    ERRO ao filtrar XLSX: {e}", "ERROR")
        return 0


# ============================================================
# PROCESSAMENTO PRINCIPAL DE CADA DATASET
# ============================================================
def processar_dataset(nome_dataset, config):
    """
    Baixa e processa todos os recursos de um dataset.
    Salva CSVs filtrados em banco de dados/<dir>/
    """
    log(f"\n{'='*60}")
    log(f"DATASET: {config['descricao']}")
    log(f"{'='*60}")

    dir_destino = os.path.join(DIR_BASE, config["dir"])
    os.makedirs(dir_destino, exist_ok=True)

    # Obter recursos
    recursos_por_id = obter_recursos_datasets(config["ids"])

    todos_recursos = []
    for ds_id in config["ids"]:
        todos_recursos.extend(recursos_por_id.get(ds_id, []))

    if not todos_recursos:
        log("  NENHUM recurso encontrado para este dataset!", "ERROR")
        return 0

    log(f"  Total de recursos: {len(todos_recursos)}")

    # Filtrar recursos pelo período 2015-2025
    recursos_filtrados = []
    for rec in todos_recursos:
        nome = rec.get("name", "") + " " + rec.get("description", "")
        url = rec.get("url", "")

        # Extrair ano do nome ou URL
        anos_encontrados = re.findall(r"(20\d{2})", nome + url)
        anos_int = [int(a) for a in anos_encontrados]

        # Se tem anos anteriores a 2015 mas também cobre 2015+, incluir
        # Se só tem anos < 2015, pular
        if anos_int:
            anos_validos = [a for a in anos_int if 2015 <= a <= 2025]
            anos_fora = [a for a in anos_int if a < 2015]
            if anos_validos or not anos_fora:
                recursos_filtrados.append(rec)
            elif anos_fora and not anos_validos:
                log(f"    Pulando (fora do periodo): {nome[:80]}")
        else:
            # Sem ano detectado, incluir (pode ser glossário, etc.)
            recursos_filtrados.append(rec)

    log(f"  Recursos no período 2015-2025: {len(recursos_filtrados)}")

    total_registros = 0
    baixados = 0
    erros = 0

    for i, rec in enumerate(recursos_filtrados):
        nome = rec.get("name", f"recurso_{i}")
        url = rec.get("url", "")
        formato = rec.get("format", "").upper()

        if not url:
            log(f"  [{i+1}/{len(recursos_filtrados)}] {nome[:80]} — SEM URL", "WARN")
            erros += 1
            continue

        # Criar nome de arquivo seguro
        nome_arquivo = re.sub(r"[^\w\-\.]", "_", nome)[:100]
        if not nome_arquivo.lower().endswith((".csv", ".zip", ".xlsx", ".xls")):
            nome_arquivo += "." + (formato.lower() if formato else "csv")

        destino_bruto = os.path.join(dir_destino, "_bruto_" + nome_arquivo)
        destino_filtrado = os.path.join(dir_destino, nome_arquivo.replace(".zip", ".csv").replace(".xlsx", ".csv").replace(".xls", ".csv"))

        log(f"  [{i+1}/{len(recursos_filtrados)}] {nome[:80]}")
        log(f"    URL: {url[:120]}")

        # Baixar
        if not os.path.exists(destino_bruto) and not os.path.exists(destino_filtrado):
            log(f"    Baixando...")
            if not baixar_arquivo(url, destino_bruto):
                log(f"    FALHA no download após tentativas", "ERROR")
                erros += 1
                continue
            baixados += 1
        else:
            log(f"    Arquivo já existe, pulando download")

        # Filtrar por Campos
        arquivo_para_filtrar = destino_bruto if os.path.exists(destino_bruto) else destino_filtrado

        if not os.path.exists(destino_filtrado) or os.path.getsize(destino_filtrado) == 0:
            log(f"    Filtrando Campos dos Goytacazes...")
            try:
                if arquivo_para_filtrar.lower().endswith((".xlsx", ".xls")):
                    n = filtrar_xlsx_campos(arquivo_para_filtrar, destino_filtrado)
                else:
                    n = filtrar_csv_campos(arquivo_para_filtrar, destino_filtrado)
                log(f"    {n} registros em Campos")
                total_registros += n
            except Exception as e:
                log(f"    ERRO ao filtrar: {e}", "ERROR")
                erros += 1
        else:
            # Contar linhas do arquivo já filtrado
            try:
                with open(destino_filtrado, "r", encoding="utf-8-sig", errors="replace") as f:
                    n = sum(1 for _ in f) - 1  # menos cabeçalho
                log(f"    {n} registros em Campos (já processado)")
                total_registros += max(0, n)
            except:
                pass

        # SHA-256 para manifesto
        if os.path.exists(destino_filtrado):
            sha = hashlib.sha256()
            with open(destino_filtrado, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha.update(chunk)
            tamanho = os.path.getsize(destino_filtrado)

            manifesto_entries.append({
                "dataset": nome_dataset,
                "arquivo": nome_arquivo.replace(".zip", ".csv").replace(".xlsx", ".csv").replace(".xls", ".csv"),
                "url": url,
                "sha256": sha.hexdigest(),
                "tamanho_bytes": tamanho,
                "registros_campos": n if 'n' in dir() else 0,
                "data_download": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

        # Remover arquivo bruto para economizar espaço
        if os.path.exists(destino_bruto) and os.path.exists(destino_filtrado):
            try:
                os.remove(destino_bruto)
                log(f"    Arquivo bruto removido (filtrado salvo)")
            except:
                pass

    log(f"\n  RESUMO: {baixados} baixados, {erros} erros, {total_registros} registros em Campos")
    return total_registros


# ============================================================
# MAIN
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download completo de dados abertos do INSS")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["todos"], default="todos",
                        help="Dataset a baixar (ou 'todos')")
    args = parser.parse_args()

    log("=" * 70)
    log("DOWNLOAD COMPLETO — PORTAL DE DADOS ABERTOS DO INSS")
    log(f"Município: Campos dos Goytacazes ({MUN_COD})")
    log(f"Período: 2015–2025")
    log(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # Resumo do que está e NÃO está disponível
    log("\n>>> DATASETS DISPONIVEIS COMO DADOS ABERTOS:")
    for key, cfg in DATASETS.items():
        if key != "glossarios":
            log(f"  [OK] {cfg['descricao']}")

    log("\n>>> DATASETS SOLICITADOS MAS NAO DISPONIVEIS COMO DADOS ABERTOS:")
    log("  [FALTA] Reabilitacao Profissional — nao publicado pelo INSS")
    log("  [FALTA] Pericias Medicas — nao publicado pelo INSS")
    log("  [FALTA] NTEP (Nexo Tecnico Epidemiologico Previdenciario) — publicado como portaria, nao como microdados")
    log("  [FALTA] Segurados por CNAE e Municipio — nao publicado como dados abertos")
    log("  [INFO] Cessacao de Beneficios — ja inclusa nos Beneficios Mantidos (status='Cessado')")

    if args.dataset == "todos":
        datasets_processar = [k for k in DATASETS.keys()]
    else:
        datasets_processar = [args.dataset]

    totals = {}

    for key in datasets_processar:
        config = DATASETS[key]
        try:
            n = processar_dataset(key, config)
            totals[key] = n
        except Exception as e:
            log(f"ERRO FATAL no dataset {key}: {e}", "ERROR")
            totals[key] = 0

    # Salvar logs e manifesto
    salvar_log()
    salvar_manifesto()

    log("\n" + "=" * 70)
    log("RESUMO FINAL")
    log("=" * 70)
    for key, n in totals.items():
        log(f"  {DATASETS[key]['descricao']}: {n} registros")
    log(f"  TOTAL: {sum(totals.values())} registros em Campos dos Goytacazes")
    log("\n[OK] Script concluido.")


if __name__ == "__main__":
    main()
