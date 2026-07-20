################################################################################
## download_sih_campos.R                                                       ##
## SIH/SUS - Internacoes Hospitalares - Campos dos Goytacazes (330100)         ##
## Fonte: FTP DATASUS (dissemin/publicos/SIHSUS/200801_/Dados)                 ##
## Metodo: download .dbc + read.dbc + filtro MUNIC_RES=330100                  ##
##                                                                             ##
## Filtro CID trabalho:                                                        ##
##   Y96 = Fatores relacionados ao trabalho                                    ##
##   Z57 = Exposicao ocupacional                                               ##
##   S00-T98 + causa externa trabalho (W00-X59, Y96, Z57)                      ##
##   J60-J70 = Pneumoconioses                                                  ##
##   L23-L25 = Dermatites ocupacionais                                         ##
##   G56 = Mononeuropatias (LER/DORT)                                          ##
################################################################################
library(read.dbc)

MUN_COD <- "330100"
DIR_SIH <- "banco de dados/sih"
DIR_PROC <- "dados/processados"
dir.create(DIR_SIH, showWarnings = FALSE, recursive = TRUE)
dir.create(DIR_PROC, showWarnings = FALSE, recursive = TRUE)

FTP_HOST <- "ftp.datasus.gov.br"
FTP_DIR <- "dissemin/publicos/SIHSUS/200801_/Dados"
ANOS <- 2018:2025

# Usar somente RDRJ (Reduzida) - contem as variaveis principais da AIH
PREFIXO <- "RDRJ"

cat("========================================\n")
cat("SIH/SUS - INTERNACOES HOSPITALARES\n")
cat("Campos dos Goytacazes (330100) | 2018-2025\n")
cat("========================================\n\n")

# CIDs relacionados ao trabalho para filtro
cids_trabalho <- c(
  # Pneumoconioses
  "J60", "J61", "J62", "J63", "J64", "J65", "J66", "J67", "J68", "J69", "J70",
  # Dermatites
  "L23", "L24", "L25",
  # LER/DORT
  "G56",
  # Transtorno mental (estresse pos-traumatico relacionado ao trabalho)
  "F431",
  # Intoxicacoes ocupacionais
  "T51", "T52", "T53", "T54", "T55", "T56", "T57", "T58", "T59", "T60",
  # Traumatismos de punho e mao (acidentes tipicos)
  "S61", "S62", "S63", "S64", "S65", "S66", "S67", "S68",
  # Queimaduras
  "T20", "T21", "T22", "T23", "T24", "T25", "T26", "T27", "T28", "T29",
  "T30", "T31", "T32",
  # Fraturas de membros superiores (quedas/acidentes)
  "S52", "S42", "S72",
  # Amputacoes traumaticas
  "S58", "S68", "S78", "S88", "S98",
  # Fatores relacionados ao trabalho
  "Y96",
  # Exposicao ocupacional
  "Z57"
)

todos <- list()
estatisticas <- list()

for (ano in ANOS) {
  ano_2dig <- substr(as.character(ano), 3, 4)
  
  for (mes in 1:12) {
    mes_str <- sprintf("%02d", mes)
    nome <- paste0(PREFIXO, ano_2dig, mes_str, ".dbc")
    local <- file.path(DIR_SIH, nome)
    
    # Download
    if (!file.exists(local)) {
      cat(sprintf("[%d-%s] Baixando %s ...", ano, mes_str, nome))
      ok <- tryCatch({
        download.file(
          url = paste0("ftp://", FTP_HOST, "/", FTP_DIR, "/", nome),
          destfile = local,
          mode = "wb",
          quiet = TRUE
        )
        TRUE
      }, error = function(e) FALSE)
      
      if (!ok || file.info(local)$size < 1000) {
        cat(" FALHOU\n")
        next
      }
      cat(sprintf(" OK (%.1f MB)\n", file.info(local)$size / 1e6))
    }
    
    # Processar
    cat(sprintf("[%d-%s] Processando ...", ano, mes_str))
    
    df <- tryCatch({
      read.dbc(local, as.is = TRUE)
    }, error = function(e) {
      cat(sprintf(" ERRO: %s\n", e$message))
      return(NULL)
    })
    
    if (is.null(df) || nrow(df) == 0) {
      cat(" vazio\n")
      next
    }
    
    n_rj <- nrow(df)
    
    # Filtrar municipio de residencia
    col_mun <- "MUNIC_RES"
    if (!(col_mun %in% names(df))) {
      col_mun <- grep("MUNIC_RES|MUNIC_MOV|MUN_RES", names(df), 
                      value = TRUE, ignore.case = TRUE)[1]
    }
    
    if (is.na(col_mun) || !(col_mun %in% names(df))) {
      cat(" sem coluna municipio\n")
      next
    }
    
    df$mun_str <- as.character(df[[col_mun]])
    campos <- df[df$mun_str == MUN_COD, ]
    n_campos <- nrow(campos)
    
    # Filtrar CID trabalho
    n_cid_trab <- 0
    col_diag <- grep("DIAG_PRINC|DIAG_PRI", names(campos), 
                     value = TRUE, ignore.case = TRUE)
    if (length(col_diag) > 0) {
      col_diag <- col_diag[1]
      campos$cid_3 <- substr(as.character(campos[[col_diag]]), 1, 3)
      campos$cid_4 <- substr(as.character(campos[[col_diag]]), 1, 4)
      
      mask_trab <- campos$cid_3 %in% cids_trabalho | campos$cid_4 %in% cids_trabalho
      n_cid_trab <- sum(mask_trab, na.rm = TRUE)
      campos$cid_trabalho <- mask_trab
    }
    
    cat(sprintf(" RJ=%d Campos=%d CID_trab=%d\n", n_rj, n_campos, n_cid_trab))
    
    if (n_campos > 0) {
      campos$`_ano` <- ano
      campos$`_mes` <- mes
      campos$`_arquivo` <- nome
      campos$mun_str <- NULL
      
      todos[[length(todos) + 1]] <- campos
    }
    
    key <- paste0(ano, "_", mes_str)
    estatisticas[[key]] <- c(ano, mes, n_rj, n_campos, n_cid_trab)
    
    gc()
  }
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
  cat(sprintf("Registros: %d | Colunas: %d\n", nrow(final), ncol(final)))
  
  # Estatisticas
  if ("cid_trabalho" %in% names(final)) {
    n_trab <- sum(final$cid_trabalho, na.rm = TRUE)
    cat(sprintf("Internacoes com CID trabalho: %d (%.1f%%)\n", 
                n_trab, 100 * n_trab / nrow(final)))
  }
  
} else {
  cat("\nNENHUM registro SIH de Campos encontrado.\n")
}

cat("\nOK Script concluido.\n")
