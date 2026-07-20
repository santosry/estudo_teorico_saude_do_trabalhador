################################################################################
## processar_sinan.R - Ler DBC do SINAN e filtrar Campos dos Goytacazes       ##
## Usa read.dbc (oficial DATASUS) para descomprimir BLAST                     ##
################################################################################

# Instalar pacotes se necessario
if (!require("read.dbc")) {
  install.packages("read.dbc", repos = "https://cran.r-project.org")
  library(read.dbc)
}

MUN_COD <- "330100"
DIR_SINAN <- "dados/brutos/sinan"
DIR_PROC <- "dados/processados"
DIR_SAIDAS <- "saidas/tabelas"

dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(DIR_SAIDAS, showWarnings = FALSE, recursive = TRUE)

# Listar arquivos
dbcs <- list.files(DIR_SINAN, pattern = "\\.dbc$", ignore.case = TRUE, full.names = TRUE)
cat(sprintf("\n%d arquivos .dbc encontrados\n", length(dbcs)))

# Processar cada arquivo
todos <- list()
estatisticas <- list()

for (path in dbcs) {
  nome <- basename(path)
  prefixo <- toupper(substr(nome, 1, 4))
  
  # Extrair ano
  ano_suf <- as.integer(substr(nome, 7, 8))
  ano <- if (ano_suf < 60) 2000 + ano_suf else 1900 + ano_suf
  
  if (ano < 2018 || ano > 2025) next
  
  cat(sprintf("\n  [%s] %d (%s)", prefixo, ano, nome))
  
  # Tentar ler com read.dbc
  df <- tryCatch({
    read.dbc(path)
  }, error = function(e) {
    cat(sprintf(" ERRO: %s", e$message))
    return(NULL)
  })
  
  if (is.null(df) || nrow(df) == 0) {
    cat(" vazio")
    next
  }
  
  # Encontrar coluna de municipio
  col_mun <- grep("ID_MUNICIP|MUNICIPIO|MUNICIP", names(df), value = TRUE, ignore.case = TRUE)
  if (length(col_mun) == 0) {
    col_mun <- grep("MUN", names(df), value = TRUE, ignore.case = TRUE)
  }
  
  if (length(col_mun) == 0) {
    cat(sprintf(" sem coluna municipio. Cols: %s", paste(names(df)[1:5], collapse=", ")))
    next
  }
  
  col_mun <- col_mun[1]
  
  # Filtrar Campos
  df$mun_str <- as.character(df[[col_mun]])
  campos <- df[df$mun_str == MUN_COD, ]
  campos$mun_str <- NULL
  
  n_campos <- nrow(campos)
  n_total <- nrow(df)
  
  cat(sprintf(" BR=%d Campos=%d", n_total, n_campos))
  
  if (n_campos > 0) {
    # Adicionar metadados
    campos$`_agravo_cod` <- prefixo
    campos$`_ano` <- ano
    campos$`_arquivo` <- nome
    
    todos[[length(todos) + 1]] <- campos
    
    # Estatisticas
    key <- paste0(prefixo, "_", ano)
    estatisticas[[key]] <- c(prefixo = prefixo, ano = ano, n = n_campos)
  }
}

# Consolidar
if (length(todos) > 0) {
  cat(sprintf("\n\nConsolidando %d data.frames...\n", length(todos)))
  
  # Juntar todos (preenchendo colunas faltantes com NA)
  todas_cols <- unique(unlist(lapply(todos, names)))
  
  todos_pad <- lapply(todos, function(df) {
    faltantes <- setdiff(todas_cols, names(df))
    for (col in faltantes) {
      df[[col]] <- NA
    }
    df[, todas_cols]
  })
  
  final <- do.call(rbind, todos_pad)
  
  # Salvar
  path_csv <- file.path(DIR_PROC, "sinan_campos_2018_2025.csv")
  write.csv2(final, path_csv, row.names = FALSE, fileEncoding = "UTF-8")
  
  cat(sprintf("\nCSV salvo: %s (%d registros, %d colunas)\n", 
              path_csv, nrow(final), ncol(final)))
  
  # Resumo
  cat("\n===== RESUMO =====\n")
  est_df <- do.call(rbind, lapply(estatisticas, as.data.frame))
  print(est_df)
  
} else {
  cat("\n\nNENHUM registro de Campos encontrado nos arquivos SINAN.\n")
  cat("Possiveis causas:\n")
  cat("  1. Campos nao teve notificacoes desses agravos no periodo\n")
  cat("  2. Subnotificacao (problema nacional conhecido)\n")
  cat("  3. Os agravos sao raros em nivel municipal\n")
}

cat("\nOK Script concluido.\n")
