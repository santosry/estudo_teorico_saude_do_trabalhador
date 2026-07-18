setwd("C:/Users/oorie/OneDrive/Documentos/TRABALHOS/CARACTERIZAÇÃO")

# ============================================================
# SIDRA/IBGE - Campos dos Goytacazes
# Código IBGE: 3301009
# ============================================================

pacotes <- c("sidrar", "dplyr", "readr", "purrr", "janitor", "tibble")

instalar <- pacotes[!pacotes %in% rownames(installed.packages())]
if (length(instalar) > 0) install.packages(instalar)

library(sidrar)
library(dplyr)
library(readr)
library(purrr)
library(janitor)
library(tibble)

municipio_ibge <- 3301009

dir.create("sidra_campos", showWarnings = FALSE)
dir.create("sidra_campos/brutos", showWarnings = FALSE)
dir.create("sidra_campos/logs", showWarnings = FALSE)

baixar_sidra_municipio <- function(tabela, periodo, nome_saida) {
  
  message("Baixando: ", nome_saida, " | Tabela: ", tabela)
  
  tryCatch({
    
    dados <- sidrar::get_sidra(
      x = as.numeric(tabela),
      variable = "allxp",
      period = periodo,
      geo = "City",
      geo.filter = list("City" = municipio_ibge)
    ) |>
      janitor::clean_names()
    
    readr::write_csv(
      dados,
      file.path("sidra_campos/brutos", paste0(nome_saida, ".csv"))
    )
    
    tibble(
      nome_saida = nome_saida,
      tabela = tabela,
      periodo = periodo,
      status = "baixado",
      linhas = nrow(dados),
      colunas = ncol(dados),
      erro = NA_character_
    )
    
  }, error = function(e) {
    
    tibble(
      nome_saida = nome_saida,
      tabela = tabela,
      periodo = periodo,
      status = "erro",
      linhas = 0L,
      colunas = 0L,
      erro = e$message
    )
  })
}

tabelas <- tibble::tribble(
  ~nome_saida, ~tabela, ~periodo,
  
  "populacao_area_densidade_censo_2022", "4714", "2022",
  "estimativas_populacionais", "6579", "all",
  "populacao_residente_censo_2022", "9605", "2022",
  "populacao_por_sexo_idade_2022", "9514", "2022",
  
  "pib_municipal", "5938", "all",
  "valor_adicionado_setores", "5939", "all",
  "pib_per_capita", "4709", "all",
  
  "producao_agricola_lavoura_temporaria", "1612", "all",
  "producao_agricola_lavoura_permanente", "1613", "all",
  "pecuaria_municipal_rebanhos", "3939", "all",
  "producao_origem_animal", "74", "all",
  "extracao_vegetal_silvicultura", "289", "all",
  
  "alfabetizacao_censo_2022", "9518", "2022",
  "instrucao_censo_2022", "9543", "2022",
  "rendimento_censo_2022", "9519", "2022",
  "trabalho_censo_2022", "9520", "2022",
  
  "domicilios_censo_2022", "9607", "2022",
  "abastecimento_agua_censo_2022", "9608", "2022",
  "esgotamento_sanitario_censo_2022", "9609", "2022",
  "destino_lixo_censo_2022", "9610", "2022",
  
  "populacao_cor_raca_censo_2022", "9606", "2022"
)

log_download <- purrr::pmap_dfr(
  tabelas,
  function(nome_saida, tabela, periodo) {
    baixar_sidra_municipio(
      tabela = tabela,
      periodo = periodo,
      nome_saida = nome_saida
    )
  }
)

readr::write_csv(
  log_download,
  "sidra_campos/logs/log_download_sidra.csv"
)

print(log_download)

arquivos <- list.files(
  "sidra_campos/brutos",
  pattern = "\\.csv$",
  full.names = TRUE
)

if (length(arquivos) > 0) {
  
  dados_sidra_campos <- arquivos |>
    setNames(tools::file_path_sans_ext(basename(arquivos))) |>
    purrr::map(readr::read_csv, show_col_types = FALSE)
  
  saveRDS(
    dados_sidra_campos,
    "sidra_campos/dados_sidra_campos_consolidado.rds"
  )
}

message("Finalizado. Verifique o arquivo: sidra_campos/logs/log_download_sidra.csv")

#juntar tabelas
library(readr)
library(dplyr)
library(purrr)
library(janitor)

arquivos <- list.files(
  "sidra_campos/brutos",
  pattern = "\\.csv$",
  full.names = TRUE
)

dados_unificados <- arquivos |>
  setNames(tools::file_path_sans_ext(basename(arquivos))) |>
  purrr::imap_dfr(function(caminho, nome_base) {
    
    readr::read_csv(caminho, show_col_types = FALSE) |>
      janitor::clean_names() |>
      mutate(
        base_sidra = nome_base,
        arquivo_origem = basename(caminho),
        .before = 1
      )
  })

readr::write_csv(
  dados_unificados,
  "sidra_campos/dados_sidra_campos_tabela_unica.csv"
)

message("Arquivo salvo em: sidra_campos/dados_sidra_campos_tabela_unica.csv")