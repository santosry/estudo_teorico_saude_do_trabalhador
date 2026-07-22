# Saúde do Trabalhador em Campos dos Goytacazes — Análise Multifonte 2015–2025

Reconstrução integral e auditada do perfil de saúde do trabalhador em Campos dos Goytacazes/RJ
(código IBGE 330100), 2015–2025, abrangendo **todas as profissões** do município. A análise
articula oito fontes independentes — sistemas de notificação, bases previdenciárias, estatísticas
do trabalho e indicadores territoriais — articuladas à formação histórico-social e econômica local:

| Fonte | Cobertura | Dimensão analisada |
|---|---|---|
| **CAT/INSS** | Acidentes de trabalho comunicados (celetistas) — 2015 a 2025 | Incidência notificada de acidentes típicos, trajeto e doenças ocupacionais |
| **Benefícios INSS** | Auxílios-doença acidentários (B91) e previdenciários (B31) — 2015 a 2025 | Afastamentos e incapacidade laboral |
| **SINAN** | Agravos de notificação compulsória relacionados ao trabalho — 2015 a 2025 | Doenças e agravos ocupacionais de notificação (LER/DORT, intoxicações, transtornos mentais, etc.) |
| **RAIS** | Vínculos formais de trabalho | Denominadores populacionais, perfil sociodemográfico e setorial da força de trabalho |
| **CAGED** | Admissões e desligamentos (2018–2019 via PDET/MTE; 2019–2025 via SmartLab/Novo CAGED) | Dinâmica do mercado formal de trabalho |
| **SmartLab** | Indicadores sintéticos do Observatório de SST/MPT (inclui Novo CAGED 2019–2025) | Epidemiologia institucional comparada e dinâmica do emprego formal |
| **SIDRA/IBGE** | Projeções populacionais e PIB municipal | Contexto socioeconômico e demográfico |

## Estrutura do repositório
```
artigos-fonte/        # PDFs teóricos (NÃO versionados — direitos autorais; ver README local)
dados/
  brutos/sinan/       # 100 arquivos SINAN .dbc (2015-2025, 9 agravos, versionados via LFS)
  brutos/sidra-campos/# tabelas SIDRA/IBGE (versionadas)
  manifesto/          # inventário com SHA-256 de todos os arquivos-fonte
  processados/        # bases processadas (CSV/Parquet) de todas as fontes + logs de decisão
documentos/           # documentos do estudo
logs/                 # logs de execução, auditoria, qualidade e validação independente
metadados/            # dicionários (variáveis, CBO), matriz teórica, fluxo, versões
referencias/          # referências verificadas, dicionário oficial da fonte, espelho CBO
saidas/tabelas|figuras/
scripts/pipeline/     # 01–16 (executar em ordem por dependência)
```

## SmartLab — Observatórios do MPT
Dados extraídos para Campos dos Goytacazes (3301009) via API `datahub`:

| Módulo | Indicadores | Conteúdo |
|---|---|---|
| **SST** (Saúde e Segurança) | 3.785 | CAT 2002–2023, benefícios B91-B94, SINAN, subnotificação, acidentalidade, atuação do MPT |
| **Trabalho Infantil** | 3.659 | Ocupação infantil, Prova Brasil, aprendizagem, fiscalização, piores formas |
| **Trabalho Escravo** | 233 | Operações de combate, CATs/SINAN adolescentes |
| **Trabalho Decente** | 42 | Oportunidades, jornada, conciliação, estabilidade, igualdade, CAGED |

Scripts: `scripts/smartlab_completo.py`, `scripts/download_smartlab_sst.py`, `scripts/explorar_smartlab.py`

## Reprodução
```bash
pip install -r metadados/requirements.txt

# Download de dados
python scripts/download_inss_completo.py --dataset cat  # CAT/INSS (48 CSVs, 2015-2025)
python scripts/download_sinan_2015_2017.py               # SINAN 2015-2017 (27 .dbc)
python scripts/pipeline/16_sinan_download.py            # SINAN 2018-2025 (72 .dbc)

# Processamento
python scripts/pipeline/03_processamento_campos.py      # filtro municipal (330100), deduplicação e tipificação
python scripts/pipeline/04_dicionario_cbo_classificacao.py  # classificação CBO 2002
python scripts/processar_sinan.py                       # processamento SINAN — agravos ocupacionais
python scripts/processar_beneficios_inss.py             # benefícios INSS acidentários e previdenciários
python scripts/sih_campos_microdatasus.R                # internações hospitalares relacionadas ao trabalho

# Denominadores e contexto
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

Caminhos relativos à raiz. Dados versionados via Git LFS. Para restaurar dados localmente:
`bash scripts/restaurar_dados_locais.sh`

### Fontes e instrumentos de coleta
- **CAT/INSS**: Portal de Dados Abertos do INSS (dados.gov.br) — CSVs mensais de Comunicações de Acidente de Trabalho, 2015–2025
- **SINAN**: FTP DATASUS — Agravos de Notificação Compulsória relacionados ao trabalho, 9 agravos, 2015–2025
- **Benefícios INSS**: Portal de Dados Abertos do INSS — Auxílios-doença acidentários (B91) e previdenciários (B31), 2015–2025
- **SIH**: Microdatasus — Sistema de Informações Hospitalares (AIHs com desfecho ocupacional)
- **RAIS**: Microdatasus/PDET — Relação Anual de Informações Sociais (vínculos formais)
- **CAGED**: PDET/MTE (2018–2019) + SmartLab/Novo CAGED (2019–2025) — Cadastro Geral de Empregados e Desempregados
- **SmartLab**: Observatório Digital de SST/MPT — indicadores sintéticos, inclui dados do Novo CAGED
- **SIDRA/IBGE**: Projeções populacionais, PIB e contexto socioeconômico

## Resultados principais

| Indicador | Total | Período |
|---|---|---|
| CATs registradas no município | **7.904** | 2015–2025 |
| Benefícios acidentários (B91-B94) | **4.149** | 2015–2025 |
| Arquivos SINAN (9 agravos) | **100 .dbc** | 2015–2025 |
| Indicadores SmartLab | **7.719** | 2000–2026 |

Tabelas completas em `saidas/tabelas/`.

## Testes e integração contínua
Workflow `.github/workflows/ci.yml`: reprocessa estágios deriváveis e verifica determinismo dos CSVs versionados.

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
- Coberturas parciais: 2015–2017 (dados semestrais), 2018 (jul–dez), 2022 (carga irregular),
  2024 (set–dez atípicos) e 2025 (parcial até out.).
- **Triangulação de fontes** é a estratégia metodológica central para mitigar limitações
  individuais de cada sistema de informação.
