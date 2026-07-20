################################################################################
## sinan_trabalho_campos.R                                                    ##
## SINAN - Agravos RELACIONADOS AO TRABALHO - Campos dos Goytacazes (330100)  ##
## Fonte: DATASUS FTP (FINAIS 2018-2022 + PRELIM 2023-2025)                  ##
## Metodo: read.dbc + filtro por CID/trabalho especifico de cada agravo       ##
################################################################################
library(read.dbc)

MUN_COD <- "330100"
DIR_SINAN <- "dados/brutos/sinan"
DIR_PROC <- "dados/processados"
DIR_SAIDAS <- "saidas/tabelas"
dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(DIR_SAIDAS, showWarnings = FALSE, recursive = TRUE)

# Agravos de interesse (RELACIONADOS AO TRABALHO)
AGRAVOS_TRAB <- c(
  "ACGR",  # Acidente de Trabalho Grave - TODOS sao de trabalho
  "ACBI",  # Acidente Trab c/ Exposicao Material Biologico - TODOS sao de trabalho
  "ANIM",  # Acidente Animais Peconhentos - filtrar por SIT_TRAB / TP_ACIDENT
  "DERM",  # Dermatose Relacionada ao Trabalho - TODOS sao de trabalho (agravo especifico)
  "CANC",  # Cancer Relacionado ao Trabalho - TODOS sao de trabalho (agravo especifico)
  "LERD",  # LER/DORT - TODOS sao de trabalho (agravo especifico)
  "PNEU",  # Pneumoconiose Relacionada ao Trabalho - TODOS sao de trabalho
  "PAIR",  # PAIR Relacionado ao Trabalho - TODOS sao de trabalho
  "MENT"   # Transtorno Mental Relacionado ao Trabalho - TODOS sao de trabalho
)

cat("========================================\n")
cat("SINAN - AGRAVOS RELACIONADOS AO TRABALHO\n")
cat("Campos dos Goytacazes (330100) | 2018-2025\n")
cat("========================================\n\n")

dbcs <- list.files(DIR_SINAN, pattern = "\\.dbc$", ignore.case = TRUE)
cat(sprintf("%d arquivos .dbc em %s\n\n", length(dbcs), DIR_SINAN))

todos <- list()
estatisticas <- list()
log_processamento <- list()

for (nome in dbcs) {
  prefixo <- toupper(substr(nome, 1, 4))
  if (!(prefixo %in% AGRAVOS_TRAB)) next
  
  ano_suf <- as.integer(substr(nome, 7, 8))
  ano <- if (ano_suf < 60) 2000 + ano_suf else 1900 + ano_suf
  if (ano < 2018 || ano > 2025) next
  
  # Pular duplicados (ex: ACGRBR18_NOVO)
  if (grepl("NOVO", nome, ignore.case = TRUE)) next
  
  path <- file.path(DIR_SINAN, nome)
  cat(sprintf("[%s] %d %s ...", prefixo, ano, nome))
  
  # Ler DBC
  df <- tryCatch({
    read.dbc(path, as.is = TRUE)
  }, error = function(e) {
    cat(sprintf(" ERRO LEITURA: %s\n", e$message))
    return(NULL)
  })
  
  if (is.null(df) || nrow(df) == 0) {
    cat(" vazio\n")
    next
  }
  
  n_br <- nrow(df)
  
  # Filtrar Campos
  col_mun <- "ID_MN_RESI"
  if (!(col_mun %in% names(df))) {
    col_mun <- grep("ID_MUNICIP|MUNICIPIO|MUN_RES", names(df), 
                    value = TRUE, ignore.case = TRUE)[1]
  }
  if (is.na(col_mun) || !(col_mun %in% names(df))) {
    cat(" sem coluna municipio\n")
    next
  }
  
  df$mun_str <- as.character(df[[col_mun]])
  campos <- df[df$mun_str == MUN_COD, ]
  n_campos_total <- nrow(campos)
  
  # ===== FILTRO DE ACIDENTE/DOENCA DE TRABALHO =====
  # Regras por agravo:
  
  if (prefixo == "ANIM") {
    # ANIM: filtrar apenas acidentes de trabalho
    # Campo SIT_TRAB: 1=Sim (trabalho), 2=Nao, 9=Ignorado
    # Campo TP_ACIDENT: 1=Trabalho habitual, 2=Trajeto, etc.
    if ("SIT_TRAB" %in% names(campos)) {
      campos <- campos[campos$SIT_TRAB == "1", ]
    } else if ("ACID_TRAB" %in% names(campos)) {
      campos <- campos[campos$ACID_TRAB == "1", ]
    }
    # Se nenhum dos campos existe, manter todos
    filtro_msg <- "SIT_TRAB=1"
    
  } else if (prefixo %in% c("ACGR", "ACBI")) {
    # ACGR e ACBI: ja sao agravos de trabalho por definicao
    # Sem filtro adicional
    filtro_msg <- "todos (agravo ja e de trabalho)"
    
  } else {
    # CANC, DERM, LERD, PNEU, PAIR, MENT:
    # Sao agravos ESPECIFICOS de doenca relacionada ao trabalho
    # Nao precisam de filtro adicional (a ficha ja e a de doenca do trabalho)
    filtro_msg <- "todos (agravo especifico de doenca do trabalho)"
  }
  
  n_campos_trab <- nrow(campos)
  
  cat(sprintf(" BR=%d Campos=%d Trab=%d (%s)\n", 
              n_br, n_campos_total, n_campos_trab, filtro_msg))
  
  if (n_campos_trab > 0) {
    campos$`_agravo_cod` <- prefixo
    campos$`_ano` <- ano
    campos$`_arquivo` <- nome
    campos$mun_str <- NULL
    
    todos[[length(todos) + 1]] <- campos
    estatisticas[[paste0(prefixo, "_", ano)]] <- c(prefixo, ano, n_campos_trab)
  }
  
  log_processamento[[paste0(prefixo, "_", ano)]] <- list(
    agravo = prefixo, ano = ano, br = n_br, 
    campos_total = n_campos_total, campos_trab = n_campos_trab,
    filtro = filtro_msg
  )
  
  gc()
}

# ========== CONSOLIDAR ==========
if (length(todos) > 0) {
  cat("\n========================================\n")
  cat("Consolidando...\n")
  
  todas_cols <- unique(unlist(lapply(todos, names)))
  todos_pad <- lapply(todos, function(df) {
    faltantes <- setdiff(todas_cols, names(df))
    for (col in faltantes) df[[col]] <- NA
    df[, todas_cols]
  })
  
  final <- do.call(rbind, todos_pad)
  
  path_csv <- file.path(DIR_PROC, "sinan_trabalho_campos_2018_2025.csv")
  write.csv2(final, path_csv, row.names = FALSE, fileEncoding = "UTF-8")
  
  cat(sprintf("CSV salvo: %s\n", path_csv))
  cat(sprintf("Registros: %d | Colunas: %d\n", nrow(final), ncol(final)))
} else {
  cat("\nNENHUM registro de agravo de trabalho encontrado em Campos.\n")
}

# ========== RESUMO ==========
cat("\n========================================\n")
cat("RESUMO - Agravos Relacionados ao Trabalho\n")
cat("Campos dos Goytacazes (330100) | 2018-2025\n")
cat("========================================\n")

anos <- 2018:2025
cat(sprintf("%-45s", "Agravo"))
for (a in anos) cat(sprintf(" %5s", a))
cat(sprintf(" %6s\n", "Total"))
cat(paste(rep("-", 85), collapse = ""), "\n")

total_geral <- 0
for (cod in AGRAVOS_TRAB) {
  total_agravo <- 0
  cat(sprintf("  %-43s", cod))
  for (a in anos) {
    key <- paste0(cod, "_", a)
    n <- if (key %in% names(estatisticas)) as.integer(estatisticas[[key]][3]) else 0
    cat(sprintf(" %5d", n))
    total_agravo <- total_agravo + n
    total_geral <- total_geral + n
  }
  cat(sprintf(" %6d\n", total_agravo))
}
cat(paste(rep("-", 85), collapse = ""), "\n")
cat(sprintf("%-45s", "  TOTAL"))
for (a in anos) {
  s <- 0
  for (cod in AGRAVOS_TRAB) {
    key <- paste0(cod, "_", a)
    s <- s + if (key %in% names(estatisticas)) as.integer(estatisticas[[key]][3]) else 0
  }
  cat(sprintf(" %5d", s))
}
cat(sprintf(" %6d\n", total_geral))

# Salvar tabela resumo
tbl_resumo <- data.frame(agravo = character(), stringsAsFactors = FALSE)
for (a in anos) tbl_resumo[[as.character(a)]] <- integer()
tbl_resumo$total <- integer()

for (cod in AGRAVOS_TRAB) {
  row <- list(agravo = cod)
  total <- 0
  for (a in anos) {
    key <- paste0(cod, "_", a)
    n <- if (key %in% names(estatisticas)) as.integer(estatisticas[[key]][3]) else 0
    row[[as.character(a)]] <- n
    total <- total + n
  }
  row$total <- total
  tbl_resumo <- rbind(tbl_resumo, as.data.frame(row, stringsAsFactors = FALSE))
}

path_tbl <- file.path(DIR_SAIDAS, "T39_sinan_trabalho_resumo.csv")
write.csv2(tbl_resumo, path_tbl, row.names = FALSE, fileEncoding = "UTF-8")
cat(sprintf("\nTabela resumo: %s\n", path_tbl))

cat("\nOK - SINAN agravos de trabalho processado.\n")
