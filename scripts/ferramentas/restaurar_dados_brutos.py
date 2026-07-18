# -*- coding: utf-8 -*-
"""
restaurar_dados_brutos.py — Restaura os CSV CAT/INSS a partir dos ZIPs de distribuição
(pasta distribuicao/ ou caminho passado como argumento) e VERIFICA cada CSV contra o
SHA-256 do manifesto (dados/manifesto/manifesto_arquivos.csv) antes de liberar a reprodução.
Uso:
    python scripts/ferramentas/restaurar_dados_brutos.py [pasta_com_zips]
"""
import os, sys, csv, hashlib, zipfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
DESTINO = os.path.join("dados", "brutos", "cat-inss")
MANIFESTO = os.path.join("dados", "manifesto", "manifesto_arquivos.csv")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "distribuicao"
    zips = sorted(os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".zip")) \
        if os.path.isdir(pasta) else []
    if not zips:
        sys.exit(f"BLOQUEIO: nenhum ZIP em '{pasta}'. Baixe os assets da release "
                 f"(gh release download v1.0.0 -D distribuicao) e rode novamente.")
    os.makedirs(DESTINO, exist_ok=True)
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            zf.extractall(DESTINO)
        print(f"extraído: {z}")

    esperados = {}
    with open(MANIFESTO, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if "cat-inss" in r["caminho_relativo"] and r["nome"].lower().endswith(".csv"):
                esperados[r["nome"]] = r["sha256"]
    if not esperados:
        sys.exit("BLOQUEIO: manifesto sem entradas cat-inss — verifique o repositório.")

    falhas, ausentes, ok = [], [], 0
    for nome, h in sorted(esperados.items()):
        p = os.path.join(DESTINO, nome)
        if not os.path.exists(p):
            ausentes.append(nome)
        elif sha256(p) != h:
            falhas.append(nome)
        else:
            ok += 1
    print(f"\nVerificação: {ok}/{len(esperados)} CSVs íntegros.")
    if ausentes:
        print("AUSENTES:", ausentes)
    if falhas:
        print("HASH DIVERGENTE (dados corrompidos/alterados):", falhas)
    if ausentes or falhas:
        sys.exit("BLOQUEIO: restauração incompleta — NÃO execute o pipeline com dados não íntegros.")
    print("Dados brutos restaurados e íntegros. Pipeline liberado (scripts/pipeline/01...).")

if __name__ == "__main__":
    main()
