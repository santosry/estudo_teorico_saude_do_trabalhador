################################################################################
## download_sih_sim_ben.R                                                    ##
## Baixa SIH (internacoes), SIM (obitos) e BEN/INSS (beneficios acidentarios) ##
## para Campos dos Goytacazes (330100) via microdatasus                       ##
################################################################################

# Instalar microdatasus se necessario
if (!require("microdatasus")) {
  install.packages("remotes", repos = "https://cran.r-project.org")
  remotes::install_github("rfsaldanha/microdatasus")
  library(microdatasus)
}

MUN_COD <- "330100"
UF <- "RJ"
ANOS <- 2018:2025
DIR_PROC <- "dados/processados"
dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)

# ============================================================
# 1. SIH/SUS - Internacoes Hospitalares (RD - Reduzida)
# ============================================================
cat("\n========================================\n")
cat("1. SIH/SUS - Internacoes Hospitalares\n")
cat("========================================\n")

# CIDs relacionados ao trabalho (grupos principais segundo OMS/OIT):
# Y96 = Fatores relacionados ao trabalho
# Z57 = Exposicao ocupacional a fatores de risco
# W00-X59 = Causas externas de traumatismos acidentais (acidentes)
# S00-T98 = Traumatismos, envenenamentos (quando causa externa = trabalho)
# J60-J70 = Pneumoconioses
# L23-L25 = Dermatites de contato
# G56 = Mononeuropatias (LER/DORT relacionada)

cids_trabalho_cat <- c(
  # Pneumoconioses e doencas pulmonares ocupacionais
  "J60", "J61", "J62", "J63", "J64", "J65", "J66", "J67", "J68", "J69", "J70",
  # Dermatites ocupacionais
  "L23", "L24", "L25",
  # LER/DORT e neuropatias
  "G56", "M70", "M75", "M76", "M77",
  # Transtornos mentais (quando relacionados ao trabalho)
  "F43",
  # Intoxicacoes ocupacionais
  "T51", "T52", "T53", "T54", "T55", "T56", "T57", "T58", "T59", "T60",
  # Traumatismos (com causa externa compativel com trabalho)
  "S61", "S62", "S63", "S64", "S65", "S66", "S67", "S68",
  # Queimaduras
  "T20", "T21", "T22", "T23", "T24", "T25", "T26", "T27", "T28", "T29",
  "T30", "T31", "T32"
)

cat("Baixando SIH-RD (RJ) 2018-2025...\n")
cat("(Este download pode demorar varios minutos por ano)\n\n")

todos_sih <- list()

for (ano in ANOS) {
  cat(sprintf("  [%d] Baixando...", ano))
  
  df <- tryCatch({
    fetch_datasus(
      year_start = ano,
      year_end = ano,
      uf = UF,
      information_system = "SIH-RD",
      vars = c("MUNIC_RES", "MUNIC_MOV", "DIAG_PRINC", "DIAG_SECUN",
               "CAUSAS_EXT", "IDADE", "SEXO", "RACA_COR",
               "DT_INTER", "DT_SAIDA", "DIAS_PERM", "MORTE",
               "VAL_TOT", "VAL_SH", "VAL_SP", "CNES", "PROC_REA")
    )
  }, error = function(e) {
    cat(sprintf(" ERRO: %s\n", e$message))
    return(NULL)
  })
  
  if (is.null(df) || nrow(df) == 0) {
    cat(" vazio\n")
    next
  }
  
  cat(sprintf(" %d registros RJ. ", nrow(df)))
  
  # Filtrar Campos
  df$MUNIC_RES <- as.character(df$MUNIC_RES)
  campos <- df[df$MUNIC_RES == MUN_COD, ]
  
  # Filtrar por CID trabalho (se disponivel)
  if ("DIAG_PRINC" %in% names(campos)) {
    campos$cid_3 <- substr(as.character(campos$DIAG_PRINC), 1, 3)
    campos$cid_trabalho <- campos$cid_3 %in% cids_trabalho_cat
    
    # Internacoes COM e SEM CID de trabalho
    n_trab <- sum(campos$cid_trabalho, na.rm = TRUE)
    cat(sprintf("Campos=%d (CID trabalho=%d)\n", nrow(campos), n_trab))
  } else {
    cat(sprintf("Campos=%d\n", nrow(campos)))
  }
  
  if (nrow(campos) > 0) {
    campos$`_ano` <- ano
    campos$`_fonte` <- "SIH/SUS"
    todos_sih[[length(todos_sih) + 1]] <- campos
  }
}

if (length(todos_sih) > 0) {
  final_sih <- do.call(rbind, todos_sih)
  path_sih <- file.path(DIR_PROC, "sih_campos_2018_2025.csv")
  write.csv2(final_sih, path_sih, row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("\nSIH salvo: %s (%d registros)\n", path_sih, nrow(final_sih)))
}


# ============================================================
# 2. SIM - Mortalidade
# ============================================================
cat("\n========================================\n")
cat("2. SIM - Mortalidade (obitos com CID trabalho)\n")
cat("========================================\n")

# CIDs de causas externas + causas relacionadas ao trabalho
cids_morte_trabalho <- c(
  # Acidentes de transporte (trabalhadores em transito)
  paste0("V", sprintf("%02d", 1:99)),
  # Quedas, exposicao a forcas mecanicas, afogamento, etc.
  paste0("W", sprintf("%02d", 0:99)),
  paste0("X", sprintf("%02d", 0:99)),
  # todas Y (eventos de intencao indeterminada + fatores relacionados ao trabalho)
  paste0("Y", sprintf("%02d", 0:99)),
  # Pneumoconioses
  "J60", "J61", "J62", "J63", "J64", "J65", "J66", "J67", "J68",
  # Intoxicacoes
  "T51", "T52", "T53", "T54", "T55", "T56", "T57", "T58", "T59", "T60"
)

cat("Baixando SIM-DO (RJ) 2018-2025...\n\n")

todos_sim <- list()

for (ano in ANOS) {
  cat(sprintf("  [%d] Baixando...", ano))
  
  df <- tryCatch({
    fetch_datasus(
      year_start = ano,
      year_end = ano,
      uf = UF,
      information_system = "SIM-DO",
      vars = c("CODMUNRES", "CAUSABAS", "LINHAA", "LINHAB",
               "LINHAC", "LINHAD", "LINHAII", "CAUSABAS_O",
               "IDADE", "SEXO", "RACACOR", "ESC", "OCUP",
               "DTOBITO", "ASSISTMED", "CIRCOBITO", "ACIDTRAB")
    )
  }, error = function(e) {
    cat(sprintf(" ERRO: %s\n", e$message))
    return(NULL)
  })
  
  if (is.null(df) || nrow(df) == 0) {
    cat(" vazio\n")
    next
  }
  
  cat(sprintf(" %d obitos RJ. ", nrow(df)))
  
  # Filtrar Campos
  df$CODMUNRES <- as.character(df$CODMUNRES)
  campos <- df[df$CODMUNRES == MUN_COD, ]
  
  # Filtrar por CID de trabalho
  if ("CAUSABAS" %in% names(campos)) {
    campos$cid_3 <- substr(as.character(campos$CAUSABAS), 1, 3)
    campos$cid_trabalho <- campos$cid_3 %in% cids_morte_trabalho
    
    n_trab <- sum(campos$cid_trabalho, na.rm = TRUE)
    cat(sprintf("Campos=%d (obitos CID trabalho=%d)\n", nrow(campos), n_trab))
  } else {
    cat(sprintf("Campos=%d\n", nrow(campos)))
  }
  
  if (nrow(campos) > 0) {
    campos$`_ano` <- ano
    campos$`_fonte` <- "SIM"
    todos_sim[[length(todos_sim) + 1]] <- campos
  }
}

if (length(todos_sim) > 0) {
  final_sim <- do.call(rbind, todos_sim)
  path_sim <- file.path(DIR_PROC, "sim_campos_obitos_trabalho_2018_2025.csv")
  write.csv2(final_sim, path_sim, row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("\nSIM salvo: %s (%d registros)\n", path_sim, nrow(final_sim)))
}


# ============================================================
# 3. BEN/INSS - Beneficios Acidentarios
# ============================================================
cat("\n========================================\n")
cat("3. BEN/INSS - Beneficios Acidentarios\n")
cat("========================================\n")

cat("Baixando beneficios acidentarios (B91-B94) 2018-2025...\n\n")

# Tentar via Infologo/INSS (se disponivel)
# O microdatasus pode acessar sistemas do INSS
todos_ben <- list()

for (ano in ANOS) {
  cat(sprintf("  [%d] Tentando...", ano))
  
  # Tentar varios sistemas
  sistemas <- c("INSS-AT", "INSS-BEN", "INSS")
  df <- NULL
  
  for (sis in sistemas) {
    df <- tryCatch({
      fetch_datasus(
        year_start = ano,
        year_end = ano,
        information_system = sis,
        vars = c("MUN_RES", "MUN_OCOR", "DT_OCOR", "ESPECIE",
                 "TP_BENEF", "SEXO", "IDADE", "CID10", "VALOR")
      )
    }, error = function(e) NULL)
    
    if (!is.null(df) && nrow(df) > 0) break
  }
  
  if (is.null(df) || nrow(df) == 0) {
    cat(" indisponivel\n")
    next
  }
  
  cat(sprintf(" %d beneficios BR. ", nrow(df)))
  
  # Buscar coluna municipio
  col_mun <- grep("MUN_RES|MUNICIP", names(df), value = TRUE, ignore.case = TRUE)
  if (length(col_mun) == 0) {
    cat(" sem coluna municipio\n")
    next
  }
  
  df[[col_mun[1]]] <- as.character(df[[col_mun[1]]])
  campos <- df[df[[col_mun[1]]] == MUN_COD, ]
  
  cat(sprintf("Campos=%d\n", nrow(campos)))
  
  if (nrow(campos) > 0) {
    campos$`_ano` <- ano
    campos$`_fonte` <- "BEN/INSS"
    todos_ben[[length(todos_ben) + 1]] <- campos
  }
}

if (length(todos_ben) > 0) {
  final_ben <- do.call(rbind, todos_ben)
  path_ben <- file.path(DIR_PROC, "ben_inss_campos_2018_2025.csv")
  write.csv2(final_ben, path_ben, row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("\nBEN/INSS salvo: %s (%d registros)\n", path_ben, nrow(final_ben)))
} else {
  cat("\nBEN/INSS: microdatasus nao suporta INSS diretamente.")
  cat("\nAlternativa: TabNet manual em http://tabnet.datasus.gov.br/cgi/deftohtm.exe?infologo/env/atbr.def\n")
}

cat("\nOK Script concluido.\n")
