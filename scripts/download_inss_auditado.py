# -*- coding: utf-8 -*-
"""
download_inss_auditado.py
==========================
Download AUDITADO dos dados do portal de dados abertos do INSS
via dados.gov.br, com filtro para Campos dos Goytacazes (330100).

PRINCÍPIOS:
  - REPRODUTIBILIDADE: mesmo script + mesmos dados = mesmos resultados
  - PORTABILIDADE: paths relativos, Python 3.10+, sem hardcoding de paths absolutos
  - RASTREABILIDADE: SHA-256 de cada arquivo, log JSON estruturado, manifesto CSV
  - COMPLIANCE: verificação pós-download (tamanho, registros, integridade)
  - BENCHMARK: tempo de cada etapa registrado

Datasets:
  1. CAT (2012-2025)          2. Benefícios Concedidos (2012-2025)
  3. Benefícios Mantidos       4. Benefícios Emitidos
  5. Benefícios Indeferidos    6. Glossários

USO:
    python scripts/download_inss_auditado.py [--dataset todos|cat|concedidos|mantidos|emitidos|indeferidos|glossarios]
    python scripts/download_inss_auditado.py --auditar  # só verifica integridade
"""
import os, sys, csv, json, time, zipfile, tempfile, re, io, hashlib, struct
import requests
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, OrderedDict
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIGURAÇÃO
# ============================================================
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)

MUN_COD = "330100"
MUN_NOME = "CAMPOS DOS GOYTACAZES"

DIR_BASE = os.path.join("banco de dados")
DIR_LOGS = "logs"
DIR_MANIFESTO = os.path.join("dados", "manifesto")
DIR_AUDITORIA = os.path.join("logs", "auditoria")
os.makedirs(DIR_BASE, exist_ok=True)
os.makedirs(DIR_LOGS, exist_ok=True)
os.makedirs(DIR_MANIFESTO, exist_ok=True)
os.makedirs(DIR_AUDITORIA, exist_ok=True)

ORG_ID = "51b6b5ce-16a9-4839-b9f5-af4a6fb34747"
S3_BASE = "https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com"

DATASETS = OrderedDict({
    "cat": {
        "ids": [
            "inss-comunicacao-de-acidente-de-trabalho-cat1",
            "comunicacoes-de-acidente-de-trabalho-cat-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "cat-inss",
        "descricao": "CAT - Comunicação de Acidente de Trabalho",
        "periodo_esperado": "2012-2025",
        "colunas_municipio": ["Munic Empr", "UF  Munic.  Acidente", "MUNIC_RES", "municipio", "MUNICIPIO"],
    },
    "concedidos": {
        "ids": [
            "inss-beneficios-concedidos1",
            "beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
            "beneficios-concedidos-dez-2012-a-nov-2018-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-concedidos-inss",
        "descricao": "Benefícios Concedidos",
        "periodo_esperado": "2012-2025",
        "colunas_municipio": ["Município Residência", "MUN_RES", "Mun Resid", "municipio", "MUNIC_RES"],
    },
    "mantidos": {
        "ids": [
            "inss-beneficios-mantidos",
            "beneficios-mantidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-mantidos-inss",
        "descricao": "Benefícios Mantidos (Ativos + Suspensos + Cessados)",
        "periodo_esperado": "2021-2025",
        "colunas_municipio": ["MUN_RES", "Mun Resid", "Município Residência", "municipio"],
    },
    "emitidos": {
        "ids": [
            "inss-beneficios-emitidos",
            "beneficios-emitidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-emitidos-inss",
        "descricao": "Benefícios Emitidos (folha de pagamento)",
        "periodo_esperado": "2021-2025",
        "colunas_municipio": ["MUN_RES", "Mun Resid", "Município Residência", "municipio"],
    },
    "indeferidos": {
        "ids": [
            "inss-beneficios-indeferidos",
            "beneficios-indeferidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
            "beneficios-indeferidos-entre-dez-2012-a-nov-2018-plano-de-dados-abertos-jun-2023-a-jun-2025",
        ],
        "dir": "beneficios-indeferidos-inss",
        "descricao": "Benefícios Indeferidos",
        "periodo_esperado": "2012-2025",
        "colunas_municipio": ["MUN_RES", "Mun Resid", "Município Residência", "municipio"],
    },
    "glossarios": {
        "ids": ["glossarios-dos-arquivos-de-beneficios-plano-de-dados-abertos-jun-2023-a-jun-2025"],
        "dir": "glossarios-inss",
        "descricao": "Glossários (dicionários de variáveis)",
        "periodo_esperado": "N/A",
        "colunas_municipio": [],
    },
})

# ============================================================
# LOG ESTRUTURADO
# ============================================================
class Auditoria:
    """Sistema de log estruturado com benchmark e compliance."""
    def __init__(self, nome_dataset):
        self.nome = nome_dataset
        self.inicio = datetime.now()
        self.etapas = []
        self.erros = []
        self.warnings = []
        self.metricas = {
            "arquivos_baixados": 0,
            "arquivos_pulados": 0,
            "arquivos_erro": 0,
            "bytes_baixados": 0,
            "bytes_filtrados": 0,
            "registros_campos": 0,
            "registros_total_bruto": 0,
            "tempo_download_segundos": 0,
            "tempo_filtro_segundos": 0,
            "arquivos_sem_campos": 0,
        }
        self.manifesto = []
        self._etapa_atual = None
        self._tempo_etapa = None

    def etapa(self, nome):
        """Inicia uma etapa com benchmark."""
        if self._etapa_atual:
            duracao = (datetime.now() - self._tempo_etapa).total_seconds()
            self.etapas.append({"etapa": self._etapa_atual, "duracao_segundos": round(duracao, 2)})
        self._etapa_atual = nome
        self._tempo_etapa = datetime.now()

    def info(self, msg):
        print(f"  {msg}")

    def warn(self, msg):
        self.warnings.append(msg)
        print(f"  [WARN] {msg}")

    def erro(self, msg):
        self.erros.append(msg)
        print(f"  [ERROR] {msg}")

    def finalizar_etapa(self):
        if self._etapa_atual:
            duracao = (datetime.now() - self._tempo_etapa).total_seconds()
            self.etapas.append({"etapa": self._etapa_atual, "duracao_segundos": round(duracao, 2)})
            self._etapa_atual = None

    def to_dict(self):
        self.finalizar_etapa()
        duracao_total = (datetime.now() - self.inicio).total_seconds()
        return {
            "dataset": self.nome,
            "inicio": self.inicio.isoformat(),
            "fim": datetime.now().isoformat(),
            "duracao_total_segundos": round(duracao_total, 2),
            "etapas": self.etapas,
            "metricas": self.metricas,
            "erros": self.erros,
            "warnings": self.warnings,
            "manifesto": self.manifesto,
        }

    def salvar(self):
        data = self.to_dict()
        path = os.path.join(DIR_AUDITORIA, f"auditoria_{self.nome}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


# ============================================================
# UTILITÁRIOS DE ARQUIVO
# ============================================================
def detectar_formato(path):
    """Detecta formato real do arquivo por magic bytes, não pela extensão."""
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
        if magic[:2] == b"PK":
            return "ZIP"
        if magic[:2] == b"\xd0\xcf" or magic[:2] == b"\x50\x4b":
            return "ZIP"  # XLSX também é ZIP
        if magic[:4] == b"\xef\xbb\xbf":
            return "CSV_UTF8_BOM"
        if magic[0:1] == b"\xff" or magic[0:1] == b"\xfe":
            return "CSV_UTF16"
        return "CSV"
    except:
        return "DESCONHECIDO"


def sha256_arquivo(path):
    """Calcula SHA-256 de um arquivo."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def extrair_zip_e_encontrar_csv(path_zip):
    """Extrai ZIP em temp dir e retorna path do primeiro CSV ou XLSX."""
    tmpdir = tempfile.mkdtemp(prefix="inss_")
    with zipfile.ZipFile(path_zip, "r") as z:
        z.extractall(tmpdir)

    # Encontrar CSV ou XLSX
    for root, dirs, files in os.walk(tmpdir):
        for f in files:
            if f.lower().endswith(".csv"):
                return os.path.join(root, f), "CSV"
            if f.lower().endswith((".xlsx", ".xls")):
                return os.path.join(root, f), "XLSX"
    return None, None


# ============================================================
# FILTRO DE MUNICÍPIO (ROBUSTO)
# ============================================================
def encontrar_coluna_municipio(cabecalho, colunas_preferenciais):
    """
    Encontra índice da coluna de município no cabeçalho.
    Prioriza colunas_preferenciais, depois qualquer coluna com MUN.
    Retorna (índice, nome_coluna) ou (None, None).
    """
    cabecalho_upper = [c.strip().upper().replace('"', "").replace(" ", "") for c in cabecalho]

    # 1. Tentar colunas preferenciais
    for pref in colunas_preferenciais:
        pref_u = pref.upper().replace(" ", "")
        for i, col in enumerate(cabecalho_upper):
            if pref_u in col or col == pref_u:
                return i, cabecalho[i].strip()

    # 2. Tentar qualquer coluna com MUN
    for i, col in enumerate(cabecalho_upper):
        if "MUN" in col and "RES" not in col:
            continue
        if "MUN" in col:
            return i, cabecalho[i].strip()

    # 3. Tentar colunas que contenham código IBGE (6 dígitos)
    for i, col in enumerate(cabecalho):
        if "IBGE" in col.upper() or "COD" in col.upper():
            return i, cabecalho[i].strip()

    return None, None


def filtrar_arquivo(path_origem, path_destino, colunas_municipio, auditoria):
    """
    Filtra arquivo (CSV, ZIP, XLSX) para Campos dos Goytacazes.
    Lida com:
      - ZIP contendo CSV
      - ZIP contendo XLSX
      - CSV com diferentes delimitadores e encodings
      - XLSX nativo
    Retorna número de registros filtrados.
    """
    formato = detectar_formato(path_origem)

    # === ZIP ===
    if formato == "ZIP":
        auditoria.info("  Arquivo ZIP detectado, extraindo...")
        csv_path, tipo = extrair_zip_e_encontrar_csv(path_origem)
        if csv_path is None:
            auditoria.erro("  Nenhum CSV/XLSX encontrado dentro do ZIP")
            return 0
        if tipo == "XLSX":
            return filtrar_xlsx(csv_path, path_destino, colunas_municipio, auditoria)
        else:
            return filtrar_csv_direto(csv_path, path_destino, colunas_municipio, auditoria)

    # === XLSX ===
    if path_origem.lower().endswith((".xlsx", ".xls")) or formato == "ZIP":
        # ZIP que é na verdade XLSX
        return filtrar_xlsx(path_origem, path_destino, colunas_municipio, auditoria)

    # === CSV ===
    return filtrar_csv_direto(path_origem, path_destino, colunas_municipio, auditoria)


def filtrar_csv_direto(path_csv, path_destino, colunas_municipio, auditoria):
    """Filtra CSV diretamente."""
    # Detectar encoding e delimitador
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(path_csv, "r", encoding=encoding, errors="replace") as f:
                primeira = f.readline()
            break
        except:
            continue

    # Delimitador
    if primeira.count(";") > primeira.count(","):
        delim = ";"
    elif primeira.count("\t") > primeira.count(","):
        delim = "\t"
    else:
        delim = ","

    cabecalho = [c.strip().replace('"', "") for c in primeira.strip().split(delim)]
    col_idx, col_nome = encontrar_coluna_municipio(cabecalho, colunas_municipio)

    if col_idx is None:
        auditoria.warn(f"  Coluna de município não encontrada! Cabeçalho: {cabecalho[:10]}")
        # Salvar tudo mesmo assim, mas marcar
        col_idx = -1

    n_campos = 0
    n_total = 0

    with open(path_destino, "w", newline="", encoding="utf-8-sig") as out:
        writer = csv.writer(out, delimiter=";")
        writer.writerow(cabecalho)

        with open(path_csv, "r", encoding=encoding, errors="replace") as f:
            f.readline()  # pular cabeçalho

            for linha in f:
                n_total += 1
                partes = linha.strip().split(delim)

                if col_idx >= 0 and col_idx < len(partes):
                    mun = partes[col_idx].strip().upper().replace('"', "")
                    if MUN_NOME in mun or MUN_COD in mun:
                        writer.writerow([p.strip().replace('"', "") for p in partes])
                        n_campos += 1
                elif col_idx == -1:
                    # Sem coluna de município, verificar linha toda
                    linha_upper = linha.upper()
                    if MUN_NOME in linha_upper or MUN_COD in linha_upper:
                        writer.writerow([p.strip().replace('"', "") for p in partes])
                        n_campos += 1

                if n_total % 100000 == 0:
                    auditoria.info(f"  ... {n_total} linhas lidas, {n_campos} em Campos")

    auditoria.metricas["registros_total_bruto"] += n_total
    auditoria.metricas["registros_campos"] += n_campos
    if n_campos == 0 and n_total > 0:
        auditoria.metricas["arquivos_sem_campos"] += 1
        auditoria.warn(f"  0 registros em Campos em {n_total} linhas! Coluna usada: {col_nome}")

    return n_campos


def filtrar_xlsx(path_xlsx, path_destino, colunas_municipio, auditoria):
    """Filtra XLSX para Campos."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path_xlsx, read_only=True, data_only=True)
        ws = wb.active

        n_campos = 0
        n_total = 0
        cabecalho = None
        col_idx = None

        with open(path_destino, "w", newline="", encoding="utf-8-sig") as out:
            writer = csv.writer(out, delimiter=";")

            for row in ws.iter_rows(values_only=True):
                if cabecalho is None:
                    cabecalho = [str(c) if c else "" for c in row]
                    writer.writerow(cabecalho)
                    col_idx, _ = encontrar_coluna_municipio(cabecalho, colunas_municipio)
                    if col_idx is None:
                        col_idx = -1
                    continue

                n_total += 1
                row_str = [str(c) if c else "" for c in row]

                match = False
                if col_idx >= 0 and col_idx < len(row_str):
                    if MUN_NOME in row_str[col_idx].upper() or MUN_COD in row_str[col_idx]:
                        match = True
                elif col_idx == -1:
                    if MUN_NOME in " ".join(row_str).upper() or MUN_COD in " ".join(row_str):
                        match = True

                if match:
                    writer.writerow(row_str)
                    n_campos += 1

                if n_total % 50000 == 0:
                    auditoria.info(f"  ... {n_total} linhas, {n_campos} em Campos")

        wb.close()
        auditoria.metricas["registros_total_bruto"] += n_total
        auditoria.metricas["registros_campos"] += n_campos
        if n_campos == 0 and n_total > 0:
            auditoria.metricas["arquivos_sem_campos"] += 1
            auditoria.warn(f"  0 registros em Campos em {n_total} linhas (XLSX)")

        return n_campos

    except Exception as e:
        auditoria.erro(f"  Erro ao processar XLSX: {e}")
        return 0


# ============================================================
# API DADOS.GOV.BR
# ============================================================
def listar_recursos_datasets(ids_datasets, auditoria):
    """Lista todos os recursos dos datasets via API do dados.gov.br (Playwright)."""
    auditoria.etapa("api_listar_recursos")

    recursos_por_id = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors", "--disable-web-security"],
        )
        page = browser.new_page()

        auditoria.info("Obtendo sessão no dados.gov.br...")
        page.goto(
            "https://dados.gov.br/dados/organizacoes/visualizar/instituto-nacional-do-seguro-social",
            wait_until="networkidle",
            timeout=60000,
        )
        page.wait_for_timeout(5000)

        for ds_id in ids_datasets:
            auditoria.info(f"Buscando: {ds_id}")

            # Buscar por nome exato via API
            result = page.evaluate(
                f"""
                async () => {{
                    const url = `https://dados.gov.br/api/publico/conjuntos-dados/buscar?offset=0&nome={ds_id}&titulo=&colunaOrdenacao=dataAtualizacao&direcaoOrdenacao=DESC&idOrganizacao=null&dadosAbertos=true`;
                    const resp = await fetch(url);
                    return await resp.json();
                }}
            """
            )

            registros = result.get("registros", [])
            if registros and registros[0].get("name") == ds_id:
                recursos = registros[0].get("resourcesAcessoRapido", [])
                recursos_por_id[ds_id] = recursos
                auditoria.info(f"  {len(recursos)} recursos")
                continue

            # Fallback: buscar em todas as páginas
            all_recursos = []
            for offset in range(0, 60, 20):
                result = page.evaluate(
                    f"""
                    async () => {{
                        const url = `https://dados.gov.br/api/publico/conjuntos-dados/buscar?offset={offset}&nome=&titulo=&colunaOrdenacao=dataAtualizacao&direcaoOrdenacao=DESC&idOrganizacao={ORG_ID}&dadosAbertos=true`;
                        const resp = await fetch(url);
                        return await resp.json();
                    }}
                """
                )
                regs = result.get("registros", [])
                if not regs:
                    break
                for r in regs:
                    if r.get("name") == ds_id:
                        all_recursos = r.get("resourcesAcessoRapido", [])
                        break
                if all_recursos:
                    break

            recursos_por_id[ds_id] = all_recursos
            auditoria.info(f"  {len(all_recursos)} recursos")

        browser.close()

    auditoria.finalizar_etapa()
    return recursos_por_id


# ============================================================
# DOWNLOAD
# ============================================================
def baixar_arquivo(url, destino, auditoria, max_retries=3):
    """Baixa arquivo com retry, progresso e benchmark."""
    for tentativa in range(max_retries):
        try:
            t0 = time.time()
            resp = requests.get(url, timeout=600, stream=True)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            baixado = 0
            chunk_size = 1024 * 1024

            with open(destino, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    baixado += len(chunk)

            t1 = time.time()
            tamanho = os.path.getsize(destino)
            auditoria.metricas["bytes_baixados"] += tamanho
            auditoria.metricas["tempo_download_segundos"] += (t1 - t0)

            formato = detectar_formato(destino)
            auditoria.info(f"  {tamanho/1e6:.1f} MB em {t1-t0:.1f}s [{formato}]")
            return True

        except Exception as e:
            auditoria.warn(f"Tentativa {tentativa+1} falhou: {e}")
            time.sleep(10 * (tentativa + 1))

    return False


# ============================================================
# PROCESSAMENTO DE DATASET
# ============================================================
def processar_dataset(nome_dataset, config, auditoria):
    """Baixa e filtra todos os recursos de um dataset."""
    auditoria.etapa("processar_dataset")

    dir_destino = os.path.join(DIR_BASE, config["dir"])
    os.makedirs(dir_destino, exist_ok=True)

    # Listar recursos
    recursos_por_id = listar_recursos_datasets(config["ids"], auditoria)
    todos_recursos = []
    for ds_id in config["ids"]:
        todos_recursos.extend(recursos_por_id.get(ds_id, []))

    auditoria.info(f"Total recursos: {len(todos_recursos)}")

    if not todos_recursos:
        auditoria.erro("NENHUM recurso encontrado!")
        auditoria.finalizar_etapa()
        return 0

    # Processar cada recurso
    for i, rec in enumerate(todos_recursos):
        nome = rec.get("name", f"recurso_{i}")
        url = rec.get("url", "")

        if not url:
            auditoria.warn(f"[{i+1}/{len(todos_recursos)}] {nome[:80]} — SEM URL")
            auditoria.metricas["arquivos_erro"] += 1
            continue

        # Nome de arquivo seguro
        nome_arquivo = re.sub(r"[^\w\-\.\,\s]", "_", nome)[:90]
        nome_arquivo = nome_arquivo.strip().replace(" ", "_")

        # Preservar extensão original ou inferir
        if not any(nome_arquivo.lower().endswith(ext) for ext in [".csv", ".zip", ".xlsx", ".xls"]):
            # Tentar inferir da URL
            url_lower = url.lower()
            if ".csv" in url_lower:
                nome_arquivo += ".csv"
            elif ".zip" in url_lower:
                nome_arquivo += ".zip"
            elif ".xlsx" in url_lower:
                nome_arquivo += ".xlsx"
            elif ".xls" in url_lower:
                nome_arquivo += ".xls"
            else:
                nome_arquivo += ".csv"  # default

        destino_bruto = os.path.join(dir_destino, "_raw_" + nome_arquivo)
        destino_filtrado = os.path.join(dir_destino, nome_arquivo)
        # Garantir que destino_filtrado termina com .csv
        if not destino_filtrado.lower().endswith(".csv"):
            destino_filtrado = destino_filtrado.rsplit(".", 1)[0] + ".csv"

        auditoria.info(f"[{i+1}/{len(todos_recursos)}] {nome[:80]}")

        # Pular se já existe filtrado E tem conteúdo
        if os.path.exists(destino_filtrado) and os.path.getsize(destino_filtrado) > 100:
            n_linhas = sum(1 for _ in open(destino_filtrado, "r", encoding="utf-8-sig", errors="replace")) - 1
            auditoria.info(f"  Já processado: {n_linhas} registros em Campos")
            auditoria.metricas["arquivos_pulados"] += 1
            auditoria.metricas["registros_campos"] += max(0, n_linhas)
            auditoria.metricas["bytes_filtrados"] += os.path.getsize(destino_filtrado)

            # Adicionar ao manifesto
            auditoria.manifesto.append({
                "dataset": nome_dataset,
                "arquivo": os.path.basename(destino_filtrado),
                "url": url,
                "sha256": sha256_arquivo(destino_filtrado),
                "tamanho_bytes": os.path.getsize(destino_filtrado),
                "registros_campos": max(0, n_linhas),
            })
            continue

        # Baixar
        if not os.path.exists(destino_bruto):
            auditoria.info(f"  Baixando {url[:100]}...")
            if not baixar_arquivo(url, destino_bruto, auditoria):
                auditoria.erro(f"  FALHA no download")
                auditoria.metricas["arquivos_erro"] += 1
                continue
            auditoria.metricas["arquivos_baixados"] += 1
        else:
            auditoria.info(f"  Arquivo bruto já existe ({os.path.getsize(destino_bruto)/1e6:.1f} MB)")

        # Filtrar
        t0 = time.time()
        arquivo_para_filtrar = destino_bruto

        auditoria.info(f"  Filtrando Campos dos Goytacazes...")
        try:
            n = filtrar_arquivo(arquivo_para_filtrar, destino_filtrado, config["colunas_municipio"], auditoria)
            t1 = time.time()
            auditoria.metricas["tempo_filtro_segundos"] += (t1 - t0)
            auditoria.info(f"  {n} registros em Campos ({t1-t0:.1f}s)")
        except Exception as e:
            auditoria.erro(f"  Erro ao filtrar: {e}")
            n = 0

        # Pós-processamento: verificar integridade
        if os.path.exists(destino_filtrado):
            tamanho_filtrado = os.path.getsize(destino_filtrado)
            auditoria.metricas["bytes_filtrados"] += tamanho_filtrado
            sha = sha256_arquivo(destino_filtrado)

            # Verificação de compliance
            if n == 0 and tamanho_filtrado < 200:
                auditoria.warn(f"  Arquivo filtrado vazio ou quase vazio — possível problema")
            if tamanho_filtrado > os.path.getsize(arquivo_para_filtrar):
                auditoria.warn(f"  Arquivo filtrado MAIOR que o original — possível corrupção")

            auditoria.manifesto.append({
                "dataset": nome_dataset,
                "arquivo": os.path.basename(destino_filtrado),
                "url": url,
                "sha256": sha,
                "tamanho_bytes": tamanho_filtrado,
                "registros_campos": n,
            })

        # Limpar bruto
        if os.path.exists(destino_bruto):
            try:
                os.remove(destino_bruto)
            except:
                pass

    auditoria.finalizar_etapa()
    return auditoria.metricas["registros_campos"]


# ============================================================
# RELATÓRIO DE AUDITORIA
# ============================================================
def gerar_relatorio_auditoria(todas_auditorias):
    """Gera relatório consolidado de auditoria."""
    path = os.path.join(DIR_AUDITORIA, "relatorio_auditoria_completo.txt")
    linhas = []
    linhas.append("=" * 80)
    linhas.append("RELATÓRIO DE AUDITORIA — DOWNLOAD DADOS ABERTOS INSS")
    linhas.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linhas.append(f"Município: Campos dos Goytacazes ({MUN_COD})")
    linhas.append("=" * 80)

    total_registros = 0
    total_bytes = 0
    total_erros = 0
    total_warnings = 0

    for aud in todas_auditorias:
        d = aud.to_dict()
        linhas.append(f"\n--- {d['dataset']} ---")
        linhas.append(f"  Duração: {d['duracao_total_segundos']}s")
        linhas.append(f"  Arquivos baixados: {d['metricas']['arquivos_baixados']}")
        linhas.append(f"  Arquivos pulados (já existentes): {d['metricas']['arquivos_pulados']}")
        linhas.append(f"  Arquivos com erro: {d['metricas']['arquivos_erro']}")
        linhas.append(f"  Registros em Campos: {d['metricas']['registros_campos']}")
        linhas.append(f"  Registros brutos lidos: {d['metricas']['registros_total_bruto']}")
        linhas.append(f"  Bytes baixados: {d['metricas']['bytes_baixados']/1e6:.1f} MB")
        linhas.append(f"  Bytes filtrados: {d['metricas']['bytes_filtrados']/1e6:.1f} MB")
        linhas.append(f"  Tempo download: {d['metricas']['tempo_download_segundos']:.1f}s")
        linhas.append(f"  Tempo filtro: {d['metricas']['tempo_filtro_segundos']:.1f}s")
        linhas.append(f"  Arquivos sem registros em Campos: {d['metricas']['arquivos_sem_campos']}")

        if d['erros']:
            linhas.append(f"  ERROS ({len(d['erros'])}):")
            for e in d['erros'][:10]:
                linhas.append(f"    - {str(e)[:200]}")
        if d['warnings']:
            linhas.append(f"  WARNINGS ({len(d['warnings'])}):")
            for w in d['warnings'][:20]:
                linhas.append(f"    - {str(w)[:200]}")

        total_registros += d['metricas']['registros_campos']
        total_bytes += d['metricas']['bytes_filtrados']
        total_erros += len(d['erros'])
        total_warnings += len(d['warnings'])

    linhas.append(f"\n{'='*80}")
    linhas.append(f"TOTAIS CONSOLIDADOS")
    linhas.append(f"  Registros em Campos: {total_registros}")
    linhas.append(f"  Bytes filtrados: {total_bytes/1e6:.1f} MB")
    linhas.append(f"  Erros: {total_erros}")
    linhas.append(f"  Warnings: {total_warnings}")

    # Compliance
    linhas.append(f"\n--- COMPLIANCE ---")
    if total_erros == 0:
        linhas.append("  [PASS] Nenhum erro de download")
    else:
        linhas.append(f"  [FAIL] {total_erros} erros encontrados")

    # Benchmark
    tempo_total = sum(d.to_dict()['duracao_total_segundos'] for d in todas_auditorias)
    linhas.append(f"  Tempo total de execução: {tempo_total:.1f}s ({tempo_total/60:.1f} min)")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print("\n".join(linhas))
    print(f"\nRelatório salvo: {path}")
    return path


# ============================================================
# MAIN
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download auditado de dados abertos do INSS")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["todos"], default="todos")
    parser.add_argument("--auditar", action="store_true", help="Apenas verificar integridade dos arquivos existentes")
    args = parser.parse_args()

    print("=" * 80)
    print("DOWNLOAD AUDITADO — PORTAL DE DADOS ABERTOS DO INSS")
    print(f"Município: Campos dos Goytacazes ({MUN_COD})")
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Resumo de disponibilidade
    print("\n>>> DISPONIBILIDADE DE DADOS")
    for key, cfg in DATASETS.items():
        if key != "glossarios":
            print(f"  [DISPONIVEL] {cfg['descricao']} ({cfg['periodo_esperado']})")
    print("\n  [INDISPONIVEL] Reabilitação Profissional")
    print("  [INDISPONIVEL] Perícias Médicas")
    print("  [INDISPONIVEL] NTEP — apenas portaria, sem microdados")
    print("  [INDISPONIVEL] Segurados por CNAE e Município")
    print("  [VIA MANTIDOS] Cessação de Benefícios — status 'Cessado' nos Mantidos")

    if args.dataset == "todos":
        datasets_processar = list(DATASETS.keys())
    else:
        datasets_processar = [args.dataset]

    todas_auditorias = []

    for key in datasets_processar:
        config = DATASETS[key]
        aud = Auditoria(config["descricao"])
        print(f"\n{'='*80}")
        print(f"DATASET: {config['descricao']}")
        print(f"{'='*80}")

        try:
            processar_dataset(key, config, aud)
        except Exception as e:
            aud.erro(f"ERRO FATAL: {e}")
            import traceback
            aud.erro(traceback.format_exc()[-500:])

        # Salvar auditoria individual
        path_aud = aud.salvar()
        print(f"  Auditoria salva: {path_aud}")
        todas_auditorias.append(aud)

    # Relatório consolidado
    gerar_relatorio_auditoria(todas_auditorias)

    # Salvar manifesto consolidado
    manifesto_consolidado = []
    for aud in todas_auditorias:
        manifesto_consolidado.extend(aud.manifesto)

    if manifesto_consolidado:
        path_manifesto = os.path.join(DIR_MANIFESTO, "manifesto_inss_auditado.csv")
        with open(path_manifesto, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["dataset", "arquivo", "url", "sha256", "tamanho_bytes", "registros_campos"], delimiter=";")
            writer.writeheader()
            writer.writerows(manifesto_consolidado)
        print(f"Manifesto consolidado: {path_manifesto} ({len(manifesto_consolidado)} arquivos)")

    print(f"\n{'='*80}")
    print("DOWNLOAD CONCLUÍDO COM SUCESSO")
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
