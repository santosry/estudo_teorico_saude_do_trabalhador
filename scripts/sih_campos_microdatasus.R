################################################################################
## sih_campos_microdatasus.R                                                   ##
## SIH/SUS via microdatasus - Campos dos Goytacazes (330100) | 2018-2025       ##
## Baixa mes a mes para evitar memoria, filtra municipio e CID trabalho        ##
## EXECUTAR COM: R.exe -f scripts/sih_campos_microdatasus.R                    ##
################################################################################
library(microdatasus)

MUN_COD <- "330100"
UF <- "RJ"
ANOS <- 2018:2025
DIR_PROC <- "dados/processados"
DIR_SAIDAS <- "saidas/tabelas"
dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(DIR_SAIDAS, showWarnings = FALSE, recursive = TRUE)

# CIDs relacionados ao trabalho
cids_trabalho <- c(
  "Y96",    # Fatores relacionados ao trabalho
  "Z57",    # Exposicao ocupacional a fatores de risco
  "J60","J61","J62","J63","J64","J65","J66","J67","J68","J69","J70", # Pneumoconioses
  "L23","L24","L25",  # Dermatites de contato
  "G56",    # Mononeuropatias (LER/DORT)
  "F431",   # Estresse pos-traumatico
  "T51","T52","T53","T54","T55","T56","T57","T58","T59","T60", # Intoxicacoes
  "S61","S62","S63","S64","S65","S66","S67","S68", # Traumatismos mao/punho
  "S52","S42",  # Fraturas membro superior
  "S58","S68",  # Amputacoes traumaticas
  "T20","T21","T22","T23","T24","T25","T26","T27","T28","T29","T30","T31","T32" # Queimaduras
)

cat("========================================\n")
cat("SIH/SUS - INTERNACOES HOSPITALARES\n")
cat("Campos dos Goytacazes (330100) | 2018-2025\n")
cat("Metodo: microdatasus + CID trabalho\n")
cat("========================================\n\n")

todos <- list()
resumo_ano <- list()

for (ano in ANOS) {
  cat(sprintf("\n--- %d ---\n", ano))
  
  total_ano <- 0
  total_cid_trab <- 0
  
  for (mes in 1:12) {
    cat(sprintf("  %02d...", mes))
    
    df <- tryCatch({
      fetch_datasus(
        year_start = ano, year_end = ano,
        month_start = mes, month_end = mes,
        uf = UF,
        information_system = "SIH-RD"
      )
    }, error = function(e) {
      cat(sprintf(" ERRO: %s\n", e$message))
      return(NULL)
    })
    
    if (is.null(df) || nrow(df) == 0) {
      cat(" vazio\n")
      next
    }
    
    # Filtrar Campos (MUNIC_RES = municipio residencia)
    col_mun <- "MUNIC_RES"
    if (!(col_mun %in% names(df))) {
      col_mun <- grep("MUNIC_RES|MUNIC_MOV", names(df), value = TRUE, ignore.case = TRUE)[1]
    }
    if (is.na(col_mun) || !(col_mun %in% names(df))) {
      cat(" sem MUNIC_RES\n")
      next
    }
    
    df$mun_str <- as.character(df[[col_mun]])
    campos <- df[df$mun_str == MUN_COD, ]
    n_campos <- nrow(campos)
    total_ano <- total_ano + n_campos
    
    # Marcar CID trabalho
    n_cid <- 0
    if (n_campos > 0 && "DIAG_PRINC" %in% names(campos)) {
      cid <- as.character(campos$DIAG_PRINC)
      campos$cid_3 <- substr(cid, 1, 3)
      campos$cid_4 <- substr(cid, 1, 4)
      campos$cid_trabalho <- campos$cid_3 %in% cids_trabalho | campos$cid_4 %in% cids_trabalho
      n_cid <- sum(campos$cid_trabalho, na.rm = TRUE)
      total_cid_trab <- total_cid_trab + n_cid
    }
    
    cat(sprintf(" Campos=%d CID_trab=%d\n", n_campos, n_cid))
    
    if (n_campos > 0) {
      campos$`_ano` <- ano
      campos$`_mes` <- mes
      campos$mun_str <- NULL
      todos[[length(todos) + 1]] <- campos
    }
    
    gc()
  }
  
  cat(sprintf("  TOTAL %d: %d internacoes, %d com CID trabalho\n", 
              ano, total_ano, total_cid_trab))
  resumo_ano[[as.character(ano)]] <- c(total_ano, total_cid_trab)
}

# Consolidar
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
  
  path_csv <- file.path(DIR_PROC, "sih_campos_2018_2025.csv")
  write.csv2(final, path_csv, row.names = FALSE, fileEncoding = "UTF-8")
  
  cat(sprintf("CSV salvo: %s\n", path_csv))
  cat(sprintf("Total registros: %d | Colunas: %d\n", nrow(final), ncol(final)))
  
  if ("cid_trabalho" %in% names(final)) {
    n_trab <- sum(final$cid_trabalho, na.rm = TRUE)
    cat(sprintf("Internacoes com CID trabalho: %d (%.1f%%)\n", 
                n_trab, 100 * n_trab / nrow(final)))
  }
  
  # Resumo por ano
  cat("\nResumo por ano:\n")
  cat(sprintf("%-6s %10s %12s\n", "Ano", "Internacoes", "CID_trabalho"))
  for (ano in ANOS) {
    vals <- resumo_ano[[as.character(ano)]]
    cat(sprintf("%-6d %10d %12d\n", ano, vals[1], vals[2]))
  }
  
} else {
  cat("\nNENHUM registro SIH de Campos encontrado.\n")
}

cat("\nOK Script concluido.\n")
