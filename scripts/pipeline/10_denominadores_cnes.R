# 10_denominadores_cnes.R — CNES via microdatasus
# Baixa CNES-PF (profissionais) para o Rio de Janeiro, filtra Campos dos Goytacazes
# e gera denominadores exploratórios de força de trabalho por ocupação e ano.
#
# Funções microdatasus disponíveis para CNES:
#   CNES-LT (leitos), CNES-ST (estabelecimentos), CNES-DC (dados complementares),
#   CNES-EQ (equipamentos), CNES-SR (serviço especializado), CNES-HB (habilitação),
#   CNES-PF (profissionais), CNES-EP (equipes), CNES-RC (regra contratual),
#   CNES-IN (incentivos), CNES-EE (estabelecimento ensino),
#   CNES-EF (estabelecimento filantrópico), CNES-GM (gestão e metas)
#
# Uso: Rscript scripts/pipeline/10_denominadores_cnes.R

library(microdatasus)

# ========== CONFIGURAÇÃO ==========
MUN_COD <- "330100"   # Campos dos Goytacazes
UF <- "RJ"
ANOS <- 2018:2025
MES_COMPETENCIA <- 12  # dezembro de cada ano (estoque)

# Mapeamento CBO 2002 (família de 4 dígitos) -> categoria do estudo
classifica_cbo <- function(cbo) {
  fam <- substr(cbo, 1, 4)
  switch(
    fam,
    "2235" = list(universo = "principal", categoria = "Enfermagem – enfermeiros"),
    "3222" = list(universo = "principal", categoria = "Enfermagem – técnicos e auxiliares"),
    "2251" = list(universo = "principal", categoria = "Medicina"),
    "2252" = list(universo = "principal", categoria = "Medicina"),
    "2253" = list(universo = "principal", categoria = "Medicina"),
    "2231" = list(universo = "principal", categoria = "Medicina"),
    "2236" = list(universo = "principal", categoria = "Fisioterapia"),
    "2234" = list(universo = "principal", categoria = "Farmácia"),
    "3251" = list(universo = "principal", categoria = "Farmácia – técnicos e auxiliares"),
    "2237" = list(universo = "principal", categoria = "Nutrição"),
    "2238" = list(universo = "principal", categoria = "Fonoaudiologia"),
    "2232" = list(universo = "principal", categoria = "Odontologia e saúde bucal"),
    "3224" = list(universo = "principal", categoria = "Odontologia e saúde bucal"),
    "3241" = list(universo = "principal", categoria = "Diagnóstico e laboratório – técnicos e auxiliares"),
    "3242" = list(universo = "principal", categoria = "Diagnóstico e laboratório – técnicos e auxiliares"),
    "5151" = list(universo = "principal", categoria = "Agentes comunitários de saúde e afins"),
    "3226" = list(universo = "principal", categoria = "Instrumentação cirúrgica"),
    "5152" = list(universo = "principal", categoria = "Diagnóstico e laboratório – técnicos e auxiliares"),
    "2515" = list(universo = "multiprofissional", categoria = "Psicologia"),
    "2516" = list(universo = "multiprofissional", categoria = "Serviço social"),
    "2241" = list(universo = "multiprofissional", categoria = "Educação física"),
    "2211" = list(universo = "multiprofissional", categoria = "Biologia"),
    "2212" = list(universo = "multiprofissional", categoria = "Biomedicina"),
    list(universo = "apoio_ou_outra", categoria = NA)
  )
}

# ========== DOWNLOAD E PROCESSAMENTO ==========
resultados <- list()

for (ano in ANOS) {
  cat(sprintf("\n=== CNES-PF %d ========================================\n", ano))
  
  tryCatch({
    # Baixar CNES-PF para o estado do RJ, competência de dezembro
    df <- fetch_datasus(
      year_start = ano, year_end = ano,
      month_start = MES_COMPETENCIA, month_end = MES_COMPETENCIA,
      uf = UF,
      information_system = "CNES-PF"
    )
    cat(sprintf("  Total CNES-PF RJ: %d registros\n", nrow(df)))
    
    # Filtrar Campos dos Goytacazes (CODUFMUN começa com 330100)
    df_campos <- subset(df, substr(CODUFMUN, 1, 6) == MUN_COD)
    cat(sprintf("  Campos dos Goytacazes: %d registros\n", nrow(df_campos)))
    
    # Classificar por CBO
    df_campos$cbo_fam <- substr(df_campos$CBO, 1, 4)
    
    # Contar profissionais por CBO
    contagem <- as.data.frame(table(df_campos$CBO))
    names(contagem) <- c("cbo_codigo", "n_profissionais")
    contagem$ano <- ano
    contagem$competencia <- sprintf("%d-%02d", ano, MES_COMPETENCIA)
    
    # Classificar cada CBO
    contagem$universo <- NA
    contagem$categoria_estudo <- NA
    for (i in 1:nrow(contagem)) {
      cls <- classifica_cbo(contagem$cbo_codigo[i])
      contagem$universo[i] <- cls$universo
      contagem$categoria_estudo[i] <- cls$categoria
    }
    
    resultados[[as.character(ano)]] <- contagem
    cat(sprintf("  Total profissionais em Campos: %d\n", sum(contagem$n_profissionais)))
    
  }, error = function(e) {
    cat(sprintf("  ERRO: %s\n", e$message))
  })
}

# ========== CONSOLIDAR E SALVAR ==========
if (length(resultados) > 0) {
  consolidado <- do.call(rbind, resultados)
  
  # Salvar CSV completo
  dir.create("cnes", showWarnings = FALSE, recursive = TRUE)
  write.csv(consolidado, "cnes/cnes_profissionais_campos_microdatasus.csv",
            row.names = FALSE, fileEncoding = "UTF-8")
  
  # Salvar sumário por ano
  dir.create("saidas/tabelas", showWarnings = FALSE, recursive = TRUE)
  
  # Tabela T21: denominadores CNES
  t21 <- aggregate(n_profissionais ~ ano + categoria_estudo,
                   data = subset(consolidado, !is.na(categoria_estudo)),
                   FUN = sum)
  write.csv(t21, "saidas/tabelas/T21_denominadores_cnes.csv",
            row.names = FALSE, fileEncoding = "UTF-8")
  
  # Log
  log <- list(
    fonte = "CNES-PF via microdatasus (R)",
    periodo = paste(min(ANOS), max(ANOS), sep = "-"),
    municipio = "Campos dos Goytacazes (330100)",
    competencia = "dezembro de cada ano",
    total_profissionais = sum(consolidado$n_profissionais),
    execucao = as.character(Sys.time())
  )
  
  dir.create("logs", showWarnings = FALSE, recursive = TRUE)
  jsonlite::write_json(log, "logs/log_10_cnes_microdatasus.json", auto_unbox = TRUE)
  
  cat("\n========================================\n")
  cat(sprintf("Total profissionais consolidados: %d\n", sum(consolidado$n_profissionais)))
  cat("Arquivos gerados:\n")
  cat("  cnes/cnes_profissionais_campos_microdatasus.csv\n")
  cat("  saidas/tabelas/T21_denominadores_cnes.csv\n")
  cat("  logs/log_10_cnes_microdatasus.json\n")
} else {
  cat("\nNenhum dado processado.\n")
}
