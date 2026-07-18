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
```
Caminhos relativos à raiz; sem procedimentos aleatórios; logs em `logs/`.
Os dados brutos da CAT devem ser obtidos conforme `dados/brutos/cat-inss/README.md` e conferidos
pelos hashes de `dados/manifesto/manifesto_arquivos.csv`.

## Advertência interpretativa
CAT = comunicações registradas (emprego formal celetista), não a totalidade dos acidentes; sem
denominadores (RAIS/eSocial-PDET; CNES) não se calculam incidência/risco/taxa. Coberturas parciais
da fonte: 2018 (competências desde jul.), 2022 (carga irregular), 2024 (set–dez atípicos) e 2025
(parcial até out.).
