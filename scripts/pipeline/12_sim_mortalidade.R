# 12_sim_mortalidade.R — Pipeline SIM via microdatasus
# Baixa dados do SIM-DO para Campos dos Goytacazes (330100)
cat("R versao:", paste(R.version$major, R.version$minor, sep="."), "\n")

# Instalar dependencias
if (!require("remotes", quietly=TRUE)) {
  install.packages("remotes", repos="https://cloud.r-project.org")
}

# Instalar read.dbc do CRAN
if (!require("read.dbc", quietly=TRUE)) {
  install.packages("read.dbc", repos="https://cloud.r-project.org")
}

# Instalar microdatasus do GitHub
if (!require("microdatasus", quietly=TRUE)) {
  remotes::install_github("rfsaldanha/microdatasus", upgrade="never")
}

library(microdatasus)
cat("microdatasus carregado:", as.character(packageVersion("microdatasus")), "\n")

# Baixar SIM-DO para RJ, 2019-2024
for (ano in 2019:2024) {
  cat(sprintf("\n=== SIM %d ===\n", ano))
  tryCatch({
    df <- fetch_datasus(
      year_start = ano, year_end = ano,
      uf = "RJ", information_system = "SIM-DO"
    )
    cat(sprintf("Total de obitos no RJ: %d\n", nrow(df)))
    
    # Filtrar Campos dos Goytacazes
    df_campos <- subset(df, CODMUNRES == "330100")
    cat(sprintf("Campos dos Goytacazes: %d obitos\n", nrow(df_campos)))
    
    # Salvar
    write.csv(df_campos, 
              sprintf("sim/SIM_Campos_%d.csv", ano),
              row.names = FALSE)
  }, error = function(e) {
    cat(sprintf("ERRO: %s\n", e$message))
  })
}

cat("\nConcluido!\n")
