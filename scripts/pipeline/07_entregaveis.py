# -*- coding: utf-8 -*-
"""
07_entregaveis.py — Gera entregáveis de documentação: inventário/manifesto XLSX,
dicionários, matriz teórica, referências ABNT, fluxo, logs de auditoria e README.
"""
import os, csv, sys, platform, datetime
import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
HOJE = "2026-07-18"

# 1) Inventário / manifesto -----------------------------------------------------
inv = pd.read_csv("dados/manifesto/manifesto_arquivos.csv", sep=";", dtype=str, encoding="utf-8-sig")
est = pd.read_csv("dados/processados/estatisticas_por_arquivo.csv", sep=";", dtype=str, encoding="utf-8-sig")
inv["nome_join"] = inv["nome"]
inv = inv.merge(est[["arquivo", "esquema", "linhas_malformadas"]], left_on="nome", right_on="arquivo", how="left").drop(columns=["arquivo", "nome_join"])
def condicao(row):
    p = row["caminho_relativo"]
    if "cat-inss" in p: return "bruto (fonte INSS/PDA)"
    if "sidra-campos" in p: return "bruto (fonte IBGE/SIDRA)"
    if "CBO2002" in p: return "tabela de validação CBO (espelho público)"
    if "dicionario-cat" in p: return "documentação da fonte (INSS)"
    if p.startswith("artigos-fonte"): return "material teórico (lido integralmente)"
    return "intermediário/derivado legado"
inv["condicao"] = inv.apply(condicao, axis=1)
inv["scripts_associados"] = inv["caminho_relativo"].map(
    lambda p: "scripts/pipeline 02–06; legado: scripts/legado/CAT-INSS_script_original.R" if "cat-inss" in p
    else ("legado: scripts/legado/CARACTERIZACAO_script_original.R" if "sidra" in p else ""))
inv.to_excel("dados/manifesto/manifesto_arquivos.xlsx", index=False)
inv.to_excel("metadados/inventario_arquivos.xlsx", index=False)

# 2) Dicionário de variáveis ----------------------------------------------------
dv = [
    ("id_linha", "Identificador técnico (arquivo:linha)", "criada", "—"),
    ("hash_registro", "SHA-256 da linha bruta original (com esquema)", "criada", "—"),
    ("arquivo_origem / esquema", "Arquivo CSV e esquema estrutural (S25, S24A, S24B, S27)", "criada", "—"),
    ("competencia_arquivo", "Competência declarada no nome do arquivo (AAAAMM)", "criada", "controle; não substitui a data do acidente"),
    ("mes_referencia_acidente_bruto", "Coluna 2 da fonte ('Data Acidente' em AAAA/MM, DD/MM/AAAA ou AAAAMM)", "posição 2", "usada apenas para consistência"),
    ("data_acidente / ano_acidente / mes_acidente", "Data completa do acidente (DD/MM/AAAA na fonte)", "posição 23 (S25/S27), 21 (S24A), 22 (S24B)", "base das análises temporais"),
    ("data_nascimento", "Data de nascimento", "posição 24 (S25), 22 (S24A), 23 (S24B), 24 (S27)", "7 registros inválidos/ausentes na base Campos"),
    ("idade", "Idade em anos completos na data do acidente", "derivada", "válida entre 14 e 100; fora => ausente com registro"),
    ("data_emissao_cat / tempo_acidente_emissao_dias", "Data de emissão da CAT e intervalo", "posição 25 (S25/S27), 23 (S24A); AUSENTE no esquema S24B (jun–out/2023)", "—"),
    ("municipio_empregador_codigo/nome", "Código (6 dígitos antes do hífen) e nome do município do EMPREGADOR", "posição 13 (S25/S27/S24B), 11 (S24A)", "filtro: 330100 + UF RJ"),
    ("uf_municipio_empregador", "UF do município do empregador", "posição 20 (S25/S27/S24B), 18 (S24A)", "—"),
    ("uf_municipio_acidente", "UF do município do acidente (alta proporção '{ñ class}')", "posição 19 (S25/S27/S24B), 17 (S24A)", "não usada no filtro"),
    ("cbo_codigo / cbo_descricao_original", "CBO 2002: código 6 dígitos; descrição da fonte (truncada em parte dos arquivos)", "posições 3-4; no S24A vêm combinados 'código-descrição'", "—"),
    ("cbo_titulo_oficial", "Título oficial CBO 2002 (tabela-espelho; ver referencias/fonte_cbo.txt)", "join", "—"),
    ("universo / categoria_profissional / nivel_formacao", "Classificação: principal | multiprofissional | nao_classificado | apoio_ou_outra", "derivadas do dicionário CBO", "—"),
    ("cid10_codigo/grupo3/descricao", "CID-10 do atestado", "posições 5-6 (combinadas no S24A)", "—"),
    ("cnae_classe / cnae_descricao / cnae_saude", "CNAE 2.0 (classe, 4 dígitos) do empregador; cnae_saude = divisão 86/87", "posições 7-8 (5-6 no S24A)", "—"),
    ("sexo, tipo_acidente, agente_causador, natureza_lesao, parte_corpo_atingida", "Características do evento (padronizadas; original preservado)", "posições conforme esquema", "tokens '{ñ class}', '0000/00' etc. => ausente"),
    ("emitente_cat, origem_cadastramento_cat, filiacao_segurado, especie_beneficio, indica_obito_acidente", "Características administrativas", "posições conforme esquema", "coluna 12 nomeada 'Indica acidente' em 2018–2020"),
    ("duplicata_interna_mesmo_arquivo", "Linha idêntica repetida dentro do mesmo arquivo (mantida e sinalizada)", "derivada", "4 registros na base candidata"),
]
pd.DataFrame(dv, columns=["variavel", "descricao", "origem_posicional", "observacao"]).to_excel("metadados/dicionario_variaveis.xlsx", index=False)

# 3) Dicionário CBO saúde -------------------------------------------------------
dic = pd.read_csv("dados/processados/dicionario_cbo_observado.csv", sep=";", dtype=str, encoding="utf-8-sig")
dic.to_excel("metadados/dicionario_cbo_profissoes_saude.xlsx", index=False)

# 4) Matriz de revisão teórica --------------------------------------------------
mt = [
 {"referencia": "ANTUNES, R. O privilégio da servidão: o novo proletariado de serviços na era digital. São Paulo: Boitempo, 2018.",
  "objetivo": "Analisar a nova morfologia do trabalho e o proletariado de serviços na era digital",
  "abordagem": "Sociologia do trabalho marxista",
  "conceitos_chave": "Precarização estrutural; terceirização; informalidade; superexploração; 'sociedade dos adoecimentos no trabalho' (cap. 8)",
  "contribuicao": "Interpreta a expansão precarizada dos serviços (inclusive saúde) e o adoecimento como traço estrutural da acumulação flexível",
  "limitacoes": "Escala macrossocial; não trata especificamente das profissões da saúde"},
 {"referencia": "CECILIO, L. C. O.; LACAZ, F. A. C. O trabalho em saúde. Rio de Janeiro: Cebes, 2012.",
  "objetivo": "Sistematizar o conceito de trabalho em saúde e as contribuições da Saúde do Trabalhador (ST)",
  "abordagem": "Saúde Coletiva; ST; gestão do cuidado",
  "conceitos_chave": "Processo de trabalho; cargas e desgaste; divisão social e técnica do trabalho; precarização no SUS (30–50% dos vínculos sem direitos); sobrecarga da enfermagem; crítica à medicina do trabalho curativa",
  "contribuicao": "Núcleo teórico do artigo: liga organização do trabalho em saúde, desgaste e desigualdades entre categorias",
  "limitacoes": "Texto de formação; dados nacionais de época"},
 {"referencia": "LEMOS, M. R. Estratificação social na teoria de Max Weber. Revista Iluminart, ano IV, n. 9, p. 113-128, 2012.",
  "objetivo": "Rever a teoria weberiana da estratificação (classe, estamento, partido)",
  "abordagem": "Sociologia compreensiva",
  "conceitos_chave": "Situação de classe e de mercado; honra estamental; fechamento social",
  "contribuicao": "Ilumina hierarquias de prestígio e renda entre profissões da saúde e o acesso desigual à proteção",
  "limitacoes": "Ensaio teórico, sem dados empíricos"},
 {"referencia": "LOURENÇO, G. G. O fim do fim do trabalho. Primeiros Estudos, n. 3, p. 104-121, 2012.",
  "objetivo": "Criticar as teses da sociedade pós-industrial e do fim da centralidade do trabalho",
  "abordagem": "Sociologia do trabalho",
  "conceitos_chave": "Centralidade do trabalho; classe trabalhadora ampliada; serviços",
  "contribuicao": "Fundamenta a leitura do setor de serviços de saúde como espaço central do conflito capital-trabalho",
  "limitacoes": "Revisão bibliográfica"},
 {"referencia": "OLIVEIRA, E. M. Transformações no mundo do trabalho... Caminhos de Geografia, v. 6, n. 11, p. 84-96, 2004.",
  "objetivo": "Historizar as transformações do processo de produção desde a Revolução Industrial",
  "abordagem": "História social (Marx, Thompson, Hobsbawm)",
  "conceitos_chave": "Disciplinarização; tempo de trabalho; maquinaria; resistências",
  "contribuicao": "Historicidade da organização do trabalho — base para articular a formação de Campos ao presente",
  "limitacoes": "Panorâmica; não trata de saúde"},
 {"referencia": "MENDES, R.; DIAS, E. C. Da medicina do trabalho à saúde do trabalhador. Revista de Saúde Pública, v. 25, n. 5, p. 341-349, 1991.",
  "objetivo": "Traçar a evolução conceitual da medicina do trabalho à ST",
  "abordagem": "Saúde Coletiva / Medicina Social Latino-Americana",
  "conceitos_chave": "Determinação social; processo de trabalho; protagonismo dos trabalhadores",
  "contribuicao": "Marco conceitual do campo ST usado como referência do enquadramento",
  "limitacoes": "Texto clássico (1991)"},
 {"referencia": "VEDOVATO, T. G. et al. Trabalhadores(as) da saúde e a COVID-19: condições de trabalho à deriva? RBSO, v. 46, e1, 2021.",
  "objetivo": "Discutir condições de trabalho dos trabalhadores da saúde na pandemia",
  "abordagem": "Saúde do Trabalhador",
  "conceitos_chave": "Precarização; riscos biológicos e psicossociais; invisibilidade; gênero",
  "contribuicao": "Contextualiza o período crítico da COVID-19 sem inferência causal",
  "limitacoes": "Ensaio/revisão"},
 {"referencia": "SILVA, J. E. M.; HASENCLEVER, L. Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes – 1999/2014. Desenvolvimento em Questão, v. 17, n. 46, p. 314-332, 2019.",
  "objetivo": "Avaliar efeitos do ciclo do petróleo/royalties sobre o desenvolvimento de Campos",
  "abordagem": "Economia regional",
  "conceitos_chave": "Renda petrolífera; dependência fiscal; fraca diversificação produtiva",
  "contribuicao": "Evidência da contradição riqueza fiscal x desenvolvimento social em Campos",
  "limitacoes": "Período até 2014"},
 {"referencia": "MARTINS, S.; HASENCLEVER, L.; MIRANDA, C. A gestão da saúde à luz da instabilidade de financiamento... Cadernos do Desenvolvimento Fluminense, n. 27, 2024.",
  "objetivo": "Analisar efeitos da queda das rendas petrolíferas e dos modelos de gestão sobre a saúde municipal de Campos (2009–2020)",
  "abordagem": "Economia da saúde; gestão pública",
  "conceitos_chave": "Financiamento instável; rendas de indenizações petrolíferas; gestão da rede",
  "contribuicao": "Liga a dependência fiscal do petróleo à organização (e fragilidade) da rede de saúde local",
  "limitacoes": "Estudo descritivo"},
]
pd.DataFrame(mt).to_excel("metadados/matriz_revisao_teorica.xlsx", index=False)

# 5) Tabela de referências ABNT -------------------------------------------------
refs = [
 ("ANTUNES, R.", "O privilégio da servidão: o novo proletariado de serviços na era digital.", "São Paulo: Boitempo, 2018.", "livro (pasta ARTIGOS; ficha catalográfica conferida)", ""),
 ("BRASIL. Ministério da Previdência Social. Instituto Nacional do Seguro Social.", "Comunicações de Acidente de Trabalho – CAT: dados abertos, 2018–2025.", "Brasília: INSS. Disponível em: https://dados.gov.br/dados/conjuntos-dados/inss-comunicacao-de-acidente-de-trabalho-cat. Acesso em: 18 jul. 2026.", "base de dados (58 arquivos na pasta CAT - INSS/DADOS)", ""),
 ("CECILIO, L. C. O.; LACAZ, F. A. C.", "O trabalho em saúde.", "Rio de Janeiro: Cebes, 2012.", "livro (pasta ARTIGOS; folha de rosto conferida)", ""),
 ("IBGE.", "Censo Demográfico 2022; Produto Interno Bruto dos Municípios; Produção Agrícola Municipal.", "Rio de Janeiro: IBGE. Sistema SIDRA (tabelas 4714, 6579, 5938, 1612). Acesso em: 18 jul. 2026.", "bases de dados (sidra-campos)", ""),
 ("LEMOS, M. R.", "Estratificação social na teoria de Max Weber: considerações em torno do tema.", "Revista Iluminart, Sertãozinho, ano IV, n. 9, p. 113-128, nov. 2012.", "artigo (pasta ARTIGOS)", ""),
 ("LOURENÇO, G. G.", "O fim do fim do trabalho: uma crítica à chamada sociedade pós-industrial e sua relação com os movimentos de trabalhadores.", "Primeiros Estudos, São Paulo, n. 3, p. 104-121, 2012.", "artigo (pasta ARTIGOS)", ""),
 ("MARTINS, S.; HASENCLEVER, L.; MIRANDA, C.", "A gestão da saúde à luz da instabilidade de financiamento e das propostas de governo.", "Cadernos do Desenvolvimento Fluminense, Rio de Janeiro, n. 27, 2024.", "artigo verificado (Crossref + página do periódico)", "10.12957/cdf.2024.87352"),
 ("MENDES, R.; DIAS, E. C.", "Da medicina do trabalho à saúde do trabalhador.", "Revista de Saúde Pública, São Paulo, v. 25, n. 5, p. 341-349, 1991.", "artigo verificado (Crossref)", "10.1590/S0034-89101991000500003"),
 ("OLIVEIRA, E. M.", "Transformações no mundo do trabalho, da Revolução Industrial aos nossos dias.", "Caminhos de Geografia, Uberlândia, v. 6, n. 11, p. 84-96, fev. 2004.", "artigo (pasta ARTIGOS)", ""),
 ("SILVA, J. E. M. da; HASENCLEVER, L.", "Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes – 1999/2014.", "Desenvolvimento em Questão, Ijuí, v. 17, n. 46, p. 314-332, 2019.", "artigo verificado (Crossref)", "10.21527/2237-6453.2019.46.314-332"),
 ("VEDOVATO, T. G.; ANDRADE, C. B.; SANTOS, D. L.; BITENCOURT, S. M.; ALMEIDA, L. P. de; SAMPAIO, J. F. da S.", "Trabalhadores(as) da saúde e a COVID-19: condições de trabalho à deriva?", "Revista Brasileira de Saúde Ocupacional, São Paulo, v. 46, e1, 2021.", "artigo verificado (Crossref)", "10.1590/2317-6369000028520"),
]
pd.DataFrame(refs, columns=["autoria", "titulo", "dados_publicacao", "verificacao", "doi"]).to_excel("referencias/tabela_referencias_abnt.xlsx", index=False)

# 6) Fluxo de seleção ------------------------------------------------------------
pd.read_csv("saidas/tabelas/T19_fluxo_selecao.csv", sep=";", encoding="utf-8-sig").to_excel("metadados/fluxo_selecao_registros.xlsx", index=False)

# 7) Logs de auditoria -----------------------------------------------------------
aud = [
 ("cobertura_fonte", "A série do INSS/PDA inicia na competência jul/2018: acidentes de jan–jun/2018 só aparecem se registrados depois", "alto", "estatisticas_por_arquivo.csv", "2018 tratado como ano de cobertura parcial (asterisco em tabelas/figuras)", "comparações anuais com ressalva"),
 ("cobertura_fonte", "Arquivos de 2022 com cobertura irregular (202201/202204 com emissões até jun; 202207–202211 sobrepostos e decrescentes)", "alto", "estatisticas_por_arquivo.csv; duplicidades_linha_bruta.csv", "deduplicação por hash entre arquivos sobrepostos; 2022 marcado como parcial", "537 duplicidades removidas no recorte Campos+RJ"),
 ("cobertura_fonte", "Competências set–dez/2024 com volume nacional atípico (3–10 mil linhas/mês vs 40–60 mil) e nov–dez/2025 quase vazias (205 e 126 linhas)", "alto", "estatisticas_por_arquivo.csv", "2024 e 2025 marcados como parciais; sensibilidade jan–out", "queda 2024–2025 NÃO interpretável como redução real"),
 ("estrutura", "4 esquemas de colunas (24A, 24B, 25, 27); cabeçalhos duplicados (CBO, CID-10, CNAE, Data Acidente); 3 arquivos de 2020 em UTF-8-BOM e demais em Latin-1", "moderado", "logs/esquemas_por_arquivo.json", "importação por posição com mapa por esquema e detecção de codificação por arquivo", "nenhuma coluna sobrescrita"),
 ("estrutura", "Esquema S24B (competências jun–out/2023) NÃO traz data de emissão nem despacho", "moderado", "logs/esquemas_por_arquivo.json", "tempo acidente→emissão calculado apenas onde disponível (n informado)", "2023 com 112/178 válidos"),
 ("municipio", "12 registros com código 330100 e UF do empregador ≠ RJ (SP, RS, GO, PR)", "baixo", "controle_330100_uf_divergente.csv", "excluídos pelo critério conjunto código+UF", "base final sem inconsistências de UF"),
 ("cbo", "184 registros (3,6%) sem CBO válido, concentrados em 2021–2023 ('{ñ class}'), 35 deles em CNAE saúde", "moderado", "T01_cat_por_ano_universo.csv", "mantidos em categoria própria 'CBO não classificado'", "possível subestimação de profissões da saúde em 2021–2023"),
 ("cbo", "Descrições truncadas a 20 caracteres em parte dos arquivos; códigos 2231xx (família médica anterior) ausentes da tabela CBO vigente", "baixo", "dicionario_cbo_observado.csv", "classificação por código+família com validação manual; títulos oficiais anexados", "classificação íntegra"),
 ("datas", "Coluna 2 'Data Acidente' é mês de referência (AAAA/MM, AAAAMM ou DD/MM/AAAA com dia=01), distinta da data completa (col. 21–23)", "alto", "amostras por esquema (logs)", "análises temporais usam exclusivamente a data completa do acidente", "sem confusão competência x data"),
 ("idade", "7 registros sem data de nascimento válida; nenhuma idade fora de [14,100] na base Campos", "baixo", "fluxo_03_processamento.json", "idade ausente registrada; sem exclusão de registros", "—"),
 ("smartlab", "Nenhum arquivo SmartLab presente na pasta; etapa excluída por decisão metodológica", "informativo", "manifesto_arquivos.csv", "—", "—"),
 ("legado", "Resultados da análise anterior (medicina x enfermagem) não localizados na pasta (RESULTADOS/ ausente); não reproduzíveis e não reutilizados", "informativo", "inspeção de diretórios", "análise integralmente refeita desde os brutos", "—"),
]
pd.DataFrame(aud, columns=["origem", "problema_evidencia", "gravidade", "fonte_evidencia", "correcao_decisao", "limitacao_remanescente"]).to_csv("logs/log_auditoria.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

alt = [
 ("CAT - INSS/script.R", "classificar_profissao()", "Classificação parcialmente textual: str_detect('enferm') incluiria CBO 519305 (auxiliar de veterinário, sinônimo 'enfermeiro veterinário' na fonte); 'medic' sem exclusões suficientes", "alto", "1 registro na base Campos seria classificado como Enfermagem", "Nova classificação exclusivamente por código CBO/família com dicionário auditado", "Enfermagem incluiria registro veterinário", "519305 excluído do universo principal"),
 ("CAT - INSS/script.R", "filtro_campos", "Filtro municipal por código OU texto, sem checagem da UF do empregador", "moderado", "12 registros 330100 com UF≠RJ entrariam na base", "Critério conjunto: código 330100 E UF RJ", "5.078 registros", "5.066 registros"),
 ("CAT - INSS/script.R", "escopo", "Universo restrito a Medicina e Enfermagem", "crítico (para o objetivo atual)", "Perda de 166 CATs de outras 10 categorias da saúde (14,5% do universo principal)", "Universo ampliado por CBO oficial (3 níveis)", "978 registros (Enf+Med)", "1.144 registros (12 categorias)"),
 ("CAT - INSS/script.R", "leitura (fread)", "Sem deduplicação entre arquivos sobrepostos (202201/202204; 202207–202211; 202404/202405; 202506–202510)", "crítico", "Dupla contagem: 537 duplicidades no recorte Campos+RJ (5.603→5.066)", "Deduplicação por hash SHA-256 da linha bruta, mantendo a 1ª competência", "contagens infladas", "base deduplicada"),
 ("CAT - INSS/script.R", "fread(encoding='Latin-1')", "3 arquivos de 2020 são UTF-8-BOM; leitura Latin-1 gera mojibake, 'corrigido' por substituições manuais (corrigir_rotulo_cat)", "moderado", "Rótulos corrompidos em gráficos/tabelas", "Detecção de codificação por arquivo", "rótulos com 'Ã§' etc.", "rótulos íntegros"),
 ("CAT - INSS/script.R", "make.unique/janitor", "Cabeçalhos duplicados renomeados automaticamente e coalescidos por regex de nomes; posição varia entre esquemas", "moderado", "Risco de mistura competência/data e código/descrição em esquemas distintos", "Importação por posição com mapa explícito por esquema", "—", "—"),
 ("CAT - INSS/script.R", "calcular_idade()", "Idades fora de [14,100] anuladas silenciosamente, sem log", "baixo", "Sem impacto na base Campos (0 casos)", "Regra registrada em log com contagem", "—", "—"),
 ("CAT - INSS/script.R", "chi-quadrado", "Testes de associação sobre dados de notificação sem denominadores", "baixo", "Risco interpretativo (frequência ≠ risco)", "Não replicados; análise descritiva com ressalvas", "—", "—"),
 ("CARACTERIZAÇÃO - CAMPOS/script.R", "setwd()", "Caminho absoluto para pasta antiga ('TRABALHOS/CARACTERIZAÇÃO')", "baixo", "Não executa em outra máquina", "Pipeline novo usa caminhos relativos", "—", "—"),
 ("CARACTERIZAÇÃO - CAMPOS/script.R", "tabela 4709", "Arquivo nomeado 'pib_per_capita.csv' contém tabela 4709 (população residente/taxa de crescimento), não PIB per capita", "moderado", "Risco de citação errada de indicador", "PIB per capita calculado explicitamente (PIB 5938 ÷ população 6579)", "rótulo incorreto", "indicador correto e documentado"),
 ("CARACTERIZAÇÃO - CAMPOS/script.R", "log_download", "8 de 21 tabelas SIDRA falharam (5939, 9518, 9519, 9520, 9607, 9609, 9610)", "informativo", "Caracterização incompleta (sem VA setorial em série própria, rendimento, esgotamento)", "Uso das tabelas disponíveis; lacunas declaradas", "—", "—"),
]
pd.DataFrame(alt, columns=["script", "linha_bloco", "problema", "gravidade", "impacto", "correcao", "resultado_anterior", "resultado_corrigido"]).to_csv("logs/log_alteracoes_scripts.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# log_qualidade_dados
comp = pd.read_csv("saidas/tabelas/T15_completude_pct.csv", sep=";", encoding="utf-8-sig")
comp.to_csv("logs/log_qualidade_dados.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# 8) versões e README ------------------------------------------------------------
import importlib.metadata as im
pacotes = ["pandas", "numpy", "matplotlib", "openpyxl", "pypdf", "pyarrow", "python-docx", "pytest"]
with open("metadados/versoes_programas_pacotes.txt", "w", encoding="utf-8") as f:
    f.write(f"Python {platform.python_version()} | {platform.platform()}\nLibreOffice 26.2.3.2 (conversão DOCX->PDF p/ contagem de páginas)\n")
    for p in pacotes:
        try: f.write(f"{p}=={im.version(p)}\n")
        except Exception: pass
with open("metadados/requirements.txt", "w", encoding="utf-8") as f:
    for p in ["pandas", "numpy", "matplotlib", "openpyxl", "pypdf", "pyarrow", "python-docx", "pytest"]:
        try: f.write(f"{p}=={im.version(p)}\n")
        except Exception: pass

with open("referencias/fonte_cbo.txt", "w", encoding="utf-8") as f:
    f.write("Tabela 'CBO2002 - Ocupação' (estrutura oficial do Ministério do Trabalho e Emprego, CBO 2002).\n"
            "Obtida em espelho público: https://github.com/cartaproale/cbo-csv (arquivo 'CBO2002 - Ocupacao.csv', 2.719 títulos).\n"
            f"Data de consulta: {HOJE}. Limitação registrada: o portal oficial (www.mtecbo.gov.br) exige cadastro para download;\n"
            "o espelho reproduz o arquivo oficial de códigos e títulos e foi usado apenas para VALIDAÇÃO dos títulos;\n"
            "a classificação decisória baseou-se em famílias/códigos observados e revisão manual (dicionario_cbo_profissoes_saude.xlsx).\n")

readme = """# Saúde do Trabalhador em Campos dos Goytacazes — CAT/INSS 2018–2025

Reconstrução integral e auditada da análise das Comunicações de Acidente de Trabalho (CAT/INSS)
vinculadas a empregadores de Campos dos Goytacazes/RJ (código 330100), 2018–2025, para **todas as
profissões da saúde** (CBO 2002), articulada à formação histórico-social e econômica do município.
Etapa SmartLab excluída por decisão metodológica (nenhum arquivo dessa origem no projeto).
A análise legada (medicina x enfermagem) foi catalogada e auditada em `scripts/legado/`, sem
reaproveitamento de resultados.

## Estrutura do repositório
```
artigos-fonte/        # PDFs teóricos (NÃO versionados — direitos autorais; ver README local)
dados/
  brutos/cat-inss/    # 58 CSV CAT/INSS (NÃO versionados — 1,8 GB; ver README local p/ download)
  brutos/sidra-campos/# tabelas SIDRA/IBGE (versionadas)
  manifesto/          # inventário com SHA-256 de todos os arquivos-fonte
  processados/        # bases processadas (CSV/Parquet) e logs de decisão
documentos/           # artigo.docx (≤5 págs) + 3 relatórios (metodológico e auditorias)
logs/                 # logs de execução, auditoria, qualidade e validação independente
metadados/            # dicionários (variáveis, CBO-saúde), matriz teórica, fluxo, versões
referencias/          # referências verificadas, dicionário oficial da fonte, espelho CBO
saidas/tabelas|figuras/
scripts/pipeline/     # 01–09 (executar em ordem)
scripts/legado/       # scripts originais catalogados + cópias auditadas comentadas
```

## Reprodução
```bash
pip install -r metadados/requirements.txt
python scripts/pipeline/01_inventario.py
python scripts/pipeline/02_ingestao_cat.py
python scripts/pipeline/03_processamento_campos.py
python scripts/pipeline/04_dicionario_cbo_classificacao.py
python scripts/pipeline/05_analises.py
python scripts/pipeline/06_validacao_independente.py   # exit 1 se totais divergirem
python scripts/pipeline/07_entregaveis.py
python scripts/pipeline/08_relatorios_docx.py
python scripts/pipeline/09_artigo_docx.py              # requer LibreOffice p/ conferir páginas
python scripts/pipeline/10_denominadores_cnes.py       # denominadores reais CNES/TabNet (rede)
```
Caminhos relativos à raiz; sem procedimentos aleatórios; logs em `logs/`.
Os dados brutos da CAT devem ser obtidos conforme `cat-inss/README.md` e conferidos
pelos hashes de `dados/manifesto/manifesto_arquivos.csv`.

## Testes e integração contínua
`python -m pytest tests -q` — 38+ testes sobre os DADOS REAIS versionados (filtro municipal,
deduplicação, classificação CBO, tabelas, supressão, denominadores, limite de páginas do artigo).
Testes que exigem os brutos (não versionados) são pulados automaticamente — nunca simulados.
O workflow `.github/workflows/ci.yml` roda os testes, reprocessa os estágios deriváveis e exige
que os CSVs regenerados sejam idênticos aos versionados (determinismo).

## Denominadores (CNES) e razões exploratórias
`10_denominadores_cnes.py` baixa do TabNet/DataSUS os profissionais (indivíduos) por ocupação
CBO 2002 em Campos (330100), dez/2018–dez/2025, com verificação dupla de totais e brutos em
`cnes/`. As razões CAT/1.000 profissionais (T22) são EXPLORATÓRIAS: o CNES
inclui vínculos estatutários/autônomos/PJ, fora da cobertura da CAT — não são incidência.
RAIS/eSocial permanece como denominador prioritário (bloqueio documentado em
`logs/log_10_denominadores.json`).

## Distribuição dos dados brutos
`python scripts/ferramentas/empacotar_dados_brutos.py` gera ZIPs por ano em `distribuicao/`
(+ SHA-256 em `metadados/SHA256SUMS_distribuicao.txt`) para anexar a uma release do GitHub
`python scripts/ferramentas/restaurar_dados_brutos.py` extrai os ZIPs e confere cada CSV
contra o manifesto antes de liberar a reprodução.

## Advertência interpretativa
CAT = comunicações registradas (emprego formal celetista), não a totalidade dos acidentes; sem
denominadores (RAIS/eSocial-PDET; CNES) não se calculam incidência/risco/taxa. Coberturas parciais
da fonte: 2018 (competências desde jul.), 2022 (carga irregular), 2024 (set–dez atípicos) e 2025
(parcial até out.).
"""
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("Entregáveis de documentação gerados.")
