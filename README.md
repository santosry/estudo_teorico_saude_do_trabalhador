# Saúde do Trabalhador em Campos dos Goytacazes — CAT/INSS 2018–2025

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
