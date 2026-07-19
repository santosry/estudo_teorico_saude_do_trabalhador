# Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes

Estudo teórico-conceitual e documental com pipeline reprodutível e auditado. Analisa as Comunicações de Acidente de Trabalho (CAT) do INSS entre profissões da saúde, à luz da formação histórico-social do município, do duplo regime previdenciário (RPPS e INSS) e dos indicadores de mortalidade e finanças públicas.

---

## Fontes de dados

| Base | Fonte | Período | Método | Variáveis principais | Valor-chave no estudo |
|------|-------|---------|--------|---------------------|----------------------|
| **CAT/INSS** | Portal de Dados Abertos ([dados.gov.br](https://dados.gov.br)) | jul/2018 a out/2025 (58 arquivos) | Download direto CSV, leitura posicional (4 esquemas) | CBO, CID-10, CNAE, data do acidente, município do empregador, sexo, tipo de acidente | **1.144 CATs** de profissões da saúde em Campos; **84,4%** concentrados na enfermagem |
| **RAIS/PDET** | FTP do MTE ([ftp.mtps.gov.br](ftp://ftp.mtps.gov.br/pdet/microdados/RAIS)) | 2018-2025 (8 anos) | `ftplib` (Python), extração `py7zr`, streaming, auto-detecção de delimitador (`;` ou `,`) | CBO 2002 (col. 7), CNAE 2.0 (col. 8), Vínculo Ativo 31/12 (col. 11), Município (col. 25) | **1.099 a 1.393** médicos celetistas ativos em Campos; denominadores comensuráveis com a CAT |
| **SIM/DATASUS** | FTP do DATASUS + `microdatasus` (R, v2.5.0) | 2019-2024 (6 anos) | Download .DBC, conversão via `read.dbc` (CRAN), filtragem CODMUNRES = 330100 | CAUSABAS (CID-10), CODMUNRES, IDADE, SEXO | **4.199 a 5.635** óbitos/ano; **10,9/1.000** em 2021 (pico); infecciosas como 1ª causa |
| **CNES** | TABNET/DATASUS ([tabnet.datasus.gov.br](http://tabnet.datasus.gov.br)) | dez/2018 a dez/2025 | Download manual CSV pelo TABNET | CBO 2002, quantidade de profissionais, competência | **9.803** profissionais em 2018; **13.275** em 2025; razões exploratórias CAT/CNES |
| **IBGE/SIDRA** | [SIDRA](https://sidra.ibge.gov.br) | Censo 2022 + estimativas | Download manual CSV | População, PIB, área, densidade, alfabetização | **483.540** hab. (2022); IDHM **0,716**; PIB per capita **R$ 88.831** |
| **CEMPRE** | [IBGE Cidades](https://cidades.ibge.gov.br) | 2024 | Download manual CSV | Empresas, pessoal ocupado, salários, setor CNAE | **16.776** empresas; saúde: **1.544** estab. / **15.002** pessoas |
| **Siconfi/STN** | [Siconfi](https://siconfi.tesouro.gov.br) | 2013-2024 | Download manual CSV | Receitas, despesas, transferências | Receitas **R$ 2,95 bi** (71% transferências); despesas **R$ 3,31 bi** |
| **Portal da Transparência** | [Prefeitura de Campos](https://transparencia.campos.rj.gov.br) | 2020-2024 | Download manual CSV (despesas por natureza econômica) | Contribuições patronais RPPS e INSS, pessoal, custeio | RPPS: **R$ 61,2 mi** (estatutários); INSS: **R$ 18,3 mi** (celetistas); déficit atuarial RPPS: **R$ 2,5 mi** |

### Notas sobre as fontes

- **CAT e RAIS** capturam majoritariamente vínculos celetistas. Seus denominadores são **comensuráveis** (mesmo universo).
- **CNES** inclui estatutários, autônomos e PJ, não cobertos pela CAT. Gera apenas **razões exploratórias**.
- **SIM** foi processado com o pacote R `microdatasus` (GitHub `rfsaldanha/microdatasus`), que baixa arquivos .DBC do FTP do DATASUS e os converte com `read.dbc`.
- **RPPS municipal**: não há base nacional consolidada de acidentes e adoecimentos de servidores estatutários. Os dados de contribuições previdenciárias foram obtidos do Portal da Transparência, mas os registros de afastamentos por acidente/doença de estatutários não são publicizados como microdados.
- **RAIS 2023-2025**: o delimitador mudou de `;` (2018-2022) para `,` (2023+). O pipeline detecta automaticamente.

---

## Estrutura do repositório

```
.
├── scripts/pipeline/          # 12 scripts numerados
├── dados/
│   ├── brutos/                # Dados brutos baixados
│   │   ├── cat-inss/          # 58 CSVs da CAT (jul/2018 a out/2025)
│   │   ├── rais/              # RAIS (microdados de vínculos, 7z)
│   │   ├── sim/               # SIM (óbitos, CSVs processados)
│   │   ├── cnes-rh/           # CNES (profissionais por ocupação)
│   │   ├── sidra-campos/      # IBGE/SIDRA (Censo, PIB, população)
│   │   └── ibge/              # CEMPRE, Finanças públicas
│   ├── processados/           # Dados processados
│   └── manifesto/             # Manifesto de arquivos (hashes)
├── despesas campos/           # Portal da Transparência (2020-2024)
├── saidas/
│   ├── tabelas/               # Tabelas finais (CSV)
│   └── figuras/               # Figuras (PNG + SVG)
├── documentos/                # Artigo .docx e .pdf
├── apresentacao/              # Slides RMarkdown (ioslides)
├── logs/                      # Logs de execução
├── metadados/                 # Dicionários, matriz de revisão teórica
├── testes/                    # 38 testes automatizados (pytest)
└── artigos-fonte/             # PDFs de artigos de referência
```

---

## Pipeline de processamento

| Script | Função |
|--------|--------|
| `01_inventario.py` | Inventaria os 58 arquivos CAT (esquema, codificação, datas) |
| `02_ingestao_cat.py` | Leitura posicional, hash SHA-256, detecção de duplicidades |
| `03_processamento_campos.py` | Filtro municipal (330100 + UF=RJ), limpeza, parsing de datas |
| `04_dicionario_cbo_classificacao.py` | Dicionário auditado de 458 CBOs, classificação em universos |
| `05_analises.py` | Análises descritivas, tabelas e figuras |
| `06_validacao_independente.py` | Rotina independente de verificação (convergência integral) |
| `07_entregaveis.py` | Geração das tabelas e gráficos finais |
| `08_relatorios_docx.py` | Relatórios complementares em DOCX |
| `09_artigo_docx.py` | Geração do artigo (A4, Times New Roman 11, espaçamento 1,5) |
| `10_denominadores_cnes.py` | Denominadores CNES (razões exploratórias) |
| `11_denominadores_rais.py` | Denominadores RAIS (vínculos celetistas, denominadores comensuráveis) |
| `12_sim_mortalidade.R` | SIM/DATASUS via microdatasus (R) — mortalidade e taxas |

---

## Auditoria e qualidade

- **938 registros duplicados removidos** entre arquivos de cobertura sobreposta (401 hashes SHA-256 distintos)
- **12 registros excluídos** por UF divergente do código 330100
- **458 códigos CBO** com dicionário auditado (descrição oficial, família, nível de formação)
- **184 registros sem CBO válido** (3,6%), mantidos em categoria própria
- **38 testes automatizados** (pytest) para classificação e integridade
- Verificação de **travessão/meia-risca** proibidos no texto
- Verificação automática de **número de páginas** via LibreOffice headless

---

## Como reproduzir

### Requisitos
- Python 3.10+ com pandas, py7zr, python-docx, pypdf, dbfread
- R 4.0+ com microdatasus, read.dbc
- LibreOffice (para verificação de páginas do artigo)

### Execução

```bash
# Pipeline CAT completo
python scripts/pipeline/01_inventario.py
python scripts/pipeline/02_ingestao_cat.py
python scripts/pipeline/03_processamento_campos.py
python scripts/pipeline/04_dicionario_cbo_classificacao.py
python scripts/pipeline/05_analises.py
python scripts/pipeline/06_validacao_independente.py
python scripts/pipeline/07_entregaveis.py

# Denominadores
python scripts/pipeline/10_denominadores_cnes.py
python scripts/pipeline/11_denominadores_rais.py

# SIM (mortalidade)
Rscript scripts/pipeline/12_sim_mortalidade.R

# Artigo
python scripts/pipeline/09_artigo_docx.py

# Testes
python -m pytest tests/ -v
```

---

## Artigo

- **Título:** Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes
- **Formato:** A4, Times New Roman 11, espaçamento 1,5, margens 2,5 cm
- **7 páginas** (limite: 8)
- **4 tabelas + 2 figuras + 9 referências**
- **Normas:** ABNT NBR 10520:2023 (citações), ABNT NBR 6023:2025 (referências)
- Arquivos: `documentos/artigo.docx` e `documentos/artigo.pdf`

---

## Apresentação

Slides em RMarkdown (formato ioslides): `apresentacao/slides.Rmd`

```bash
cd apresentacao
Rscript -e "rmarkdown::render('slides.Rmd')"
```

---

## Licença

MIT.

## Citação

SANTOS, Ryan. **Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes**. 2026. `github.com/santosry/estudo_te-rico-sa-de_do_trabalhador`.
