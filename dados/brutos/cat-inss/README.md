# Dados brutos CAT/INSS (não versionados)

Os 58 arquivos CSV (competências jul/2018–dez/2025; ~1,8 GB; 3.902.905 linhas) **não são
versionados** no Git (limites do GitHub). Para reproduzir:

1. Baixe os conjuntos "Comunicação de Acidente de Trabalho – CAT" no Portal de Dados Abertos
   (https://dados.gov.br/dados/conjuntos-dados/inss-comunicacao-de-acidente-de-trabalho-cat)
   e/ou nas páginas da Previdência/INSS, cobrindo as competências jul/2018 a dez/2025.
2. Coloque os CSVs nesta pasta com os nomes listados em `../../manifesto/manifesto_arquivos.csv`.
3. Confira a integridade: os hashes SHA-256 de cada arquivo estão no mesmo manifesto.
4. Execute o pipeline a partir de `scripts/pipeline/01_inventario.py`.

O dicionário oficial da fonte está versionado em `referencias/dicionario-cat-dados-abertos-10-02-2021.xlsx`.
