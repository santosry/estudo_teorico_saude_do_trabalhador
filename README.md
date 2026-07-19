# Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes

Estudo teórico-conceitual e documental com pipeline reprodutível e auditado. Analisa as Comunicações de Acidente de Trabalho (CAT) do INSS entre profissões da saúde, à luz da formação histórico-social do município, do duplo regime previdenciário (RPPS e INSS) e dos indicadores de mortalidade, finanças públicas e progresso social.

---

## Fontes de dados

| Base | Fonte | Período | Método | Valor-chave no estudo |
|------|-------|---------|--------|----------------------|
| **CAT/INSS** | Portal de Dados Abertos | jul/2018 a out/2025 (58 arquivos) | Download CSV, leitura posicional (4 esquemas) | **1.144 CATs** de profissões da saúde; **84,4%** enfermagem |
| **RAIS/PDET** | FTP do MTE | 2018-2025 (8 anos) | `ftplib`, `py7zr`, auto-detecção de delimitador | **1.099 a 1.393** médicos celetistas ativos; denominadores comensuráveis |
| **SIM/DATASUS** | `microdatasus` (R, v2.5.0) | 2019-2024 (6 anos) | Download .DBC, conversão `read.dbc` | **4.199 a 5.635** óbitos/ano; **10,9/1.000** em 2021 |
| **CNES-PF** | `microdatasus` (R) | 2018-2025 (8 anos) | Download .DBC, filtragem CODUFMUN | **13.839** profissionais (2018); **18.382** (2025) |
| **IBGE/SIDRA** | SIDRA | Censo 2022 + estimativas | Download CSV | **483.540** hab.; IDHM **0,716**; PIB per capita **R$ 88.831** |
| **CEMPRE** | IBGE Cidades | 2024 | Download CSV | **16.776** empresas; saúde: **1.544** estab. / **15.002** pessoas |
| **Siconfi/STN** | Siconfi | 2013-2024 | Download CSV | Receitas **R$ 2,95 bi** (71% transferências); despesas **R$ 3,31 bi** |
| **Portal da Transparência** | Prefeitura de Campos | 2020-2024 | Download CSV (despesas por natureza) | RPPS: **R$ 61,2 mi**; INSS: **R$ 18,3 mi**; déficit atuarial: **R$ 2,5 mi** |
| **IPS Brasil** | IPS Brasil | 2026 | Download CSV | IPS **62,68**/100; Oportunidades **48,6**; Segurança Pessoal **52,8** |

### Notas

- **CAT e RAIS** capturam vínculos celetistas. Denominadores **comensuráveis**.
- **CNES-PF** inclui estatutários, autônomos e PJ. Razões **exploratórias**.
- **RPPS municipal**: sem base nacional de acidentes/adoecimentos de estatutários. Registros no PREVICAMPOS, não publicizados como microdados.
- **RAIS 2023-2025**: delimitador mudou de `;` para `,`. Pipeline detecta automaticamente.

---

## Estrutura do repositório

```
├── cat-inss/                 # 58 CSVs da CAT (jul/2018 a out/2025)
├── rais/                     # RAIS 2018-2025 (microdados, 7z)
├── sim/                      # SIM 2019-2024 (CSVs processados)
├── cnes/                     # CNES-PF 2018-2025 (microdatasus)
├── sidra-campos/             # IBGE/SIDRA (Censo, PIB, população)
├── ibge/                     # CEMPRE, Finanças públicas
├── despesas campos/          # Portal da Transparência (2020-2024)
├── ips-brasil/               # IPS Brasil 2026
├── artigos-fonte/            # 9 PDFs de referência (ver abaixo)
├── dados/processados/        # Dados processados
├── dados/manifesto/          # Manifesto de arquivos (hashes)
├── documentos/               # Artigo .docx e .pdf
├── apresentacao/             # Slides RMarkdown (ioslides)
├── saidas/
│   ├── tabelas/              # 33 tabelas finais (CSV)
│   └── figuras/              # Figuras (PNG + SVG)
├── scripts/pipeline/         # 12 scripts numerados
├── logs/                     # Logs de execução
├── metadados/                # Dicionários, matriz de revisão
├── testes/                   # 38 testes automatizados (pytest)
└── referencias/              # Tabela de referências ABNT
```

---

## Referências bibliográficas

| # | Referência | PDF |
|---|-----------|-----|
| 1 | ANTUNES, Ricardo. **O privilégio da servidão**: o novo proletariado de serviços na era digital. São Paulo: Boitempo, 2018. | `Antunes - O privilegio da servidao.pdf` |
| 2 | CECÍLIO, Luiz Carlos de Oliveira; LACAZ, Francisco de Castro. **O trabalho em saúde**. Rio de Janeiro: Cebes, 2012. | `Costa et al. - O trabalho em saude.pdf` |
| 3 | LEMOS, Marcelo Rodrigues. Estratificação social na teoria de Max Weber: considerações em torno do tema. **Revista Iluminart**, Sertãozinho, ano 4, n. 9, p. 113-128, nov. 2012. | `Lemos - Estratificacao social na teoria de Max Weber.pdf` |
| 4 | LOURENÇO, Guilherme Grandi. O fim do fim do trabalho: uma crítica à chamada sociedade pós-industrial e sua relação com os movimentos de trabalhadores. **Primeiros Estudos**, São Paulo, n. 3, p. 104-121, 2012. | `Lourenco - O fim do fim do trabalho.pdf` |
| 5 | MARTINS, Samuel; HASENCLEVER, Lia; MIRANDA, Caroline. A gestão da saúde à luz da instabilidade de financiamento e das propostas de governo. **Cadernos do Desenvolvimento Fluminense**, Rio de Janeiro, n. 27, 2024. | `Martins et al. - A gestao da saude a luz da instabilidade de financiamento.pdf` |
| 6 | MENDES, René; DIAS, Elizabeth Costa. Da medicina do trabalho à saúde do trabalhador. **Revista de Saúde Pública**, São Paulo, v. 25, n. 5, p. 341-349, 1991. | `Mendes e Dias - Da medicina do trabalho a saude do trabalhador.pdf` |
| 7 | OLIVEIRA, Elisângela Magela. Transformações no mundo do trabalho, da Revolução Industrial aos nossos dias. **Caminhos de Geografia**, Uberlândia, v. 6, n. 11, p. 84-96, fev. 2004. | `Oliveira - Transformacoes no mundo do trabalho.pdf` |
| 8 | SILVA, José Eduardo Matias da; HASENCLEVER, Lia. Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes (1999-2014). **Desenvolvimento em Questão**, Ijuí, v. 17, n. 46, p. 314-332, 2019. | `Silva e Hasenclever - Ciclo do petroleo e desenvolvimento socioeconomico.pdf` |
| 9 | VEDOVATO, Tatiana Giovanelli; ANDRADE, Cristiane Batista; SANTOS, Daniela Lacerda; BITENCOURT, Silvana Maria; ALMEIDA, Leticia Passos de; SAMPAIO, Juliana Ferreira da Silva. Trabalhadores(as) da saúde e a COVID-19: condições de trabalho à deriva? **Revista Brasileira de Saúde Ocupacional**, São Paulo, v. 46, e1, 2021. | `Vedovato et al. - Trabalhadores da saude e a COVID-19.pdf` |

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

---

## Auditoria

- **938 registros duplicados removidos** (401 hashes SHA-256)
- **12 registros excluídos** por UF divergente
- **458 códigos CBO** com dicionário auditado
- **184 registros sem CBO válido** (3,6%)
- **38 testes automatizados** (pytest)
- **9 referências verificadas** nos PDFs fonte, 6 divergências corrigidas
- Verificação de travessão/meia-risca proibidos
- Verificação automática de páginas via LibreOffice

---

## Artigo

- **Título:** Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes
- **Formato:** A4, Times New Roman 11, espaçamento 1,5, margens 2,5 cm
- **9 páginas**, 6 tabelas, 2 figuras, 9 referências
- **Normas:** Citações (Mendes e Dias, 1991); ABNT NBR 6023:2025
- Arquivos: `documentos/artigo.docx` e `documentos/artigo.pdf`

---

## Apresentação

Slides em RMarkdown (ioslides): `apresentacao/slides.Rmd`

```bash
cd apresentacao
Rscript -e "rmarkdown::render('slides.Rmd')"
```

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

# Artigo
python scripts/pipeline/09_artigo_docx.py

# Testes
python -m pytest tests/ -v
```

---

## Licença

MIT.

## Citação

SANTOS, Ryan. **Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes**. 2026. `github.com/santosry/estudo_teorico_saude_do_trabalhador`.
