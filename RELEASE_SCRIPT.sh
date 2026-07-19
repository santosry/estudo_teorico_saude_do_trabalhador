#!/bin/bash
# Script de publicação — execute APÓS 'gh auth login' e 'git remote add origin <URL>'
set -e
cd "$(dirname "$0")"

echo "=== Push do código e tag ==="
git push -u origin main
git push origin v1.0.0

echo "=== Criar release e anexar ZIPs dos dados brutos ==="
gh release create v1.0.0 distribuicao/*.zip \
  -t "v1.0.0: CAT/INSS 2018-2025 – Campos dos Goytacazes" \
  -n "$(cat <<'EOF'
Reconstrução integral e auditada da análise das Comunicações de Acidente de Trabalho (CAT/INSS)
vinculadas a empregadores de Campos dos Goytacazes/RJ (código 330100), 2018–2025, para todas as
profissões da saúde (CBO 2002).

**Dados brutos**: os 5 arquivos ZIP anexados contêm os 58 CSVs originais do INSS/PDA (1,8 GB).
Confira a integridade com `metadados/SHA256SUMS_distribuicao.txt` e restaure com:
```bash
python scripts/ferramentas/restaurar_dados_brutos.py distribuicao
```

**Reprodução**: `pip install -r metadados/requirements.txt` + scripts numerados em `scripts/pipeline/`.

**Denominadores**: RAIS/PDET 2018-2023 (comensuráveis com a CAT — celetistas). CNES/TabNet (exploratório).
Tabelas T21-T24 em `saidas/tabelas/`. Artigo final em `documentos/artigo.docx` (≤5 páginas).
EOF
)"

echo "=== Concluído ==="
echo "URL da release: https://github.com/<seu-usuario>/<repo>/releases/tag/v1.0.0"
