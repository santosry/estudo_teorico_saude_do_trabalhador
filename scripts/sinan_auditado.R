################################################################################
## sinan_auditado.R                                                            ##
## SINAN - AUDITORIA RIGOROSA dos agravos de trabalho                          ##
## Campos dos Goytacazes (330100) | 2018-2025                                  ##
##                                                                             ##
## Regras de filtro (baseadas nos campos do SINAN):                            ##
##                                                                             ##
## ACGR (Acidente de Trabalho):                                                ##
##   SIT_TRAB=01 (Sim, acidente de trabalho)                                   ##
##   Excluir SIT_TRAB=02 (Nao), 03 (Ignorado), 04 (Nao se aplica)             ##
##                                                                             ##
## ACBI (Acid Trab Material Biologico):                                        ##
##   SIT_TRAB=01 (Sim, acidente de trabalho)                                   ##
##   Excluir SIT_TRAB=02, 03, 04                                               ##
##                                                                             ##
## ANIM (Animais Peconhentos):                                                 ##
##   SIT_TRAB=01 (ou TP_ACIDENT indicando trabalho)                            ##
##                                                                             ##
## CANC, DERM, LERD, MENT, PAIR, PNEU (doencas):                               ##
##   TRAB_DOE=1 (Sim, doenca relacionada ao trabalho)                          ##
##   Excluir TRAB_DOE=2 (Nao), 9 (Ignorado)                                   ##
##                                                                             ##
## NOTA: Os arquivos do FTP (CANC, DERM, etc) sao as fichas ESPECIFICAS        ##
## de notificacao de doenca relacionada ao trabalho. Porem, o campo            ##
## TRAB_DOE indica se o profissional de saude confirmou o nexo causal.         ##
## Por rigor metodologico, so contamos TRAB_DOE=1 (confirmado).                ##
################################################################################
library(read.dbc)

MUN_COD <- "330100"
DIR_SINAN <- "dados/brutos/sinan"
DIR_PROC <- "dados/processados"
DIR_SAIDAS <- "saidas/tabelas"
dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(DIR_SAIDAS, showWarnings = FALSE, recursive = TRUE)

cat("========================================\n")
cat("SINAN - AUDITORIA RIGOROSA\n")
cat("Agravos de trabalho - Campos dos Goytacazes (330100)\n")
cat("2018-2025\n")
cat("========================================\n\n")

dbcs <- list.files(DIR_SINAN, pattern = "\\.dbc$", ignore.case = TRUE)

todos <- list()
estatisticas <- list()
log_filtros <- list()

for (nome in dbcs) {
  prefixo <- toupper(substr(nome, 1, 4))
  if (!(prefixo %in% c("ACGR","ACBI","ANIM","CANC","DERM","LERD","MENT","PAIR","PNEU"))) next
  
  ano_suf <- as.integer(substr(nome, 7, 8))
  ano <- if (ano_suf < 60) 2000 + ano_suf else 1900 + ano_suf
  if (ano < 2018 || ano > 2025) next
  if (grepl("NOVO", nome, ignore.case = TRUE)) next
  
  path <- file.path(DIR_SINAN, nome)
  cat(sprintf("[%s] %d %s ...", prefixo, ano, nome))
  
  df <- tryCatch(read.dbc(path, as.is = TRUE), error = function(e) NULL)
  if (is.null(df) || nrow(df) == 0) { cat(" vazio\n"); next }
  
  # Filtrar Campos
  col_mun <- "ID_MN_RESI"
  if (!(col_mun %in% names(df))) {
    col_mun <- grep("ID_MUNICIP|ID_MN_RESI", names(df), value = TRUE, ignore.case = TRUE)[1]
  }
  if (is.na(col_mun) || !(col_mun %in% names(df))) { cat(" sem coluna mun\n"); next }
  
  df$mun_str <- as.character(df[[col_mun]])
  campos <- df[df$mun_str == MUN_COD, ]
  n_total <- nrow(campos)
  
  # === APLICAR FILTRO DE TRABALHO ===
  
  if (prefixo %in% c("ACGR", "ACBI")) {
    # Acidentes de trabalho: filtrar por SIT_TRAB=01
    if ("SIT_TRAB" %in% names(campos)) {
      sit_trab <- as.character(campos$SIT_TRAB)
      mask_trab <- sit_trab == "1" | sit_trab == "01"
      campos <- campos[mask_trab, ]
      filtro <- "SIT_TRAB=1"
    } else {
      filtro <- "SIT_TRAB indisponivel - mantendo todos"
    }
    
  } else if (prefixo == "ANIM") {
    # Animais peconhentos: SIT_TRAB=1 OU TP_ACIDENT indicando trabalho
    if ("SIT_TRAB" %in% names(campos)) {
      sit_trab <- as.character(campos$SIT_TRAB)
      mask <- sit_trab == "1" | sit_trab == "01"
      campos <- campos[mask, ]
      filtro <- "SIT_TRAB=1"
    } else if ("TP_ACIDENT" %in% names(campos)) {
      tp <- as.character(campos$TP_ACIDENT)
      mask <- tp == "1"  # 1=Trabalho habitual
      campos <- campos[mask, ]
      filtro <- "TP_ACIDENT=1"
    } else {
      filtro <- "sem campo de filtro"
    }
    
  } else {
    # Doencas (CANC, DERM, LERD, MENT, PAIR, PNEU): filtrar por TRAB_DOE=1
    if ("TRAB_DOE" %in% names(campos)) {
      trab_doe <- as.character(campos$TRAB_DOE)
      mask <- trab_doe == "1" | trab_doe == "01" | trab_doe == "1.0"
      campos <- campos[mask, ]
      filtro <- "TRAB_DOE=1"
    } else if ("SIT_TRAB" %in% names(campos)) {
      sit_trab <- as.character(campos$SIT_TRAB)
      mask <- sit_trab == "1" | sit_trab == "01"
      campos <- campos[mask, ]
      filtro <- "SIT_TRAB=1 (fallback)"
    } else {
      filtro <- "sem campo TRAB_DOE - mantendo todos"
    }
  }
  
  n_filtrado <- nrow(campos)
  
  cat(sprintf(" total=%d filtrado=%d (%s)\n", n_total, n_filtrado, filtro))
  
  if (n_filtrado > 0) {
    campos$`_agravo_cod` <- prefixo
    campos$`_ano` <- ano
    campos$`_arquivo` <- nome
    campos$mun_str <- NULL
    
    todos[[length(todos) + 1]] <- campos
    estatisticas[[paste0(prefixo, "_", ano)]] <- c(prefixo, ano, n_filtrado)
  }
  
  log_filtros[[paste0(prefixo, "_", ano)]] <- list(
    agravo = prefixo, ano = ano, total = n_total, 
    filtrado = n_filtrado, filtro = filtro
  )
  
  gc()
}

# Consolidar
if (length(todos) > 0) {
  todas_cols <- unique(unlist(lapply(todos, names)))
  todos_pad <- lapply(todos, function(df) {
    faltantes <- setdiff(todas_cols, names(df))
    for (col in faltantes) df[[col]] <- NA
    df[, todas_cols]
  })
  
  final <- do.call(rbind, todos_pad)
  
  path_csv <- file.path(DIR_PROC, "sinan_trabalho_auditado_2018_2025.csv")
  write.csv2(final, path_csv, row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("\nCSV salvo: %s (%d registros)\n", path_csv, nrow(final)))
}

# Resumo
cat("\n========================================\n")
cat("RESUMO AUDITADO - SINAN Trab. Campos 2018-2025\n")
cat("========================================\n")

nomes_agravo <- c(
  "ACGR" = "Acidente de Trabalho",
  "ACBI" = "Acid Trab c/ Mat Biologico",
  "ANIM" = "Animais Peconhentos (trab)",
  "CANC" = "Cancer Relacionado ao Trab",
  "DERM" = "Dermatose Relacionada ao Trab",
  "LERD" = "LER/DORT",
  "MENT" = "Transtorno Mental Relac Trab",
  "PAIR" = "PAIR",
  "PNEU" = "Pneumoconiose Relac Trab"
)

anos <- 2018:2025
cat(sprintf("%-42s", "Agravo"))
for (a in anos) cat(sprintf(" %6s", a))
cat(sprintf(" %7s\n", "Total"))
cat(paste(rep("-", 90), collapse = ""), "\n")

total_geral <- 0
for (cod in names(nomes_agravo)) {
  total_agravo <- 0
  cat(sprintf("  %-40s", nomes_agravo[cod]))
  for (a in anos) {
    key <- paste0(cod, "_", a)
    n <- if (key %in% names(estatisticas)) as.integer(estatisticas[[key]][3]) else 0
    cat(sprintf(" %6d", n))
    total_agravo <- total_agravo + n
    total_geral <- total_geral + n
  }
  cat(sprintf(" %7d\n", total_agravo))
}
cat(paste(rep("-", 90), collapse = ""), "\n")
cat(sprintf("%-42s", "  TOTAL"))
for (a in anos) {
  s <- sum(sapply(names(nomes_agravo), function(cod) {
    key <- paste0(cod, "_", a)
    if (key %in% names(estatisticas)) as.integer(estatisticas[[key]][3]) else 0
  }))
  cat(sprintf(" %6d", s))
}
cat(sprintf(" %7d\n", total_geral))

cat("\nNOTAS METODOLOGICAS:\n")
cat("  ACGR/ACBI: filtro SIT_TRAB=01 (acidente de trabalho confirmado)\n")
cat("  ANIM: filtro SIT_TRAB=01\n")
cat("  CANC/DERM/LERD/MENT/PAIR/PNEU: filtro TRAB_DOE=1 (nexo confirmado)\n")
cat("  Fonte: DATASUS SINAN (FINAIS 2018-2022 + PRELIM 2023-2025)\n")

cat("\nOK Script concluido.\n")
