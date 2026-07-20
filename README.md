# Panorama da saúde do trabalhador em Campos dos Goytacazes (RJ)

Estudo descritivo-analítico com pipeline reprodutível e auditado. Analisa as Comunicações de Acidente de Trabalho (CAT) do INSS entre profissões da saúde de Campos dos Goytacazes (2018-2025), com séries temporais, redes de associação e triangulação de denominadores previdenciários.

---

## Fontes de dados

| Base | Fonte | Período | Método | Valor-chave no estudo |
|------|-------|---------|--------|----------------------|
| **CAT/INSS** | Portal de Dados Abertos (dados.gov.br) | jul/2018 a out/2025 (58 arquivos) | Download CSV, leitura posicional (4 esquemas) | **1.144 CATs** de profissões da saúde; **84,4%** enfermagem |
| **RAIS/PDET** | FTP do MTE (ftp.mtps.gov.br) | 2018-2025 (8 anos) | `ftplib`, `py7zr`, auto-detecção de delimitador | Denominadores celetistas comensuráveis com a CAT |
| **SIM/DATASUS** | microdatasus (R) | 2019-2024 (6 anos) | Download .DBC, conversão read.dbc | **4.199 a 5.635** óbitos/ano; **10,9/1.000** em 2021 |
| **CNES-PF** | microdatasus (R), ftp.datasus.gov.br | 2018-2025 (8 anos) | Download .DBC, filtragem CODUFMUN | **13.839** profissionais (2018); **18.382** (2025) |
| **SINAN/DATASUS** | FTP do DATASUS (ftp.datasus.gov.br) | 2018-2022 | Download .dbc, 46 arquivos, 9 agravos | 126,5 MB de notificações compulsórias |
| **IBGE/SIDRA** | SIDRA (sidra.ibge.gov.br) | Censo 2022 + estimativas | Download CSV | **483.540** hab.; IDHM **0,716**; PIB per capita **R$ 88.831** |
| **CEMPRE** | IBGE Cidades | 2024 | Download CSV | **16.776** empresas; saúde: **1.544** estab. / **15.002** pessoas |
| **Siconfi/STN** | Siconfi (siconfi.tesouro.gov.br) | 2024 | Download CSV | Receitas **R$ 2,95 bi** (71% transferências) |
| **Portal da Transparência** | Prefeitura de Campos | 2020-2024 | Download CSV (despesas por natureza) | RPPS: **R$ 61,2 mi**; INSS: **R$ 18,3 mi** |
| **IPS Brasil** | ipsbrasil.org.br | 2024, 2025, 2026 | Download CSV | IPS **62,68**/100; Oportunidades **48,6**; Segurança Pessoal **52,8** |
| **BEN/INSS** | Portal de Dados Abertos do INSS | 2018-2025 | Download CSV/XLSX mensal (API CKAN) | **48.528** benefícios acidentários (B91-B94) em Campos |
| **SmartLab** | Observatório do Trabalho Decente (MPT) | 2010-2026 | Playwright (web scraping) | **42 indicadores** em 6 dimensões (oportunidades, jornada, conciliação, estabilidade, igualdade, rendimentos) |
| **SIH/SUS** | microdatasus (R) | 2018-2025 | Download .dbc + read.dbc | **255.254** internações (5.585 c/ CID trabalho) |

### Notas

- **Oliveira (2004)** fornece o marco histórico das transformações do mundo do trabalho, da Revolução Industrial aos dias atuais, fundamentando a análise de como cada configuração do processo de trabalho produz padrões específicos de adoecimento.

- **CAT e RAIS** capturam vínculos celetistas. Denominadores **comensuráveis**.
- **SINAN** 2018-2022 (FINAIS) + 2023-2025 (PRELIM), 9 agravos de notificação relacionados ao trabalho.
- **CNES-PF** inclui estatutários, autônomos e PJ. Utilizado como **triangulação**.

- **SmartLab**: indicadores do Observatório do Trabalho Decente (MPT) extraídos via Playwright para Campos dos Goytacazes. Abrange 6 dimensões: oportunidades de emprego (Novo CAGED), jornada, conciliação trabalho-vida, estabilidade, igualdade de oportunidades e rendimentos. Dados de 2010 (Censo) a 2026 (Novo CAGED).
- **BEN/INSS**: dados de benefícios concedidos do Portal de Dados Abertos do INSS (dadosabertos.inss.gov.br). Filtraram-se as espécies acidentárias (B91 Auxílio-Doença, B92 Aposentadoria por Invalidez, B93 Pensão por Morte, B94 Auxílio-Acidente) para o município de Campos dos Goytacazes. Sem CBO na base — comparação apenas por volume total.
- **RPPS municipal (PREVICAMPOS)**: sem base nacional de acidentes/adoecimentos de estatutários.
- **IPS 2024-2026**: análise trianual da evolução dos indicadores sociais do município.

---

## Estrutura do repositório

```
├── banco de dados/           # Todos os bancos de dados brutos
│   ├── cat-inss/             # 58 CSVs da CAT (jul/2018 a out/2025)
│   ├── rais/                 # RAIS 2018-2025 (microdados, 7z)
│   ├── sim/                  # SIM 2019-2024 (CSVs processados)
│   ├── cnes/                 # CNES-PF 2018-2025 (microdatasus)
│   ├── sidra-campos/         # IBGE/SIDRA (Censo, PIB, população)
│   ├── ibge/                 # CEMPRE, Finanças públicas
│   ├── despesas campos/      # Portal da Transparência (2020-2024)
│   ├── ips-brasil/           # IPS Brasil 2024, 2025, 2026
│   ├── beneficios-inss/      # INSS - Benefícios Concedidos (2018-2025)
│   └── smartlab/             # SmartLab/MPT - Trabalho Decente (2010-2026)
├── artigos-fonte/            # 6 PDFs de referência (ver abaixo)
├── dados/processados/        # Dados processados
├── dados/manifesto/          # Manifesto de arquivos (hashes)
├── documentos/               # Artigo .docx e .pdf
├── apresentacao/             # Slides RMarkdown (ioslides)
├── saidas/
│   ├── tabelas/              # Tabelas finais (CSV)
│   └── figuras/              # Figuras (PNG + SVG)
├── scripts/pipeline/         # 16 scripts numerados
├── logs/                     # Logs de execução
├── metadados/                # Dicionários, matriz de revisão
├── testes/                   # Testes automatizados (pytest)
└── referencias/              # Tabela de referências ABNT
```

---

## Referências bibliográficas

| # | Referência | PDF |
|---|-----------|-----|
| 1 | BRASIL. Lei nº 8.213, de 24 de julho de 1991. | — |
| 2 | BRASIL. Lei nº 9.478, de 6 de agosto de 1997. | — |
| 3 | MARTINS, S.; HASENCLEVER, L.; MIRANDA, C. A gestão da saúde à luz da instabilidade de financiamento... **Cad. Desenvolv. Fluminense**, n. 27, 2024. | `Martins et al. - A gestao da saude a luz da instabilidade de financiamento.pdf` |
| 4 | SILVA, J. E. M.; HASENCLEVER, L. Ciclo do petróleo e desenvolvimento socioeconômico... **Desenvolvimento em Questão**, v. 17, n. 46, 2019. | `Silva e Hasenclever - Ciclo do petroleo e desenvolvimento socioeconomico.pdf` |
| 5 | SOUZA, D. O.; MELO, A. I. S. C.; VASCONCELLOS, L. C. F. Saúde do(s) trabalhador(es): do 'campo' à 'questão'... **Saúde em Debate**, v. 41, n. 113, 2017. | `Souza et al. - Saude do trabalhador do campo a questao.pdf` |
| 6 | VEDOVATO, T. G. et al. Trabalhadores(as) da saúde e a COVID-19... **Rev. Bras. Saúde Ocup.**, v. 46, 2021. | `Vedovato et al. - Trabalhadores da saude e a COVID-19.pdf` |
| 7 | FRANÇA, M. J. P. O pensamento de Antônio Gramsci na luta pela Saúde do Trabalhador. **Em Pauta**, v. 11, n. 32, 2014. | `Franca - O pensamento de Antonio Gramsci na luta pela Saude do Trabalhador.pdf` |
| 8 | OLIVEIRA, E. M. Transformações no mundo do trabalho, da Revolução Industrial aos nossos dias. **Caminhos de Geografia**, v. 6, n. 11, p. 84-96, 2004. | `Oliveira - Transformacoes no mundo do trabalho.pdf` |

---

## Pipeline de processamento

| Script | Função |
|--------|--------|
| `01_inventario.py` | Inventaria os 58 arquivos CAT (esquema, codificação, datas) |
| `02_ingestao_cat.py` | Leitura posicional, hash SHA-256, detecção de duplicidades |
| `03_processamento_campos.py` | Filtro municipal (330100 + UF=RJ), limpeza, parsing |
| `04_dicionario_cbo_classificacao.py` | Dicionário auditado de 458 CBOs, classificação |
| `05_analises.py` | Análises descritivas, tabelas e figuras |
| `06_validacao_independente.py` | Rotina independente (convergência integral) |
| `07_entregaveis.py` | Tabelas e gráficos finais |
| `08_relatorios_docx.py` | Relatórios complementares em DOCX |
| `09_artigo_docx.py` | Artigo (A4, Times New Roman 11, espaçamento 1,5) |
| `10_denominadores_cnes.R` | CNES-PF via microdatasus (R) |
| `11_denominadores_rais.py` | RAIS (vínculos celetistas, denominadores comensuráveis) |
| `12_sim_mortalidade.R` | SIM/DATASUS via microdatasus (R) |
| `13_series_temporais.py` | Decomposição, Mann-Kendall, ADF, LOESS, ARIMA |
| `14_redes_associacao.py` | Apriori, grafos bipartidos, V de Cramér, razões de prevalência |
| `15_ips_campos.py` | IPS Brasil 2024-2025-2026, filtro Campos |
| `16_sinan_download.py` | Download SINAN via FTP DATASUS (46 .dbc, 9 agravos) |

---

## Artigo

- **Título:** Panorama da saúde do trabalhador em Campos dos Goytacazes (RJ)
- **Formato:** A4, Times New Roman 11, espaçamento 1,5, margens 2,5 cm, recuo 1,25 cm
- **10 páginas**, 7 tabelas, 5 figuras, 8 referências
- **Sem resumo**. Sem travessão, meia-risca ou dois-pontos no corpo do texto. Sem projeções.
- Arquivos: `documentos/artigo.docx` e `documentos/artigo.pdf`

---

## Apresentação

Slides em RMarkdown (ioslides): `apresentacao/slides.Rmd`

---

## Como reproduzir

```bash
# Pipeline CAT
python scripts/pipeline/01_inventario.py
python scripts/pipeline/02_ingestao_cat.py
python scripts/pipeline/03_processamento_campos.py
python scripts/pipeline/04_dicionario_cbo_classificacao.py
python scripts/pipeline/05_analises.py
python scripts/pipeline/06_validacao_independente.py
python scripts/pipeline/07_entregaveis.py

# Denominadores
Rscript scripts/pipeline/10_denominadores_cnes.R
python scripts/pipeline/11_denominadores_rais.py
Rscript scripts/pipeline/12_sim_mortalidade.R

# Análises complementares
python scripts/pipeline/13_series_temporais.py
python scripts/pipeline/14_redes_associacao.py
python scripts/pipeline/15_ips_campos.py
python scripts/pipeline/16_sinan_download.py

# Artigo
python scripts/pipeline/09_artigo_docx.py

# Testes
python -m pytest tests/ -v
```

---

## Licença

MIT.

## Citação

SANTOS, Ryan. **Panorama da saúde do trabalhador em Campos dos Goytacazes (RJ)**. 2026. `github.com/santosry/estudo_teorico_saude_do_trabalhador`.
