# Saúde do Trabalhador em Campos dos Goytacazes — Análise Multifonte 2015–2025

Reconstrução integral e auditada do perfil de saúde do trabalhador em Campos dos Goytacazes/RJ
(código IBGE 330100), 2015–2025, para **todas as profissões da saúde** (CBO 2002), articulada
à formação histórico-social e econômica do município. A análise **não se restringe às CATs ou ao
INSS** — integra múltiplas bases do Sistema Único de Saúde e de estatísticas do trabalho:

| Fonte | Cobertura | Dimensão analisada |
|---|---|---|
| **CAT/INSS** | Acidentes de trabalho comunicados (celetistas) — 2015 a 2025 | Incidência notificada de acidentes típicos, trajeto e doenças ocupacionais |
| **Benefícios INSS** | Auxílios-doença acidentários (B91) e previdenciários (B31) — 2015 a 2025 | Afastamentos e incapacidade laboral |
| **SINAN** | Agravos de notificação compulsória relacionados ao trabalho — 2015 a 2025 | Doenças e agravos ocupacionais de notificação (LER/DORT, intoxicações, transtornos mentais, etc.) |
| **RAIS** | Vínculos formais de trabalho | Denominadores populacionais, perfil sociodemográfico e setorial da força de trabalho |
| **CAGED** | Admissões e desligamentos (2018–2019 via PDET/MTE; 2019–2025 via SmartLab/Novo CAGED) | Dinâmica do mercado formal de trabalho em saúde |
| **CNES/TabNet** | Profissionais de saúde cadastrados (indivíduos) — 2018 a 2025 | Denominadores exploratórios por ocupação CBO 2002 |
| **SmartLab** | Indicadores sintéticos do Observatório de SST/MPT (inclui Novo CAGED 2019–2025) | Epidemiologia institucional comparada e dinâmica do emprego formal |
| **SIDRA/IBGE** | Projeções populacionais e PIB municipal | Contexto socioeconômico e demográfico |

A análise legada (medicina x enfermagem) foi catalogada e auditada em `scripts/legado/`, sem
reaproveitamento de resultados.

## Estrutura do repositório
```
artigos-fonte/        # PDFs teóricos (NÃO versionados — direitos autorais; ver README local)
dados/
  brutos/cat-inss/    # 58 CSV CAT/INSS (NÃO versionados — 1,8 GB; ver README local p/ download)
  brutos/sinan/       # arquivos SINAN brutos (NÃO versionados)
  brutos/rais/        # arquivos RAIS brutos (NÃO versionados)
  brutos/sidra-campos/# tabelas SIDRA/IBGE (versionadas)
  manifesto/          # inventário com SHA-256 de todos os arquivos-fonte
  processados/        # bases processadas (CSV/Parquet) de todas as fontes + logs de decisão
documentos/           # ensaio.docx/pdf (≤5 págs)
logs/                 # logs de execução, auditoria, qualidade e validação independente
metadados/            # dicionários (variáveis, CBO-saúde), matriz teórica, fluxo, versões
referencias/          # referências verificadas, dicionário oficial da fonte, espelho CBO
saidas/tabelas|figuras/
scripts/pipeline/     # 01–16 (executar em ordem por dependência)
scripts/legado/       # scripts originais catalogados + cópias auditadas comentadas
```

## Reprodução
```bash
pip install -r metadados/requirements.txt

# Preparação: inventário e ingestão de bases
python scripts/pipeline/01_inventario.py                # inventário SHA-256 de todos os arquivos-fonte
python scripts/pipeline/02_ingestao_cat.py              # ingestão CAT/INSS (58 CSVs, 1,8 GB)
python scripts/pipeline/16_sinan_download.py            # download e validação SINAN (Microdatasus)
python scripts/download_sih_sim_ben.R                   # download SIH + Benefícios INSS

# Processamento
python scripts/pipeline/03_processamento_campos.py      # filtro municipal (330100), deduplicação e tipificação
python scripts/pipeline/04_dicionario_cbo_classificacao.py  # classificação CBO 2002 — profissões da saúde
python scripts/processar_sinan.py                       # processamento SINAN — agravos ocupacionais
python scripts/processar_beneficios_inss.py             # benefícios INSS acidentários e previdenciários
python scripts/sih_campos_microdatasus.R                # internações hospitalares relacionadas ao trabalho

# Denominadores e contexto
python scripts/pipeline/10_denominadores_cnes.R         # CNES/TabNet — profissionais por CBO (rede)
python scripts/pipeline/11_denominadores_rais.py        # RAIS — vínculos formais, gênero e setor
python scripts/download_caged_campos.py                 # CAGED — dinâmica de admissões/desligamentos
python scripts/download_rais_campos.py                  # RAIS — perfil sociodemográfico da força de trabalho
python scripts/RAIS_genero.py                           # estratificação por gênero RAIS/CAGED

# Análises
python scripts/pipeline/05_analises.py                  # estatísticas descritivas e séries temporais
python scripts/pipeline/13_series_temporais.py          # modelos de tendência e sazonalidade
python scripts/pipeline/14_redes_associacao.py          # redes de associação entre agravos e ocupações
python scripts/pipeline/15_ips_campos.py                # Índice de Pressão Social (IPS) municipal
python scripts/smartlab_completo.py                     # indicadores SmartLab — epidemiologia institucional

# Validação e entregáveis
python scripts/pipeline/06_validacao_independente.py    # exit 1 se totais divergirem
python scripts/pipeline/07_entregaveis.py               # tabelas e figuras finais
python scripts/pipeline/08_relatorios_docx.py           # relatórios metodológicos e de auditoria
python scripts/pipeline/09_artigo_docx.py               # ensaio final (requer LibreOffice p/ conferir páginas)
```

Caminhos relativos à raiz; sem procedimentos aleatórios; logs em `logs/`.
Os dados brutos não versionados (CAT, SINAN, RAIS) devem ser obtidos conforme
os respectivos READMEs em cada subpasta e conferidos pelos hashes de
`dados/manifesto/manifesto_arquivos.csv`.

### Fontes e instrumentos de coleta
- **CAT/INSS**: Portal de Dados Abertos do INSS (dados.gov.br) — CSVs mensais de Comunicações de Acidente de Trabalho, 2015–2025
- **SINAN**: FTP DATASUS — Agravos de Notificação Compulsória relacionados ao trabalho, 9 agravos, 2015–2025
- **Benefícios INSS**: Portal de Dados Abertos do INSS — Auxílios-doença acidentários (B91) e previdenciários (B31), 2015–2025
- **SIH**: Microdatasus — Sistema de Informações Hospitalares (AIHs com desfecho ocupacional)
- **RAIS**: Microdatasus/PDET — Relação Anual de Informações Sociais (vínculos formais)
- **CAGED**: PDET/MTE (2018–2019) + SmartLab/Novo CAGED (2019–2025) — Cadastro Geral de Empregados e Desempregados
- **CNES**: TabNet/DataSUS — Cadastro Nacional de Estabelecimentos de Saúde
- **SmartLab**: Observatório Digital de SST/MPT — indicadores sintéticos, inclui dados do Novo CAGED
- **SIDRA/IBGE**: Projeções populacionais, PIB e contexto socioeconômico

## Testes e integração contínua
`python -m pytest tests -q` — 38+ testes sobre os DADOS REAIS versionados (filtro municipal,
deduplicação, classificação CBO, consistência entre fontes: CAT × SINAN × SIH,
integridade referencial de códigos IBGE e CBO, supressão de células <3, denominadores,
limite de páginas do artigo). Testes que exigem os brutos (não versionados) são pulados
automaticamente — nunca simulados. O workflow `.github/workflows/ci.yml` roda os testes,
reprocessa os estágios deriváveis e exige que os CSVs regenerados sejam idênticos aos
versionados (determinismo).

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

## Advertências interpretativas
- **CAT** = comunicações registradas (emprego formal celetista), não a totalidade dos acidentes.
  Sem denominadores (RAIS/eSocial-PDET; CNES) não se calculam incidência/risco/taxa.
- **SINAN** = agravos notificados (subnotificação reconhecida), cobertura heterogênea por
  unidade de saúde e período. Nexo ocupacional depende da qualidade do preenchimento.
- **SIH** = internações pelo SUS (AIHs aprovadas); exclui rede privada não conveniada,
  planos de saúde e desembolso direto.
- **Benefícios INSS** = apenas auxílios-doença concedidos (B31/B91); não captura
  subnotificação previdenciária nem indeferimentos.
- **RAIS** = vínculos formais celetistas + estatutários; exclui trabalhadores informais,
  autônomos, MEIs e cooperados sem vínculo.
- **CAGED** = 2018–2019 via PDET/MTE (CAGEDEST); 2019–2025 via SmartLab (Novo CAGED). Apenas movimentações do mercado formal celetista.
- Coberturas parciais: 2018 (competências desde jul.), 2022 (carga irregular em múltiplas
  fontes), 2024 (set–dez atípicos) e 2025 (parcial até out.).
- **Triangulação de fontes** é a estratégia metodológica central para mitigar limitações
  individuais de cada sistema de informação.
