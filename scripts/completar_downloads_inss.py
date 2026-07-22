# -*- coding: utf-8 -*-
"""
completar_downloads_inss.py
===========================
Script para completar os downloads pendentes do portal de dados abertos do INSS.
Executa apenas os datasets que ainda não foram totalmente baixados.

Executar APÓS restaurar os dados com scripts/restaurar_dados_locais.sh.

USO:
    python scripts/completar_downloads_inss.py [--dataset mantidos|emitidos|indeferidos|todos]
"""
import subprocess
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), ".."))

DATASETS_PENDENTES = {
    "concedidos_2024_2025": (
        "Benefícios Concedidos (completar 2024-2025)",
        ["concedidos"]
    ),
    "mantidos": (
        "Benefícios Mantidos (Ativos/Suspensos/Cessados)",
        ["mantidos"]
    ),
    "emitidos": (
        "Benefícios Emitidos (folha de pagamento)",
        ["emitidos"]
    ),
    "indeferidos": (
        "Benefícios Indeferidos",
        ["indeferidos"]
    ),
    "glossarios": (
        "Glossários (dicionários de variáveis)",
        ["glossarios"]
    ),
}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Completar downloads pendentes do INSS")
    parser.add_argument("--dataset", choices=list(DATASETS_PENDENTES.keys()) + ["todos"],
                        default="todos", help="Dataset a baixar")
    args = parser.parse_args()

    if args.dataset == "todos":
        pendentes = list(DATASETS_PENDENTES.keys())
    else:
        pendentes = [args.dataset]

    for key in pendentes:
        nome, datasets = DATASETS_PENDENTES[key]
        print(f"\n{'='*60}")
        print(f"  {nome}")
        print(f"{'='*60}")

        for ds in datasets:
            cmd = [sys.executable, "scripts/download_inss_completo.py", "--dataset", ds]
            print(f"  Executando: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=os.getcwd())
            if result.returncode != 0:
                print(f"  [ERRO] Falha ao baixar {ds}")
            else:
                print(f"  [OK] {ds} concluído")

        # Após cada dataset, commit e push
        print(f"\n  Fazendo commit e push do dataset {key}...")
        subprocess.run(["git", "add", "-A"], check=False)
        subprocess.run(["git", "commit", "-m", f"feat: completa download INSS - {nome}"], check=False)
        subprocess.run(["git", "push", "origin", "main"], check=False)

    print("\n[OK] Downloads pendentes concluídos.")

if __name__ == "__main__":
    main()
