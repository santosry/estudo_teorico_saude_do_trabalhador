#!/bin/bash
# restaura_dados_locais.sh
# Restaura os arquivos grandes de dados do Git LFS quando necessário.
# Por padrão, os dados estão armazenados no GitHub via LFS como ponteiros
# (arquivos de ~130 bytes). Este script baixa o conteúdo real.
#
# Uso:
#   bash scripts/restaurar_dados_locais.sh [sinan|caged|cat|beneficios|todos]
#
# Para economia de espaço: após o uso, execute 'git lfs prune' para
# remover objetos não referenciados do cache local.

set -e

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"

restaurar() {
    local DIR="$1"
    local LABEL="$2"
    echo ">>> Restaurando $LABEL..."
    git lfs fetch --all -I "$DIR"
    git checkout -- "$DIR"
    echo "    OK: $LABEL restaurado."
}

case "${1:-todos}" in
    sinan)
        restaurar "dados/brutos/sinan/" "SINAN (Agravos de Notificação)"
        ;;
    caged)
        restaurar "banco de dados/caged/" "CAGED (Admissões/Desligamentos)"
        ;;
    cat)
        restaurar "banco de dados/cat-inss/" "CAT (Acidentes de Trabalho)"
        ;;
    beneficios)
        restaurar "banco de dados/beneficios-concedidos-inss/" "Benefícios Concedidos INSS"
        ;;
    todos|*)
        restaurar "dados/brutos/sinan/" "SINAN"
        restaurar "banco de dados/caged/" "CAGED"
        restaurar "banco de dados/cat-inss/" "CAT"
        restaurar "banco de dados/beneficios-concedidos-inss/" "Benefícios Concedidos"
        ;;
esac

echo ""
echo "=== Dados restaurados. Use 'git lfs prune' para liberar espaço depois. ==="
