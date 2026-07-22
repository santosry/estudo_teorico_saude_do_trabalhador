# Saúde do Trabalhador em Campos dos Goytacazes — Análise Multifonte 2015–2025

Ensaio teórico apoiado na triangulação de oito fontes independentes sobre acidentes
e agravos relacionados ao trabalho em Campos dos Goytacazes/RJ (IBGE 330100),
2015–2025, abrangendo **todas as profissões** do município.

A premissa metodológica é que nenhuma fonte isolada oferece retrato completo dos
agravos ocupacionais. Cada sistema de informação captura uma fração distinta do
fenômeno, determinada por sua finalidade institucional, cobertura populacional e
regras de notificação. A justaposição de fontes permite identificar padrões
convergentes e divergências informativas.

| Fonte | Cobertura | Dimensão analisada |
|---|---|---|
| **SINAN** | Agravos de notificação compulsória — 2015 a 2025 | Doenças e agravos ocupacionais (acidente grave, expos. material biológico, LER/DORT, transtorno mental, intoxicações, etc.) |
| **Benefícios INSS** | Auxílios-doença acidentários (B91) e previdenciários (B31) — 2015 a 2025 | Afastamentos e incapacidade laboral |
| **CAT/INSS** | Acidentes de trabalho comunicados (celetistas) — 2015 a 2025 | Incidência notificada de acidentes típicos, trajeto e doenças ocupacionais |
| **RAIS** | Vínculos formais de trabalho — 2018 a 2025 | Denominadores populacionais, perfil sociodemográfico e setorial |
| **CAGED** | Admissões e desligamentos (2018–2019 via PDET/MTE; 2019–2025 via SmartLab/Novo CAGED) | Dinâmica do mercado formal de trabalho |
| **SmartLab** | Indicadores sintéticos do Observatório de SST/MPT — 2000 a 2026 | Epidemiologia institucional, subnotificação, trabalho infantil, trabalho escravo |
| **IPS Brasil** | Evolução trianual — 2024 a 2026 | Indicadores sociais e territoriais |
| **SIDRA/IBGE** | Projeções populacionais, PIB, CEMPRE | Contexto socioeconômico e demográfico |

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
- **SINAN**: FTP DATASUS — Agravos de Notificação Compulsória, 9 agravos, 2015–2025
- **Benefícios INSS**: Portal de Dados Abertos (dados.gov.br) — Auxílios-doença acidentários (B91) e previdenciários (B31), 2015–2025
- **CAT/INSS**: Portal de Dados Abertos (dados.gov.br) — Comunicações de Acidente de Trabalho, 2015–2025
- **RAIS**: PDET/MTE — Relação Anual de Informações Sociais (vínculos formais)
- **CAGED**: PDET/MTE (2018–2019) + SmartLab/Novo CAGED (2019–2025)
- **SmartLab**: API datahub/MPT — SST, Trabalho Infantil, Trabalho Escravo, Trabalho Decente
- **IPS Brasil**: ipsbrasil.org.br — evolução trianual 2024–2026
- **SIDRA/IBGE**: Censo 2022, PIB municipal, CEMPRE

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
Cada fonte possui limitações intrínsecas que a triangulação atenua, mas não elimina:
- **SINAN**: agravos notificados com subnotificação reconhecida; cobertura heterogênea
  por unidade de saúde e período; nexo ocupacional depende da qualidade do preenchimento.
- **Benefícios INSS**: apenas concessões (B31/B91); não captura indeferimentos nem
  subnotificação previdenciária; base sem Classificação Brasileira de Ocupações.
- **CAT**: exclusiva de celetistas; estatutários (RPPS) estruturalmente excluídos.
- **RAIS**: vínculos formais celetistas + estatutários; exclui informais, autônomos, MEIs.
- **CAGED**: cobertura 2018–2019 (CAGEDEST) + 2019–2025 (Novo CAGED via SmartLab).
- Coberturas parciais em múltiplas fontes: 2015–2017 (semestral), 2018 (jul–dez),
  2022 (carga irregular), 2024–2025 (parcial até outubro).
- **Triangulação de fontes** é a estratégia metodológica central para mitigar
  limitações individuais de cada sistema de informação.
