# =====================================================================
# CÓPIA AUDITADA E COMENTADA — NÃO EXECUTAR COMO FONTE DE RESULTADOS
# Original: 'CAT - INSS/script.R' -> scripts/legado/CAT-INSS_script_original.R (preservado em scripts/legado/*_original.R)
# Auditoria: 2026-07-18 | Ver logs/log_alteracoes_scripts.csv
# ---------------------------------------------------------------------
# ACHADOS PRINCIPAIS (marcadores [A1]...[A8] ao longo do código):
# [A1] CRÍTICO  escopo restrito a Enfermagem/Medicina -> perde 166 CATs de
#      outras 10 categorias da saúde (14,5% do universo principal atual).
# [A2] CRÍTICO  ausência de deduplicação ENTRE arquivos sobrepostos
#      (202201/202204; 202207-202211; 202404/202405; 202506-202510):
#      537 duplicidades no recorte Campos+RJ (5.603 -> 5.066).
# [A3] ALTO     classificar_profissao() usa descrição textual ('enferm',
#      'medic'): incluiria CBO 519305 'Auxiliar de veterinário' (sinônimo
#      'enfermeiro veterinário' na fonte) como Enfermagem.
# [A4] MODERADO filtro_campos aceita código OU nome, sem validar UF do
#      empregador: 12 registros 330100 com UF≠RJ entrariam na base.
# [A5] MODERADO fread(encoding='Latin-1') aplicado a TODOS os arquivos,
#      mas 3 arquivos de 2020 são UTF-8-BOM -> mojibake tratado depois por
#      substituições manuais (corrigir_rotulo_cat), sintoma do erro de leitura.
# [A6] MODERADO cabeçalhos duplicados renomeados por make.unique/janitor e
#      coalescidos por regex de NOMES; posições variam entre 4 esquemas
#      (24A/24B/25/27) -> risco de troca competência x data completa.
# [A7] BAIXO    idades fora de [14,100] anuladas sem log (0 casos em Campos).
# [A8] BAIXO    qui-quadrado sobre dados de notificação sem denominador:
#      risco de leitura de frequência como risco. Não replicado.
# CORREÇÕES adotadas no pipeline novo: scripts_auditados/pipeline_reproducao/
# =====================================================================

# ============================================================
# ANALISE CAT/INSS - CAMPOS DOS GOYTACAZES
# Enfermagem x Medicina
#
# Entrada:
#   - CSVs brutos em DADOS/
#   - dicionario-cat-dados-abertos-10-02-2021.xlsx
#
# Saida:
#   - RESULTADOS/execucao_YYYYMMDD_HHMMSS/
#     - tabelas/
#     - graficos/
#     - auditoria/
#     - relatorios/
#
# Nota metodologica:
#   A cidade disponivel nos arquivos e "Munic Empr" (municipio do
#   empregador), conforme o dicionario. Portanto, o filtro de Campos dos
#   Goytacazes e aplicado ao municipio do empregador.
# ============================================================

# ---- 0. Dependencias --------------------------------------------------------

pacotes <- c(
  "data.table", "dplyr", "tidyr", "stringr", "stringi", "lubridate",
  "ggplot2", "scales", "purrr", "jsonlite", "writexl", "readxl", "janitor",
  "forcats"
)

instalar_se_ausente <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

invisible(lapply(pacotes, instalar_se_ausente))
suppressPackageStartupMessages(invisible(lapply(pacotes, library, character.only = TRUE)))

options(
  dplyr.summarise.inform = FALSE,
  readr.show_col_types = FALSE,
  scipen = 999,
  stringsAsFactors = FALSE
)

# ---- 1. Configuracao --------------------------------------------------------

DIR_BASE <- getwd()
DIR_DADOS <- file.path(DIR_BASE, "DADOS")
ARQUIVO_DICIONARIO <- file.path(DIR_BASE, "dicionario-cat-dados-abertos-10-02-2021.xlsx")

SESSAO_ID <- format(Sys.time(), "%Y%m%d_%H%M%S")
DIR_RESULTADOS <- file.path(DIR_BASE, "RESULTADOS", paste0("execucao_", SESSAO_ID))
DIR_TABELAS <- file.path(DIR_RESULTADOS, "tabelas")
DIR_GRAFICOS <- file.path(DIR_RESULTADOS, "graficos")
DIR_DADOS_GRAFICOS <- file.path(DIR_RESULTADOS, "dados_graficos")
DIR_AUDITORIA <- file.path(DIR_RESULTADOS, "auditoria")
DIR_RELATORIOS <- file.path(DIR_RESULTADOS, "relatorios")

purrr::walk(
  c(DIR_RESULTADOS, DIR_TABELAS, DIR_GRAFICOS, DIR_DADOS_GRAFICOS, DIR_AUDITORIA, DIR_RELATORIOS),
  ~ dir.create(.x, recursive = TRUE, showWarnings = FALSE)
)

ARQUIVO_LOG_JSON <- file.path(DIR_AUDITORIA, "auditoria_completa.json")
ARQUIVO_LOG_TXT <- file.path(DIR_RELATORIOS, "relatorio_metodologico.txt")
ARQUIVO_MANIFESTO <- file.path(DIR_RESULTADOS, "manifesto_arquivos.csv")

CODIGO_CAMPOS <- "330100"
NOME_CAMPOS <- "Campos dos Goytacazes"
DATA_HOJE <- Sys.Date()

log_global <- list(
  sessao = SESSAO_ID,
  timestamp_inicio = as.character(Sys.time()),
  diretorio_base = DIR_BASE,
  diretorio_dados = DIR_DADOS,
  arquivo_dicionario = ARQUIVO_DICIONARIO,
  filtro_municipio = list(
    campo_usado = "Munic Empr",
    codigo = CODIGO_CAMPOS,
    nome = NOME_CAMPOS
  ),
  estagios = list()
)

registrar <- function(estagio, metricas = list(), alertas = character(0)) {
  log_global$estagios[[estagio]] <<- list(
    timestamp = as.character(Sys.time()),
    metricas = metricas,
    alertas = alertas
  )
  cat("\n[", estagio, "]\n", sep = "")
  if (length(metricas) > 0) {
    for (nm in names(metricas)) cat("  - ", nm, ": ", metricas[[nm]], "\n", sep = "")
  }
  if (length(alertas) > 0) cat(paste0("  ! ", alertas, collapse = "\n"), "\n")
}

salvar_log <- function() {
  log_global$timestamp_fim <<- as.character(Sys.time())
  jsonlite::write_json(log_global, ARQUIVO_LOG_JSON, pretty = TRUE, auto_unbox = TRUE, null = "null")
}

# ---- 2. Funcoes utilitarias -------------------------------------------------

na_tokens <- c(
  "", "NA", "N/A", "NULL", "null", "NaN", "nan",
  "Nao Informado", "Nao informado", "Não Informado", "Não informado",
  "{ñ class}", "{n class}", "{na class}", "{Ã± class}",
  "0000/00", "00/00/0000", "0000-00-00"
)

sem_info <- "Não informado"

limpar_texto <- function(x) {
  x <- as.character(x)
  x <- stringr::str_squish(x)
  x[x %in% na_tokens] <- NA_character_
  x
}

normalizar_texto <- function(x) {
  x <- limpar_texto(x)
  x <- stringi::stri_trans_general(x, "Latin-ASCII")
  stringr::str_to_lower(x)
}

coalesce_chr <- function(df, cols) {
  cols <- intersect(cols, names(df))
  if (length(cols) == 0) return(rep(NA_character_, nrow(df)))
  out <- limpar_texto(df[[cols[1]]])
  if (length(cols) > 1) {
    for (col in cols[-1]) out <- dplyr::coalesce(out, limpar_texto(df[[col]]))
  }
  out
}

coalesce_reverse_chr <- function(df, cols) {
  coalesce_chr(df, rev(intersect(cols, names(df))))
}

cols_match <- function(df, padrao) {
  names(df)[stringr::str_detect(names(df), padrao)]
}

extrair_ano_arquivo <- function(path) {
  nome <- basename(path)
  ano <- stringr::str_extract(nome, "20[0-9]{2}")
  suppressWarnings(as.integer(ano))
}

extrair_competencia_arquivo <- function(path) {
  nome <- basename(path)
  comp <- stringr::str_extract(nome, "20[0-9]{4}")
  ifelse(is.na(comp), NA_character_, paste0(substr(comp, 1, 4), "-", substr(comp, 5, 6)))
}

parse_data_completa <- function(x) {
  x <- limpar_texto(x)
  x[!stringr::str_detect(x, "^\\d{2}/\\d{2}/\\d{4}$|^\\d{4}-\\d{2}-\\d{2}$|^\\d{4}/\\d{2}/\\d{2}$")] <- NA_character_
  dplyr::coalesce(
    suppressWarnings(lubridate::dmy(x)),
    suppressWarnings(lubridate::ymd(x))
  )
}

parse_competencia <- function(x) {
  x <- limpar_texto(x)
  x <- stringr::str_replace_all(x, "/", "-")
  out <- suppressWarnings(lubridate::ym(x))
  format(out, "%Y-%m")
}

canonizar_data_acidente <- function(df) {
  data_cols <- cols_match(df, "^data_acidente")
  if (length(data_cols) == 0) {
    return(list(
      data = as.Date(rep(NA, nrow(df)), origin = "1970-01-01"),
      coluna = NA_character_,
      competencia = rep(NA_character_, nrow(df))
    ))
  }

  datas <- lapply(rev(data_cols), function(col) parse_data_completa(df[[col]]))
  data_final <- datas[[1]]
  coluna_origem <- rep(rev(data_cols)[1], nrow(df))

  if (length(datas) > 1) {
    for (i in seq_along(datas)[-1]) {
      faltante <- is.na(data_final) & !is.na(datas[[i]])
      data_final[faltante] <- datas[[i]][faltante]
      coluna_origem[faltante] <- rev(data_cols)[i]
    }
  }

  competencia <- coalesce_chr(df, data_cols)
  competencia <- parse_competencia(competencia)
  list(data = data_final, coluna = coluna_origem, competencia = competencia)
}

extrair_codigo <- function(x) {
  stringr::str_extract(limpar_texto(x), "[0-9]{4,6}")
}

extrair_descricao_codigo <- function(x) {
  x <- limpar_texto(x)
  desc <- stringr::str_replace(x, "^[0-9]{4,6}\\s*-\\s*", "")
  desc[stringr::str_detect(desc, "^[0-9]{4,6}$")] <- NA_character_
  desc[desc == x & !stringr::str_detect(x, "-")] <- NA_character_
  desc <- stringr::str_squish(desc)
  desc[desc == ""] <- NA_character_
  desc
}

classificar_profissao <- function(cbo_codigo, cbo_descricao) {
  desc_norm <- normalizar_texto(cbo_descricao)
  familia4 <- stringr::str_sub(cbo_codigo, 1, 4)
  familia3 <- stringr::str_sub(cbo_codigo, 1, 3)

  dplyr::case_when(
    familia4 %in% c("2235", "3222") | stringr::str_detect(desc_norm, "enferm") ~ "Enfermagem",
    familia3 == "225" | (stringr::str_detect(desc_norm, "medic") & !stringr::str_detect(desc_norm, "veterin")) ~ "Medicina",
      TRUE ~ NA_character_
  )
}

rotular_ocupacao <- function(cbo_codigo, cbo_descricao) {
  mapa <- c(
    "223505" = "Enfermeiro",
    "223510" = "Enfermeiro auditor",
    "223515" = "Enfermeiro de centro cirurgico",
    "223520" = "Enfermeiro de terapia intensiva",
    "223525" = "Enfermeiro do trabalho",
    "223530" = "Enfermeiro nefrologista",
    "223535" = "Enfermeiro neonatologista",
    "223540" = "Enfermeiro obstetrico",
    "223545" = "Enfermeiro psiquiatrico",
    "223550" = "Enfermeiro puericultor e pediatrico",
    "223555" = "Enfermeiro sanitarista",
    "322205" = "Técnico de enfermagem",
    "322210" = "Técnico de enfermagem de terapia intensiva",
    "322215" = "Técnico de enfermagem do trabalho",
    "322220" = "Técnico de enfermagem psiquiátrica",
    "322225" = "Instrumentador cirúrgico",
    "322230" = "Auxiliar de enfermagem",
    "322235" = "Auxiliar de enfermagem do trabalho",
    "322240" = "Auxiliar de saúde",
    "322245" = "Técnico de enfermagem da ESF",
    "322250" = "Auxiliar de enfermagem da ESF",
    "225105" = "Médico acupunturista",
    "225110" = "Médico alergista e imunologista",
    "225115" = "Médico angiologista",
    "225120" = "Médico cardiologista",
    "225125" = "Médico clínico",
    "225130" = "Médico de família e comunidade",
    "225135" = "Médico dermatologista",
    "225140" = "Médico do trabalho",
    "225145" = "Médico em medicina de tráfego",
    "225150" = "Médico endocrinologista",
    "225155" = "Médico fisiatra",
    "225160" = "Médico gastroenterologista",
    "225165" = "Médico geriatra",
    "225170" = "Médico generalista",
    "225175" = "Médico geneticista",
    "225180" = "Médico hematologista",
    "225185" = "Médico hemoterapeuta",
    "225195" = "Médico homeopata",
    "225203" = "Médico em cirurgia vascular",
    "225210" = "Médico cirurgião cardiovascular",
    "225215" = "Médico cirurgião de cabeça e pescoço",
    "225220" = "Médico cirurgião do aparelho digestivo",
    "225225" = "Médico cirurgião geral",
    "225230" = "Médico cirurgião pediátrico",
    "225235" = "Médico cirurgião plástico",
    "225240" = "Médico cirurgião torácico",
    "225250" = "Médico ginecologista e obstetra",
    "225255" = "Médico mastologista",
    "225260" = "Médico neurocirurgião",
    "225265" = "Médico oftalmologista",
    "225270" = "Médico ortopedista e traumatologista",
    "225275" = "Médico otorrinolaringologista",
    "225280" = "Médico coloproctologista",
    "225285" = "Médico urologista",
    "225290" = "Médico cancerologista cirúrgico",
    "225295" = "Médico cirurgião da mão",
    "225305" = "Médico citopatologista",
    "225310" = "Médico em endoscopia",
    "225315" = "Médico patologista",
    "225320" = "Médico patologista clínico",
    "225325" = "Médico radiologista",
    "225330" = "Médico radioterapeuta",
    "225335" = "Médico em medicina nuclear",
    "225340" = "Médico anatomopatologista",
    "225345" = "Médico em medicina intensiva",
    "225350" = "Médico neurofisiologista",
    "225355" = "Médico radiologista intervencionista",
    "225365" = "Médico emergencista"
  )

  saida <- unname(mapa[cbo_codigo])
  dplyr::coalesce(saida, cbo_descricao, paste("CBO", cbo_codigo))
}

calcular_idade <- function(data_nascimento, data_evento) {
  idade <- floor(as.numeric(difftime(data_evento, data_nascimento, units = "days")) / 365.25)
  idade[idade < 14 | idade > 100] <- NA_real_
  idade
}

parse_data_nascimento <- function(x) {
  x <- limpar_texto(x)
  dplyr::coalesce(
    suppressWarnings(lubridate::dmy(x)),
    suppressWarnings(lubridate::ymd(x))
  )
}

salvar_grafico <- function(g, nome, width = 10, height = 6) {
  png_path <- file.path(DIR_GRAFICOS, paste0(nome, ".png"))
  ggplot2::ggsave(png_path, g, width = width, height = height, dpi = 300, bg = "white")
  tibble::tibble(arquivo = png_path, tipo = "grafico_png")
}

tema_cat <- function(base_size = 12) {
  ggplot2::theme_classic(base_size = base_size) +
    ggplot2::theme(
      plot.title = element_text(face = "bold", size = base_size + 3, color = "#303030"),
      plot.subtitle = element_text(color = "#4A4A4A", size = base_size),
      axis.text = element_text(color = "#303030"),
      axis.title = element_text(face = "bold", color = "#303030"),
      axis.line = element_line(color = "#4A4A4A", linewidth = 0.45),
      axis.ticks = element_line(color = "#4A4A4A", linewidth = 0.35),
      panel.grid.major.y = element_line(color = "#D8D8D8", linewidth = 0.35, linetype = "dashed"),
      panel.grid.major.x = element_blank(),
      panel.grid.minor = element_blank(),
      legend.position = "top",
      legend.justification = "right",
      legend.title = element_blank(),
      legend.background = element_rect(fill = "white", color = "#DDDDDD", linewidth = 0.35),
      legend.key = element_rect(fill = "white", color = NA),
      strip.background = element_rect(fill = "#F4F4F4", color = "#BDBDBD", linewidth = 0.35),
      strip.text = element_text(face = "bold", color = "#303030"),
      plot.margin = margin(10, 16, 10, 10)
    )
}

breaks_inteiros <- function(n = 5) {
  force(n)
  function(lims) {
    br <- pretty(lims, n = n)
    br <- unique(round(br))
    br[br >= lims[1] & br <= lims[2]]
  }
}

top_n_com_outros <- function(df, var, n = 10) {
  var <- rlang::ensym(var)
  principais <- df |>
    filter(!is.na(!!var)) |>
    count(!!var, sort = TRUE) |>
    slice_head(n = n) |>
    pull(!!var)
  df |>
    mutate(valor_top = if_else(!!var %in% principais, as.character(!!var), "Outros/menos frequentes"))
}

corrigir_rotulo_cat <- function(x) {
  x <- limpar_texto(x)
  x <- stringr::str_replace_all(x, fixed("TÃ­pico"), "Típico")
  x <- stringr::str_replace_all(x, fixed("DoenÃ§a"), "Doença")
  x <- stringr::str_replace_all(x, fixed("NÃ£o informado"), sem_info)
  x <- stringr::str_replace_all(x, fixed("NÃ£o Informado"), sem_info)
  x <- stringr::str_replace_all(x, fixed("Ã³"), "ó")
  x <- stringr::str_replace_all(x, fixed("Ãª"), "ê")
  x <- stringr::str_replace_all(x, fixed("Ã©"), "é")
  x <- stringr::str_replace_all(x, fixed("Ã¡"), "á")
  x <- stringr::str_replace_all(x, fixed("Ã£"), "ã")
  x <- stringr::str_replace_all(x, fixed("Ã§"), "ç")
  x <- stringr::str_replace_all(x, fixed("Ã­"), "í")
  x <- stringr::str_replace_all(x, fixed("Ãº"), "ú")
  x <- stringr::str_replace_all(x, regex("\\bMao\\b", ignore_case = FALSE), "Mão")
  x <- stringr::str_replace_all(x, regex("\\bPe\\b", ignore_case = FALSE), "Pé")
  x <- stringr::str_replace_all(x, regex("\\bCabeca\\b", ignore_case = FALSE), "Cabeça")
  x <- stringr::str_replace_all(x, regex("\\bArticulacao\\b", ignore_case = FALSE), "Articulação")
  x <- stringr::str_replace_all(x, regex("\\bOrgaos\\b", ignore_case = FALSE), "Órgãos")
  x <- stringr::str_replace_all(x, regex("\\bTorax\\b", ignore_case = FALSE), "Tórax")
  x <- stringr::str_replace_all(x, regex("\\bMusculos\\b", ignore_case = FALSE), "Músculos")
  x <- stringr::str_replace_all(x, regex("\\bVisao\\b", ignore_case = FALSE), "Visão")
  x <- stringr::str_replace_all(x, regex("\\bOtico\\b", ignore_case = FALSE), "Ótico")
  x <- stringr::str_replace_all(x, regex("\\bPescoco\\b", ignore_case = FALSE), "Pescoço")
  x <- stringr::str_replace_all(x, regex("\\bBraco\\b", ignore_case = FALSE), "Braço")
  x <- stringr::str_replace_all(x, regex("\\bAntebraco\\b", ignore_case = FALSE), "Antebraço")
  x <- stringr::str_replace_all(x, regex("\\bCoracao\\b", ignore_case = FALSE), "Coração")
  x <- stringr::str_replace_all(x, regex("\\bLesao\\b", ignore_case = FALSE), "Lesão")
  x <- stringr::str_replace_all(x, regex("\\bLesoes\\b", ignore_case = FALSE), "Lesões")
  x <- stringr::str_replace_all(x, regex("\\bContusao\\b", ignore_case = FALSE), "Contusão")
  x <- stringr::str_replace_all(x, regex("\\bLaceracao\\b", ignore_case = FALSE), "Laceração")
  x <- stringr::str_replace_all(x, regex("\\bPerfuracao\\b", ignore_case = FALSE), "Perfuração")
  x <- stringr::str_replace_all(x, regex("\\bLuxacao\\b", ignore_case = FALSE), "Luxação")
  x <- stringr::str_replace_all(x, regex("\\bDistensao\\b", ignore_case = FALSE), "Distensão")
  x <- stringr::str_replace_all(x, regex("\\bTorcao\\b", ignore_case = FALSE), "Torção")
  x <- stringr::str_replace_all(x, regex("\\bFratura\\b", ignore_case = FALSE), "Fratura")
  x <- stringr::str_replace_all(x, regex("\\bEsmagament\\b", ignore_case = FALSE), "Esmagamento")
  x <- stringr::str_replace_all(x, regex("\\bQuimic", ignore_case = FALSE), "Químic")
  x <- stringr::str_replace_all(x, regex("\\bFisic", ignore_case = FALSE), "Físic")
  x <- stringr::str_replace_all(x, regex("\\bNerv\\b", ignore_case = FALSE), "Nervo")
  x <- stringr::str_replace_all(x, regex("\\bNic\\b", ignore_case = FALSE), "NEC")
  x <- stringr::str_replace_all(x, regex("^Mão \\(Exceto Punho ou.*", ignore_case = FALSE), "Mão (exceto punho ou dedos)")
  x <- stringr::str_replace_all(x, regex("^Pé \\(Exceto Artelhos.*", ignore_case = FALSE), "Pé (exceto artelhos)")
  x <- stringr::str_replace_all(x, regex("^Olho \\(Inclusive Nervo.*", ignore_case = FALSE), "Olho (inclusive nervo ótico e visão)")
  x <- stringr::str_replace_all(x, regex("^Articulação do Torno.*", ignore_case = FALSE), "Articulação do tornozelo")
  x <- stringr::str_replace_all(x, regex("^Cabeça,.*", ignore_case = FALSE), "Cabeça")
  stringr::str_squish(x)
}

rotulo_grafico <- function(x) {
  y <- corrigir_rotulo_cat(x)
  y[is.na(y) | y == "" | y == "NA"] <- sem_info
  y
}

# ---- 3. Validacoes iniciais -------------------------------------------------

cat("\nPIPELINE CAT/INSS - CAMPOS DOS GOYTACAZES: ENFERMAGEM X MEDICINA\n")
cat("Sessao:", SESSAO_ID, "\n")

if (!dir.exists(DIR_DADOS)) stop("Subpasta DADOS nao encontrada: ", DIR_DADOS)
if (!file.exists(ARQUIVO_DICIONARIO)) stop("Dicionario nao encontrado: ", ARQUIVO_DICIONARIO)

arquivos_csv <- list.files(DIR_DADOS, pattern = "\\.csv$", full.names = TRUE)
arquivos_csv <- arquivos_csv[order(arquivos_csv)]
if (length(arquivos_csv) == 0) stop("Nenhum CSV encontrado em: ", DIR_DADOS)

dicionario <- readxl::read_excel(ARQUIVO_DICIONARIO)
data.table::fwrite(as.data.frame(dicionario), file.path(DIR_AUDITORIA, "dicionario_importado.csv"))

registrar(
  "validacao_inicial",
  list(
    arquivos_csv = length(arquivos_csv),
    dicionario_linhas = nrow(dicionario),
    pasta_resultados = DIR_RESULTADOS
  )
)

# ---- 4. Leitura, padronizacao e auditoria por arquivo -----------------------

ler_filtrar_arquivo <- function(path) {
  nome <- basename(path)
  tamanho_mb <- round(file.info(path)$size / 1024^2, 2)
  ano_arquivo <- extrair_ano_arquivo(path)
  competencia_arquivo <- extrair_competencia_arquivo(path)

  cat("\nLendo: ", nome, " (", tamanho_mb, " MB)\n", sep = "")

  erro <- NULL
  dt <- tryCatch(
    data.table::fread(
      path,
      sep = ";",
      encoding = "Latin-1",
      colClasses = "character",
      na.strings = na_tokens,
      fill = TRUE,
      quote = "",
      showProgress = FALSE
    ),
    error = function(e) {
      erro <<- conditionMessage(e)
      NULL
    }
  )

  if (is.null(dt)) {
    return(list(
      dados = tibble::tibble(),
      auditoria = tibble::tibble(
        arquivo = nome,
        status = "erro_leitura",
        erro = erro,
        tamanho_mb = tamanho_mb,
        ano_arquivo = ano_arquivo,
        competencia_arquivo = competencia_arquivo
      ),
      colunas = tibble::tibble(arquivo = nome, coluna_original = NA_character_, coluna_limpa = NA_character_)
    ))
  }

  nomes_originais <- names(dt)
  nomes_unicos <- make.unique(nomes_originais, sep = "_dup")
  nomes_limpos <- janitor::make_clean_names(nomes_unicos)
  names(dt) <- nomes_limpos
  df <- tibble::as_tibble(dt)
  rm(dt)
  gc(verbose = FALSE)

  data_info <- canonizar_data_acidente(df)
  cbo_cols <- cols_match(df, "^cbo")
  cid_cols <- cols_match(df, "^cid_10|^cid")
  cnae_cols <- cols_match(df, "^cnae2_0_empregador|^cnae")

  cbo_bruto <- coalesce_chr(df, cbo_cols)
  cbo_descritivo <- coalesce_reverse_chr(df, cbo_cols)
  cbo_codigo <- extrair_codigo(cbo_bruto)
  cbo_descricao <- extrair_descricao_codigo(cbo_descritivo)
  cbo_descricao <- dplyr::coalesce(cbo_descricao, extrair_descricao_codigo(cbo_bruto))
  profissao <- classificar_profissao(cbo_codigo, cbo_descricao)
  ocupacao <- rotular_ocupacao(cbo_codigo, cbo_descricao)

  municipio_empregador_raw <- coalesce_chr(df, cols_match(df, "^munic_empr|^municipio_empregador"))
  municipio_codigo <- stringr::str_extract(municipio_empregador_raw, "^[0-9]{6}")
  municipio_nome <- stringr::str_squish(stringr::str_remove(municipio_empregador_raw, "^[0-9]{6}\\s*-\\s*"))
  municipio_norm <- normalizar_texto(municipio_nome)

  filtro_campos <- municipio_codigo == CODIGO_CAMPOS |
    stringr::str_detect(municipio_norm, "campos dos goytacazes")
  filtro_profissao <- !is.na(profissao)
  filtro_final <- filtro_campos & filtro_profissao

  cid_bruto <- coalesce_chr(df, cid_cols)
  cid_descritivo <- coalesce_reverse_chr(df, cid_cols)
  cid_codigo <- stringr::str_extract(cid_bruto, "^[A-Z][0-9]{2}[0-9A-Z]?")
  cid_descricao <- extrair_descricao_codigo(cid_descritivo)
  cid_descricao <- dplyr::coalesce(cid_descricao, extrair_descricao_codigo(cid_bruto))

  cnae_bruto <- coalesce_chr(df, cnae_cols)
  cnae_descritivo <- coalesce_reverse_chr(df, cnae_cols)
  cnae_codigo <- extrair_codigo(cnae_bruto)
  cnae_descricao <- extrair_descricao_codigo(cnae_descritivo)
  cnae_descricao <- dplyr::coalesce(cnae_descricao, extrair_descricao_codigo(cnae_bruto))

  data_nascimento <- parse_data_nascimento(coalesce_chr(df, cols_match(df, "^data_nascimento")))
  idade <- calcular_idade(data_nascimento, data_info$data)

  obito <- coalesce_chr(df, cols_match(df, "^indica_obito_acidente|^indica_acidente"))
  obito_norm <- normalizar_texto(obito)
  obito_bin <- dplyr::case_when(
    stringr::str_detect(obito_norm, "^sim|^s$") ~ "Sim",
    stringr::str_detect(obito_norm, "^nao|^n$") ~ "Não",
    TRUE ~ NA_character_
  )

  dados_filtrados <- tibble::tibble(
    arquivo_origem = nome,
    ano_arquivo = ano_arquivo,
    competencia_arquivo = competencia_arquivo,
    competencia_registro = data_info$competencia,
    data_acidente = data_info$data,
    data_acidente_coluna_origem = data_info$coluna,
    ano_acidente = lubridate::year(data_info$data),
    mes_acidente = lubridate::floor_date(data_info$data, "month"),
    municipio_empregador_codigo = municipio_codigo,
    municipio_empregador = municipio_nome,
    cbo_codigo = cbo_codigo,
    cbo_descricao = cbo_descricao,
    ocupacao = ocupacao,
    profissao = profissao,
    cid_codigo = cid_codigo,
    cid_capitulo = stringr::str_sub(cid_codigo, 1, 1),
    cid_grupo = stringr::str_sub(cid_codigo, 1, 3),
    cid_descricao = cid_descricao,
    cnae_codigo = cnae_codigo,
    cnae_descricao = cnae_descricao,
    agente_causador = coalesce_chr(df, cols_match(df, "^agente_causador_acidente")),
    natureza_lesao = coalesce_chr(df, cols_match(df, "^natureza_da_lesao")),
    parte_corpo_atingida = coalesce_chr(df, cols_match(df, "^parte_corpo_atingida")),
    sexo = coalesce_chr(df, cols_match(df, "^sexo")),
    tipo_acidente = coalesce_chr(df, cols_match(df, "^tipo_do_acidente|^tipo_de_acidente")),
    emitente_cat = coalesce_chr(df, cols_match(df, "^emitente_cat|^emitente_da_cat")),
    especie_beneficio = coalesce_chr(df, cols_match(df, "^especie_do_beneficio|^esp$")),
    filiacao_segurado = coalesce_chr(df, cols_match(df, "^filiacao_segurado|^filiacao_do_segurado")),
    origem_cadastramento = coalesce_chr(df, cols_match(df, "^origem_de_cadastramento_cat|^origem_do_cadastramento")),
    uf_municipio_acidente = coalesce_chr(df, cols_match(df, "^uf_munic_acidente|^uf_municipio_do_acidente")),
    uf_municipio_empregador = coalesce_chr(df, cols_match(df, "^uf_munic_empregador|^uf_municipio_empregador")),
    data_nascimento = data_nascimento,
    idade = idade,
    faixa_etaria = cut(
      idade,
      breaks = c(14, 24, 34, 44, 54, 64, Inf),
      labels = c("15-24", "25-34", "35-44", "45-54", "55-64", "65+"),
      right = TRUE
    ),
    indica_obito = obito_bin
  ) |>
    filter(filtro_final)

  chave <- paste(
    dados_filtrados$data_acidente,
    dados_filtrados$data_nascimento,
    dados_filtrados$sexo,
    dados_filtrados$cbo_codigo,
    dados_filtrados$cid_codigo,
    dados_filtrados$municipio_empregador_codigo,
    sep = "|"
  )

  auditoria <- tibble::tibble(
    arquivo = nome,
    status = "ok",
    erro = NA_character_,
    tamanho_mb = tamanho_mb,
    ano_arquivo = ano_arquivo,
    competencia_arquivo = competencia_arquivo,
    linhas_lidas = nrow(df),
    colunas_lidas = ncol(df),
    colunas_duplicadas_no_cabecalho = sum(duplicated(nomes_originais)),
    linhas_campos = sum(filtro_campos, na.rm = TRUE),
    linhas_enfermagem_ou_medicina = sum(filtro_profissao, na.rm = TRUE),
    linhas_filtradas_final = nrow(dados_filtrados),
    linhas_enfermagem_campos = sum(dados_filtrados$profissao == "Enfermagem", na.rm = TRUE),
    linhas_medicina_campos = sum(dados_filtrados$profissao == "Medicina", na.rm = TRUE),
    cbo_ausente = sum(is.na(cbo_codigo)),
    municipio_ausente = sum(is.na(municipio_empregador_raw)),
    data_acidente_ausente_ou_invalida = sum(is.na(data_info$data)),
    data_acidente_futura = sum(data_info$data > DATA_HOJE, na.rm = TRUE),
    idade_invalida_ou_ausente_filtrado = sum(is.na(dados_filtrados$idade)),
    duplicidades_chave_filtrado = sum(duplicated(chave), na.rm = TRUE),
    anos_acidente_min = suppressWarnings(min(dados_filtrados$ano_acidente, na.rm = TRUE)),
    anos_acidente_max = suppressWarnings(max(dados_filtrados$ano_acidente, na.rm = TRUE))
  ) |>
    mutate(
      anos_acidente_min = ifelse(is.infinite(anos_acidente_min), NA, anos_acidente_min),
      anos_acidente_max = ifelse(is.infinite(anos_acidente_max), NA, anos_acidente_max)
    )

  colunas <- tibble::tibble(
    arquivo = nome,
    posicao = seq_along(nomes_originais),
    coluna_original = nomes_originais,
    coluna_limpa = nomes_limpos,
    duplicada_no_cabecalho = duplicated(nomes_originais) | duplicated(nomes_originais, fromLast = TRUE)
  )

  list(dados = dados_filtrados, auditoria = auditoria, colunas = colunas)
}

resultados_lista <- purrr::map(arquivos_csv, ler_filtrar_arquivo)

dados <- dplyr::bind_rows(purrr::map(resultados_lista, "dados"))
auditoria_arquivos <- dplyr::bind_rows(purrr::map(resultados_lista, "auditoria"))
auditoria_colunas <- dplyr::bind_rows(purrr::map(resultados_lista, "colunas"))

data.table::fwrite(auditoria_arquivos, file.path(DIR_AUDITORIA, "auditoria_por_arquivo.csv"))
data.table::fwrite(auditoria_colunas, file.path(DIR_AUDITORIA, "auditoria_colunas_por_arquivo.csv"))

registrar(
  "ingestao_e_filtros",
  list(
    linhas_lidas = sum(auditoria_arquivos$linhas_lidas, na.rm = TRUE),
    linhas_campos = sum(auditoria_arquivos$linhas_campos, na.rm = TRUE),
    linhas_enfermagem_medicina_campos = nrow(dados),
    enfermagem = sum(dados$profissao == "Enfermagem", na.rm = TRUE),
    medicina = sum(dados$profissao == "Medicina", na.rm = TRUE)
  ),
  alertas = c(
    if (any(auditoria_arquivos$status != "ok")) "Houve arquivo com erro de leitura; verificar auditoria_por_arquivo.csv." else character(0),
    if (nrow(dados) == 0) "Filtro final retornou zero registros." else character(0),
    if (sum(auditoria_arquivos$data_acidente_futura, na.rm = TRUE) > 0) "Existem datas futuras nos arquivos brutos." else character(0)
  )
)

if (nrow(dados) == 0) {
  salvar_log()
  stop("Nenhum registro encontrado para Campos dos Goytacazes + Enfermagem/Medicina.")
}

# ---- 5. Auditoria pesada da base filtrada ----------------------------------

dados <- dados |>
  mutate(
    sexo = forcats::fct_na_value_to_level(as.factor(sexo), level = sem_info) |> as.character(),
    tipo_acidente = forcats::fct_na_value_to_level(as.factor(tipo_acidente), level = sem_info) |> as.character(),
    natureza_lesao = forcats::fct_na_value_to_level(as.factor(natureza_lesao), level = sem_info) |> as.character(),
    parte_corpo_atingida = forcats::fct_na_value_to_level(as.factor(parte_corpo_atingida), level = sem_info) |> as.character(),
    indica_obito = forcats::fct_na_value_to_level(as.factor(indica_obito), level = sem_info) |> as.character(),
    chave_auditoria = paste(data_acidente, data_nascimento, sexo, cbo_codigo, cid_codigo, municipio_empregador_codigo, sep = "|"),
    duplicidade_chave = duplicated(chave_auditoria) | duplicated(chave_auditoria, fromLast = TRUE),
    alerta_data_vs_arquivo = !is.na(ano_acidente) & !is.na(ano_arquivo) & abs(ano_acidente - ano_arquivo) > 1
  )

auditoria_qualidade <- tibble::tibble(
  indicador = c(
    "registros_filtrados",
    "arquivos_com_registro_filtrado",
    "periodo_min_data_acidente",
    "periodo_max_data_acidente",
    "cbo_ausente",
    "cid_ausente",
    "idade_ausente_ou_invalida",
    "sexo_não_informado",
    "tipo_acidente_não_informado",
    "óbito_não_informado",
    "duplicidades_por_chave",
    "alertas_data_vs_arquivo"
  ),
  valor = c(
    nrow(dados),
    dplyr::n_distinct(dados$arquivo_origem),
    as.character(min(dados$data_acidente, na.rm = TRUE)),
    as.character(max(dados$data_acidente, na.rm = TRUE)),
    sum(is.na(dados$cbo_codigo)),
    sum(is.na(dados$cid_codigo)),
    sum(is.na(dados$idade)),
    sum(dados$sexo == sem_info, na.rm = TRUE),
    sum(dados$tipo_acidente == sem_info, na.rm = TRUE),
    sum(dados$indica_obito == sem_info, na.rm = TRUE),
    sum(dados$duplicidade_chave, na.rm = TRUE),
    sum(dados$alerta_data_vs_arquivo, na.rm = TRUE)
  )
)

auditoria_profissao_ano <- dados |>
  count(ano_acidente, profissao, name = "n") |>
  tidyr::complete(ano_acidente, profissao, fill = list(n = 0)) |>
  arrange(ano_acidente, profissao)

auditoria_perdas <- auditoria_arquivos |>
  transmute(
    arquivo,
    linhas_lidas,
    linhas_campos,
    linhas_enfermagem_ou_medicina,
    linhas_filtradas_final,
    perda_fora_campos = linhas_lidas - linhas_campos,
    perda_profissoes_fora_alvo_em_campos = linhas_campos - linhas_filtradas_final,
    prop_filtrada_pct = 100 * linhas_filtradas_final / pmax(linhas_lidas, 1)
  )

data.table::fwrite(auditoria_qualidade, file.path(DIR_AUDITORIA, "auditoria_qualidade_base_filtrada.csv"))
data.table::fwrite(auditoria_profissao_ano, file.path(DIR_AUDITORIA, "auditoria_profissao_por_ano.csv"))
data.table::fwrite(auditoria_perdas, file.path(DIR_AUDITORIA, "auditoria_perdas_por_filtro.csv"))

# ---- 6. Tabelas analiticas --------------------------------------------------

tabela_profissao <- dados |>
  count(profissao, name = "n") |>
  mutate(prop_pct = 100 * n / sum(n)) |>
  arrange(desc(n))

tabela_ocupacao <- dados |>
  count(profissao, cbo_codigo, ocupacao, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(profissao, desc(n))

tabela_ano <- dados |>
  count(ano_acidente, profissao, name = "n") |>
  group_by(ano_acidente) |>
  mutate(prop_ano_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(ano_acidente, profissao)

tabela_mes <- dados |>
  filter(!is.na(mes_acidente)) |>
  count(mes_acidente, profissao, name = "n") |>
  arrange(mes_acidente, profissao)

tabela_tipo <- dados |>
  count(profissao, tipo_acidente, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(profissao, desc(n))

tabela_sexo <- dados |>
  count(profissao, sexo, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup()

tabela_idade <- dados |>
  group_by(profissao) |>
  summarise(
    n = n(),
    idade_media = mean(idade, na.rm = TRUE),
    idade_mediana = median(idade, na.rm = TRUE),
    idade_p25 = quantile(idade, 0.25, na.rm = TRUE),
    idade_p75 = quantile(idade, 0.75, na.rm = TRUE),
    idade_ausente = sum(is.na(idade)),
    .groups = "drop"
  )

tabela_cid <- dados |>
  count(profissao, cid_grupo, cid_descricao, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(profissao, desc(n))

tabela_natureza <- dados |>
  count(profissao, natureza_lesao, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(profissao, desc(n))

tabela_parte_corpo <- dados |>
  count(profissao, parte_corpo_atingida, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup() |>
  arrange(profissao, desc(n))

tabela_obito <- dados |>
  count(profissao, indica_obito, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup()

data.table::fwrite(dados, file.path(DIR_TABELAS, "cat_campos_enfermagem_medicina.csv"))
data.table::fwrite(filter(dados, profissao == "Enfermagem"), file.path(DIR_TABELAS, "cat_campos_enfermagem.csv"))
data.table::fwrite(filter(dados, profissao == "Medicina"), file.path(DIR_TABELAS, "cat_campos_medicina.csv"))
data.table::fwrite(filter(dados, profissao == "Enfermagem"), file.path(DIR_TABELAS, "CATs_Campos_dos_Goytacazes_Enfermagem.csv"))
data.table::fwrite(filter(dados, profissao == "Medicina"), file.path(DIR_TABELAS, "CATs_Campos_dos_Goytacazes_Medicina.csv"))

tabelas_resumo <- list(
  profissao = tabela_profissao,
  ocupacao = tabela_ocupacao,
  ano = tabela_ano,
  mes = tabela_mes,
  tipo_acidente = tabela_tipo,
  sexo = tabela_sexo,
  idade = tabela_idade,
  cid = tabela_cid,
  natureza_lesao = tabela_natureza,
  parte_corpo = tabela_parte_corpo,
  obito = tabela_obito,
  auditoria_qualidade = auditoria_qualidade,
  auditoria_arquivos = auditoria_arquivos,
  auditoria_perdas = auditoria_perdas
)

writexl::write_xlsx(tabelas_resumo, file.path(DIR_TABELAS, "resumos_comparativos_e_auditoria.xlsx"))

purrr::iwalk(
  tabelas_resumo[setdiff(names(tabelas_resumo), c("auditoria_arquivos", "auditoria_perdas"))],
  ~ data.table::fwrite(.x, file.path(DIR_TABELAS, paste0("resumo_", .y, ".csv")))
)

registrar(
  "exportacao_tabelas",
  list(
    tabelas_csv = length(list.files(DIR_TABELAS, pattern = "\\.csv$")),
    arquivo_xlsx = "resumos_comparativos_e_auditoria.xlsx"
  )
)

# ---- 7. Graficos comparativos ----------------------------------------------

pal_prof <- c("Enfermagem" = "#FFB36F", "Medicina" = "#2C115F")
pal_prof_dark <- c("Enfermagem" = "#E85B5B", "Medicina" = "#7A1F86")
pal_multi <- c("#FFB36F", "#F35B5B", "#B83280", "#7A1F86", "#2C115F", "#009E73", "#56B4E9", "#E69F00")

graficos_manifesto <- list()

serie_mensal <- dados |>
  filter(!is.na(mes_acidente)) |>
  count(mes_acidente, profissao, name = "n") |>
  tidyr::complete(
    mes_acidente = seq(min(mes_acidente), max(mes_acidente), by = "month"),
    profissao = c("Enfermagem", "Medicina"),
    fill = list(n = 0)
  ) |>
  arrange(profissao, mes_acidente) |>
  group_by(profissao) |>
  mutate(media_movel_3m = as.numeric(stats::filter(n, rep(1 / 3, 3), sides = 1))) |>
  ungroup()
data.table::fwrite(serie_mensal, file.path(DIR_DADOS_GRAFICOS, "01_serie_mensal_cats.csv"))

g1 <- serie_mensal |>
  ggplot(aes(x = mes_acidente, y = n, fill = profissao)) +
  geom_col(width = 24, color = "white", linewidth = 0.15, alpha = 0.92) +
  geom_line(aes(y = media_movel_3m, color = profissao), linewidth = 0.9, na.rm = TRUE) +
  facet_wrap(~profissao, ncol = 1, scales = "free_y") +
  scale_fill_manual(values = pal_prof) +
  scale_color_manual(values = pal_prof_dark) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y", expand = expansion(mult = c(0.01, 0.02))) +
  scale_y_continuous(
    breaks = breaks_inteiros(5),
    labels = scales::label_number(big.mark = ".", decimal.mark = ",", accuracy = 1),
    expand = expansion(mult = c(0, 0.14))
  ) +
  labs(
    title = "Série mensal de CATs",
    subtitle = "Barras mensais e linha de média móvel de 3 meses",
    x = "Mês do acidente",
    y = "Registros"
  ) +
  tema_cat(13) +
  theme(legend.position = "none")
graficos_manifesto[[1]] <- salvar_grafico(g1, "01_serie_mensal_cats", width = 12, height = 7.5)

g2 <- tabela_tipo |>
  mutate(tipo_acidente = rotulo_grafico(tipo_acidente)) |>
  group_by(profissao, tipo_acidente) |>
  summarise(n = sum(n), .groups = "drop_last") |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  ungroup()
data.table::fwrite(g2, file.path(DIR_DADOS_GRAFICOS, "02_tipo_acidente_percentual.csv"))

g2 <- g2 |>
  ggplot(aes(x = profissao, y = prop_profissao_pct, fill = tipo_acidente)) +
  geom_col(width = 0.68, color = "white", linewidth = 0.5) +
  scale_fill_manual(values = pal_multi) +
  scale_y_continuous(labels = scales::label_percent(scale = 1), expand = expansion(mult = c(0, 0.10))) +
  labs(
    title = "Composição por tipo de acidente",
    subtitle = "Percentual dentro de cada profissão",
    x = NULL,
    y = "% dentro da profissão",
    fill = "Tipo"
  ) +
  tema_cat(13)
graficos_manifesto[[2]] <- salvar_grafico(g2, "02_tipo_acidente_percentual")

faixas_idade_ordem <- c("15-24", "25-34", "35-44", "45-54", "55-64", "65+", sem_info)
idade_abs <- dados |>
  mutate(
    faixa_etaria_grafico = as.character(faixa_etaria),
    faixa_etaria_grafico = if_else(is.na(faixa_etaria_grafico) | faixa_etaria_grafico == "", sem_info, faixa_etaria_grafico),
    faixa_etaria_grafico = factor(faixa_etaria_grafico, levels = faixas_idade_ordem)
  ) |>
  count(profissao, faixa_etaria_grafico, name = "n") |>
  tidyr::complete(profissao, faixa_etaria_grafico = factor(faixas_idade_ordem, levels = faixas_idade_ordem), fill = list(n = 0))
data.table::fwrite(idade_abs, file.path(DIR_DADOS_GRAFICOS, "03_faixa_etaria_absoluta.csv"))

g3 <- idade_abs |>
  filter(n > 0) |>
  ggplot(aes(x = faixa_etaria_grafico, y = n, fill = profissao)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.68, color = "white", linewidth = 0.45) +
  scale_fill_manual(values = pal_prof) +
  scale_y_log10(
    breaks = c(1, 2, 5, 10, 25, 50, 100, 250, 500),
    labels = scales::label_number(big.mark = ".", decimal.mark = ",", accuracy = 1),
    expand = expansion(mult = c(0, 0.12))
  ) +
  labs(
    title = "Registros por faixa etária",
    subtitle = "Números absolutos por profissão; eixo Y em escala log10",
    x = "Faixa etária",
    y = "Registros (escala log10)",
    fill = "Profissão"
  ) +
  tema_cat(13)
graficos_manifesto[[3]] <- salvar_grafico(g3, "03_faixa_etaria_absoluta")

g4 <- tabela_sexo |>
  mutate(sexo = if_else(is.na(sexo) | sexo == "", sem_info, sexo))
data.table::fwrite(g4, file.path(DIR_DADOS_GRAFICOS, "04_sexo_percentual.csv"))

g4 <- g4 |>
  ggplot(aes(x = sexo, y = prop_profissao_pct, fill = profissao)) +
  geom_col(position = position_dodge(width = 0.76), width = 0.66, color = "white", linewidth = 0.45) +
  scale_fill_manual(values = pal_prof) +
  scale_y_continuous(labels = scales::label_percent(scale = 1), expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Distribuição por sexo",
    subtitle = "Percentual dentro de cada profissão",
    x = "Sexo",
    y = "% dentro da profissão",
    fill = "Profissão"
  ) +
  tema_cat(13)
graficos_manifesto[[4]] <- salvar_grafico(g4, "04_sexo_percentual")

top_cid <- tabela_cid |>
  filter(!is.na(cid_grupo), cid_grupo != "", cid_grupo != "NA") |>
  group_by(profissao) |>
  slice_max(n, n = 8, with_ties = FALSE) |>
  ungroup() |>
  mutate(
    cid_descricao_grafico = if_else(is.na(cid_descricao) | cid_descricao == "" | cid_descricao == "NA", "", as.character(cid_descricao)),
    cid_rotulo = if_else(
      cid_descricao_grafico == "",
      cid_grupo,
      stringr::str_squish(paste(cid_grupo, cid_descricao_grafico, sep = " - "))
    ),
    cid_rotulo = stringr::str_wrap(cid_rotulo, width = 36),
    cid_rotulo = forcats::fct_reorder(cid_rotulo, n),
    n_log10 = log10(n + 1)
  )
data.table::fwrite(top_cid, file.path(DIR_DADOS_GRAFICOS, "05_top_cid10.csv"))

g5 <- top_cid |>
  ggplot(aes(x = n, y = cid_rotulo, fill = profissao)) +
  geom_col(width = 0.72, color = "white", linewidth = 0.45) +
  facet_wrap(~profissao, scales = "free") +
  scale_fill_manual(values = pal_prof) +
  scale_x_log10(
    breaks = c(1, 2, 5, 10, 25, 50, 100, 250, 500),
    labels = scales::label_number(big.mark = ".", decimal.mark = ",", accuracy = 1),
    expand = expansion(mult = c(0, 0.12))
  ) +
  labs(
    title = "Principais grupos CID-10",
    subtitle = "Top 8 dentro de cada profissão; eixo de registros em escala log10",
    x = "Registros (escala log10)",
    y = NULL,
    fill = "Profissão"
  ) +
  tema_cat(12) +
  theme(legend.position = "none")
graficos_manifesto[[5]] <- salvar_grafico(g5, "05_top_cid10", width = 11, height = 6.5)

top_natureza <- dados |>
  mutate(natureza_lesao_grafico = rotulo_grafico(natureza_lesao)) |>
  count(profissao, natureza_lesao_grafico, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  slice_max(n, n = 8, with_ties = FALSE) |>
  ungroup() |>
  mutate(
    natureza_rotulo = stringr::str_wrap(natureza_lesao_grafico, width = 34),
    natureza_rotulo = forcats::fct_reorder(natureza_rotulo, n)
  )
data.table::fwrite(top_natureza, file.path(DIR_DADOS_GRAFICOS, "06_top_natureza_lesao.csv"))

g6 <- top_natureza |>
  ggplot(aes(x = natureza_rotulo, y = prop_profissao_pct, fill = profissao)) +
  geom_col(width = 0.72, color = "white", linewidth = 0.45) +
  coord_flip() +
  facet_wrap(~profissao, scales = "free_y") +
  scale_fill_manual(values = pal_prof) +
  scale_y_continuous(labels = scales::label_percent(scale = 1), expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Natureza da lesão mais frequente",
    subtitle = "Top 8 por profissão, em percentual interno",
    x = NULL,
    y = "% dentro da profissão",
    fill = "Profissão"
  ) +
  tema_cat(12) +
  theme(legend.position = "none")
graficos_manifesto[[6]] <- salvar_grafico(g6, "06_top_natureza_lesao", width = 11, height = 6.5)

top_parte <- dados |>
  mutate(parte_corpo_grafico = rotulo_grafico(parte_corpo_atingida)) |>
  count(profissao, parte_corpo_grafico, name = "n") |>
  group_by(profissao) |>
  mutate(prop_profissao_pct = 100 * n / sum(n)) |>
  slice_max(n, n = 8, with_ties = FALSE) |>
  ungroup() |>
  mutate(
    parte_rotulo = stringr::str_wrap(parte_corpo_grafico, width = 34),
    parte_rotulo = forcats::fct_reorder(parte_rotulo, n)
  )
data.table::fwrite(top_parte, file.path(DIR_DADOS_GRAFICOS, "07_top_parte_corpo.csv"))

g7 <- top_parte |>
  ggplot(aes(x = parte_rotulo, y = prop_profissao_pct, fill = profissao)) +
  geom_col(width = 0.72, color = "white", linewidth = 0.45) +
  coord_flip() +
  facet_wrap(~profissao, scales = "free_y") +
  scale_fill_manual(values = pal_prof) +
  scale_y_continuous(labels = scales::label_percent(scale = 1), expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Parte do corpo atingida",
    subtitle = "Top 8 por profissão, em percentual interno",
    x = NULL,
    y = "% dentro da profissão",
    fill = "Profissão"
  ) +
  tema_cat(12) +
  theme(legend.position = "none")
graficos_manifesto[[7]] <- salvar_grafico(g7, "07_top_parte_corpo", width = 11, height = 6.5)

data.table::fwrite(dplyr::bind_rows(graficos_manifesto), file.path(DIR_GRAFICOS, "manifesto_graficos.csv"))

registrar(
  "graficos",
  list(graficos_png = length(list.files(DIR_GRAFICOS, pattern = "\\.png$")))
)

# ---- 8. Testes estatisticos descritivos ------------------------------------

teste_quiquadrado <- function(df, var) {
  var <- rlang::ensym(var)
  base <- df |>
    filter(!is.na(profissao), !is.na(!!var)) |>
    count(profissao, !!var, name = "n")
  tab <- xtabs(n ~ profissao + ., data = base)
  if (min(dim(tab)) < 2 || sum(tab) == 0) {
    return(tibble::tibble(variavel = rlang::as_string(var), qui_quadrado = NA_real_, gl = NA_real_, p_valor = NA_real_, n = sum(tab)))
  }
  teste <- suppressWarnings(chisq.test(tab, correct = FALSE))
  tibble::tibble(
    variavel = rlang::as_string(var),
    qui_quadrado = as.numeric(teste$statistic),
    gl = as.numeric(teste$parameter),
    p_valor = as.numeric(teste$p.value),
    n = sum(tab)
  )
}

testes_associacao <- bind_rows(
  teste_quiquadrado(dados, tipo_acidente),
  teste_quiquadrado(dados, sexo),
  teste_quiquadrado(dados, cid_grupo),
  teste_quiquadrado(dados, natureza_lesao),
  teste_quiquadrado(dados, parte_corpo_atingida),
  teste_quiquadrado(dados, indica_obito)
) |>
  mutate(
    p_formatado = case_when(
      is.na(p_valor) ~ "NA",
      p_valor < 0.001 ~ "<0,001",
      TRUE ~ formatC(p_valor, format = "f", digits = 3, decimal.mark = ",")
    )
  )

data.table::fwrite(testes_associacao, file.path(DIR_TABELAS, "testes_associacao_quiquadrado.csv"))

# ---- 9. Relatório metodológico ---------------------------------------------

linhas_relatorio <- c(
  "RELATÓRIO METODOLÓGICO - CAT/INSS",
  paste0("Sessão: ", SESSAO_ID),
  paste0("Gerado em: ", Sys.time()),
  "",
  "Escopo",
  paste0("- Município filtrado: ", NOME_CAMPOS, " (código ", CODIGO_CAMPOS, ")."),
  "- Campo usado para cidade: Munic Empr, isto é, município do empregador.",
  "- Profissões filtradas: Enfermagem e Medicina.",
  "- Enfermagem: famílias CBO 2235 e 3222, além de descrições contendo 'enferm'.",
  "- Medicina: família CBO 225, além de descrições médicas não veterinárias.",
  "",
  "Cobertura",
  paste0("- Arquivos CSV lidos: ", length(arquivos_csv), "."),
  paste0("- Linhas brutas lidas: ", scales::comma(sum(auditoria_arquivos$linhas_lidas, na.rm = TRUE), big.mark = ".", decimal.mark = ","), "."),
  paste0("- Registros finais: ", scales::comma(nrow(dados), big.mark = ".", decimal.mark = ","), "."),
  paste0("- Enfermagem: ", scales::comma(sum(dados$profissao == "Enfermagem"), big.mark = ".", decimal.mark = ","), "."),
  paste0("- Medicina: ", scales::comma(sum(dados$profissao == "Medicina"), big.mark = ".", decimal.mark = ","), "."),
  paste0("- Período observado: ", min(dados$data_acidente, na.rm = TRUE), " a ", max(dados$data_acidente, na.rm = TRUE), "."),
  "",
  "Auditoria de qualidade",
  paste0("- CBO ausente na base filtrada: ", sum(is.na(dados$cbo_codigo)), "."),
  paste0("- CID ausente na base filtrada: ", sum(is.na(dados$cid_codigo)), "."),
  paste0("- Idade ausente/inválida na base filtrada: ", sum(is.na(dados$idade)), "."),
  paste0("- Duplicidades por chave composta: ", sum(dados$duplicidade_chave, na.rm = TRUE), "."),
  paste0("- Alertas de data vs ano do arquivo: ", sum(dados$alerta_data_vs_arquivo, na.rm = TRUE), "."),
  "",
  "Arquivos principais",
  paste0("- Base completa filtrada: ", file.path(DIR_TABELAS, "cat_campos_enfermagem_medicina.csv")),
  paste0("- Base Enfermagem: ", file.path(DIR_TABELAS, "cat_campos_enfermagem.csv")),
  paste0("- Base Medicina: ", file.path(DIR_TABELAS, "cat_campos_medicina.csv")),
  paste0("- CATs Campos dos Goytacazes Enfermagem: ", file.path(DIR_TABELAS, "CATs_Campos_dos_Goytacazes_Enfermagem.csv")),
  paste0("- CATs Campos dos Goytacazes Medicina: ", file.path(DIR_TABELAS, "CATs_Campos_dos_Goytacazes_Medicina.csv")),
  paste0("- Auditoria por arquivo: ", file.path(DIR_AUDITORIA, "auditoria_por_arquivo.csv")),
  paste0("- Gráficos PNG: ", DIR_GRAFICOS),
  "",
  "Cuidado interpretativo",
  "- CAT é base de notificação; sem denominador populacional ou número de trabalhadores expostos, os resultados são frequências e proporções de registros, não incidência.",
  "- Mudanças no volume ao longo do tempo podem refletir notificação, cobertura administrativa, atraso de carga e alterações de layout, além de mudanças reais de risco."
)

writeLines(linhas_relatorio, ARQUIVO_LOG_TXT, useBytes = TRUE)

manifesto <- tibble::tibble(
  arquivo = list.files(DIR_RESULTADOS, recursive = TRUE, full.names = TRUE),
  tipo = tools::file_ext(arquivo),
  tamanho_kb = round(file.info(arquivo)$size / 1024, 2)
) |>
  arrange(arquivo)

data.table::fwrite(manifesto, ARQUIVO_MANIFESTO)
writeLines(DIR_RESULTADOS, file.path(DIR_BASE, "RESULTADOS", "ULTIMA_EXECUCAO.txt"), useBytes = TRUE)

registrar(
  "finalizacao",
  list(
    pasta_resultados = DIR_RESULTADOS,
    arquivos_gerados = nrow(manifesto),
    relatorio = ARQUIVO_LOG_TXT
  )
)

salvar_log()

cat("\nConcluido.\n")
cat("Resultados em: ", DIR_RESULTADOS, "\n", sep = "")
