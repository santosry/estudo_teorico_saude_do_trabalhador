################################################################################
## Baixar microdados RAIS do FTP do MTE e converter para CSV                  ##
## Baseado no script original de Guilherme Cemin (http://cemin.wikidot.com)   ##
##                                                                           ##
## IMPORTANTE: Execute com R.exe (NAO com Rscript.exe):                      ##
##   "C:\Program Files\R\R-4.6.0\bin\R.exe" --no-init-file --no-save -f      ##
##      "C:\Users\oorie\OneDrive\Documentos\TRABALHOS\SAÚDE DO TRABALHADOR"  ##
##      "\scripts\download_rais_csv.R"                                       ##
################################################################################

# ============================================================================
# CONFIGURACOES - Edite conforme necessario
# ============================================================================

# Pasta onde os arquivos CSV serao salvos
PASTA_DESTINO <- "C:/Users/oorie/OneDrive/Documentos/TRABALHOS/SAUDE DO TRABALHADOR/banco de dados"

# Anos para baixar (1985 a 2025 disponiveis no FTP)
ANOS <- 2018:2025

# Regioes para baixar
# Opcoes: "MG_ES_RJ", "SP", "NORDESTE", "NORTE", "SUL", "CENTRO_OESTE", "NI"
REGIOES <- c("MG_ES_RJ")

# Tipo de arquivo: "VINC" (vinculos) ou "ESTAB" (estabelecimentos)
TIPO <- "VINC"

# Formato de saida: "csv" ou "csv.gz" (comprimido, recomendado)
FORMATO_SAIDA <- "csv"

# Pasta temporaria para extracao (precisa de espaco: cada arquivo ~7GB descompactado)
PASTA_TEMP <- "C:/Users/oorie/tmp_rais"

# Caminho para o 7za.exe (sera baixado automaticamente se nao existir)
SETEZA <- "C:/Users/oorie/7za.exe"

# Se TRUE, usa arquivos .7z ja baixados da pasta abaixo
# Se FALSE, baixa tudo novamente do FTP
USAR_ARQUIVOS_LOCAIS <- TRUE
PASTA_7Z_LOCAIS <- "C:/Users/oorie/OneDrive/Documentos/TRABALHOS/SAUDE DO TRABALHADOR/rais"

# Se TRUE, mantem o .txt extraido na pasta temp (util se for processar novamente)
MANTER_TXT <- FALSE

# ============================================================================
# INICIO DO SCRIPT
# ============================================================================

cat("\n========================================\n")
cat("  DOWNLOAD RAIS -> CSV\n")
cat("========================================\n")
cat("Inicio:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n\n")

# Carregar pacotes necessarios
if (!require("data.table")) {
  install.packages("data.table")
  library(data.table)
}
cat("data.table versao", as.character(packageVersion("data.table")), "carregado.\n")

# Criar pastas necessarias
dir.create(PASTA_DESTINO, showWarnings = FALSE, recursive = TRUE)
dir.create(PASTA_TEMP, showWarnings = FALSE, recursive = TRUE)

# Baixar 7za.exe se nao existir
if (!file.exists(SETEZA)) {
  cat("Baixando 7za.exe (descompactador)...\n")
  download.file(
    "http://cemin.wikidot.com/local--files/raisrm/7za.exe",
    SETEZA, mode = "wb"
  )
  cat("7za.exe baixado com sucesso.\n")
} else {
  cat("7za.exe encontrado em:", SETEZA, "\n")
}

# Construir lista de arquivos a processar
cat("\n--- Montando lista de arquivos ---\n")
arquivos_info <- list()

for (ano in ANOS) {
  for (regiao in REGIOES) {
    nome_ftp <- sprintf("RAIS_%s_PUB_%s.7z", TIPO, regiao)
    nome_local <- sprintf("RAIS_%d_%s.7z", ano, regiao)
    caminho_local <- file.path(PASTA_7Z_LOCAIS, nome_local)
    nome_saida <- sprintf("RAIS_%s_%d_%s", TIPO, ano, regiao)

    info <- list(
      ano = ano,
      regiao = regiao,
      nome_saida = nome_saida,
      arquivo_saida = file.path(PASTA_DESTINO, paste0(nome_saida, ".", FORMATO_SAIDA))
    )

    if (USAR_ARQUIVOS_LOCAIS && file.exists(caminho_local)) {
      info$usar_local <- TRUE
      info$caminho_7z <- caminho_local
      cat(sprintf("  [LOCAL] %d - %s\n", ano, regiao))
    } else {
      info$usar_local <- FALSE
      info$url_ftp <- sprintf(
        "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/%d/%s",
        ano, nome_ftp
      )
      info$caminho_7z <- file.path(PASTA_TEMP, paste0(nome_saida, ".7z"))
      cat(sprintf("  [FTP] %d - %s\n", ano, regiao))
    }

    arquivos_info[[length(arquivos_info) + 1]] <- info
  }
}

cat(sprintf("\nTotal: %d arquivos para processar.\n\n", length(arquivos_info)))

# ============================================================================
# Funcao: Download com retry
# ============================================================================
download_com_retry <- function(url, destfile, max_tentativas = 10) {
  for (tentativa in 1:max_tentativas) {
    resultado <- tryCatch({
      download.file(url, destfile, mode = "wb")
      TRUE
    }, error = function(e) {
      cat(sprintf("  Tentativa %d/%d falhou: %s\n", tentativa, max_tentativas, e$message))
      FALSE
    })

    if (resultado) return(TRUE)

    if (tentativa < max_tentativas) {
      cat(sprintf("  Aguardando 60s para nova tentativa...\n"))
      Sys.sleep(60)
    }
  }
  return(FALSE)
}

# ============================================================================
# Funcao: Processar um arquivo
# ============================================================================
processar_arquivo <- function(info) {
  t_total_inicio <- Sys.time()

  cat(sprintf("\n========================================\n"))
  cat(sprintf("Processando: RAIS %d - %s\n", info$ano, info$regiao))
  cat(sprintf("Saida: %s\n", basename(info$arquivo_saida)))
  cat(sprintf("========================================\n"))

  # Pular se CSV ja existe
  if (file.exists(info$arquivo_saida)) {
    tamanho <- file.info(info$arquivo_saida)$size / (1024^3)
    cat(sprintf("  Arquivo CSV ja existe (%.2f GB). Pulando...\n", tamanho))
    return(TRUE)
  }

  # ===== ETAPA 1: Obter o arquivo .7z =====
  if (info$usar_local) {
    cat(sprintf("[1/4] Usando .7z local: %s\n", basename(info$caminho_7z)))
    arquivo_7z <- info$caminho_7z
  } else {
    cat(sprintf("[1/4] Baixando do FTP: %s\n", info$url_ftp))
    sucesso <- download_com_retry(info$url_ftp, info$caminho_7z)
    if (!sucesso) {
      cat(sprintf("  ERRO: Falha ao baixar. Pulando...\n"))
      return(FALSE)
    }
    tamanho_mb <- file.info(info$caminho_7z)$size / (1024^2)
    cat(sprintf("  Download concluido (%.0f MB).\n", tamanho_mb))
    arquivo_7z <- info$caminho_7z
  }

  # ===== ETAPA 2: Extrair .txt =====
  pasta_extracao <- file.path(PASTA_TEMP, info$nome_saida)
  dir.create(pasta_extracao, showWarnings = FALSE, recursive = TRUE)

  # Verificar se o txt ja existe de uma execucao anterior
  txts_existentes <- list.files(pasta_extracao, pattern = "\\.txt$", full.names = TRUE)
  if (length(txts_existentes) > 0) {
    txt_extraido <- txts_existentes[1]
  } else {
    txt_extraido <- file.path(pasta_extracao,
      paste0("RAIS_", TIPO, "_PUB_", info$regiao, ".txt"))
  }

  if (!file.exists(txt_extraido) || file.info(txt_extraido)$size == 0) {
    cat(sprintf("[2/4] Extraindo .7z com 7za...\n"))
    comando <- sprintf('"%s" e "%s" -o"%s" -y', SETEZA, arquivo_7z, pasta_extracao)
    resultado <- system(comando, intern = TRUE, ignore.stderr = TRUE)
    cat(sprintf("  7za saida: %s\n", paste(tail(resultado, 3), collapse = " | ")))

    # Encontrar o arquivo .txt extraido
    txts_encontrados <- list.files(pasta_extracao, pattern = "\\.txt$", full.names = TRUE)
    if (length(txts_encontrados) == 0) {
      txts_encontrados <- list.files(pasta_extracao, pattern = "\\.txt$", full.names = TRUE, recursive = TRUE)
    }
    if (length(txts_encontrados) == 0) {
      cat("  ERRO: Nenhum arquivo .txt encontrado apos extracao. Pulando...\n")
      return(FALSE)
    }
    txt_extraido <- txts_encontrados[1]
  } else {
    cat(sprintf("[2/4] Usando .txt ja extraido: %s\n", basename(txt_extraido)))
  }

  tamanho_gb <- file.info(txt_extraido)$size / (1024^3)
  cat(sprintf("  Arquivo txt: %.2f GB\n", tamanho_gb))

  # ===== ETAPA 3: Ler e converter para CSV =====
  cat(sprintf("[3/4] Lendo .txt com fread...\n"))
  t_leitura <- Sys.time()

  df <- tryCatch({
    fread(
      txt_extraido,
      sep = ";",
      dec = ",",
      header = TRUE,
      encoding = "Latin-1",
      showProgress = TRUE,
      nThread = 4
    )
  }, error = function(e) {
    cat(sprintf("  ERRO na leitura: %s\n", e$message))
    NULL
  })

  if (is.null(df)) {
    cat("  Falha na leitura. Pulando...\n")
    return(FALSE)
  }

  t_pos_leitura <- Sys.time()
  duracao_leitura <- difftime(t_pos_leitura, t_leitura, units = "mins")
  cat(sprintf("  Leitura concluida em %.1f min. %d linhas, %d colunas.\n",
              duracao_leitura, nrow(df), ncol(df)))

  # Salvar como CSV
  cat(sprintf("[4/4] Salvando como %s...\n", FORMATO_SAIDA))
  fwrite(
    df,
    info$arquivo_saida,
    sep = ",",
    dec = ",",
    bom = TRUE
  )

  t_escrita <- Sys.time()
  duracao_escrita <- difftime(t_escrita, t_pos_leitura, units = "mins")
  tamanho_csv <- file.info(info$arquivo_saida)$size / (1024^3)

  cat(sprintf("  CSV salvo: %.2f GB (%.1f min)\n", tamanho_csv, duracao_escrita))
  cat(sprintf("  Arquivo: %s\n", info$arquivo_saida))

  # Liberar memoria
  rm(df)
  gc()

  # Limpar arquivos temporarios
  if (!MANTER_TXT) {
    cat("  Limpando .txt extraido...\n")
    if (file.exists(txt_extraido)) {
      unlink(txt_extraido)
      unlink(pasta_extracao, recursive = TRUE)
    }
  }
  if (!info$usar_local && file.exists(info$caminho_7z)) {
    cat("  Removendo .7z temporario...\n")
    unlink(info$caminho_7z)
  }

  t_total_fim <- Sys.time()
  duracao_total <- difftime(t_total_fim, t_total_inicio, units = "mins")
  cat(sprintf("CONCLUIDO! Tempo total: %.1f minutos.\n", duracao_total))
  return(TRUE)
}

# ============================================================================
# PROCESSAR TODOS OS ARQUIVOS
# ============================================================================
sucessos <- 0
falhas <- 0

for (i in seq_along(arquivos_info)) {
  info <- arquivos_info[[i]]

  resultado <- processar_arquivo(info)
  if (resultado) {
    sucessos <- sucessos + 1
  } else {
    falhas <- falhas + 1
  }
  cat(sprintf("\nProgresso: %d/%d concluidos (%d sucessos, %d falhas)\n",
              i, length(arquivos_info), sucessos, falhas))
}

# ============================================================================
# RESUMO FINAL
# ============================================================================
cat("\n\n========================================\n")
cat("  PROCESSAMENTO CONCLUIDO!\n")
cat("========================================\n")
cat(sprintf("Sucessos: %d | Falhas: %d\n", sucessos, falhas))
cat(sprintf("Arquivos CSV salvos em:\n  %s\n", PASTA_DESTINO))

# Listar arquivos gerados
arquivos_gerados <- list.files(PASTA_DESTINO, pattern = "\\.csv$", full.names = FALSE)
if (length(arquivos_gerados) > 0) {
  cat(sprintf("\n%d arquivos CSV gerados:\n", length(arquivos_gerados)))
  for (f in sort(arquivos_gerados)) {
    tamanho <- file.info(file.path(PASTA_DESTINO, f))$size / (1024^3)
    cat(sprintf("  %s (%.2f GB)\n", f, tamanho))
  }
}

cat(sprintf("\nFim: %s\n", format(Sys.time(), "%Y-%m-%d %H:%M:%S")))
cat("\nPara carregar no R, use:\n")
cat('  library(data.table)\n')
cat('  df <- fread("arquivo.csv", sep=",", dec=",")\n')
