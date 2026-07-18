# -*- coding: utf-8 -*-
"""
empacotar_dados_brutos.py — Empacota os 58 CSV CAT/INSS (não versionáveis no Git) em ZIPs
por ano de competência, prontos para anexar a uma release do GitHub (limite 2 GB/arquivo)
ou a um depósito Zenodo. Gera SHA-256 dos ZIPs em metadados/SHA256SUMS_distribuicao.txt.
Nenhum dado é alterado: os ZIPs contêm os bytes originais (hashes do manifesto preservados).
"""
import os, re, sys, hashlib, zipfile, datetime

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
ORIGEM = os.path.join("dados", "brutos", "cat-inss")
DESTINO = "distribuicao"

GRUPOS = {  # nome_zip -> função que decide se o arquivo pertence ao grupo
    "cat-inss-2018-2020": lambda n: bool(re.search(r"(2018|2019|2020)", n)) and not n.startswith("D.SDA"),
    "cat-inss-2021-2022": lambda n: bool(re.match(r"D\.SDA\.PDA\.005\.CAT\.202[12]", n)),
    "cat-inss-2023": lambda n: bool(re.match(r"D\.SDA\.PDA\.005\.CAT\.2023", n)),
    "cat-inss-2024": lambda n: bool(re.match(r"D\.SDA\.PDA\.005\.CAT\.2024", n)),
    "cat-inss-2025": lambda n: bool(re.match(r"D\.SDA\.PDA\.005\.CAT\.2025", n)),
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def main():
    if not os.path.isdir(ORIGEM):
        sys.exit(f"BLOQUEIO: {ORIGEM} inexistente — nada a empacotar (nenhum dado é inventado).")
    arquivos = sorted(f for f in os.listdir(ORIGEM) if f.lower().endswith(".csv"))
    if len(arquivos) != 58:
        print(f"AVISO: esperados 58 CSV, encontrados {len(arquivos)} — empacotando o que existe.")
    os.makedirs(DESTINO, exist_ok=True)

    atribuidos = set()
    linhas_sums = []
    for nome_zip, pertence in GRUPOS.items():
        membros = [f for f in arquivos if pertence(f)]
        atribuidos.update(membros)
        if not membros:
            continue
        zpath = os.path.join(DESTINO, nome_zip + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for m in membros:
                z.write(os.path.join(ORIGEM, m), arcname=m)
        mb = round(os.path.getsize(zpath) / 1e6, 1)
        linhas_sums.append(f"{sha256(zpath)}  {nome_zip}.zip  ({len(membros)} arquivos, {mb} MB)")
        print(f"{nome_zip}.zip: {len(membros)} arquivos, {mb} MB")

    sobras = set(arquivos) - atribuidos
    if sobras:
        sys.exit(f"ERRO: arquivos não atribuídos a nenhum grupo: {sorted(sobras)}")

    with open(os.path.join("metadados", "SHA256SUMS_distribuicao.txt"), "w", encoding="utf-8") as f:
        f.write(f"# ZIPs de distribuição dos brutos CAT/INSS — gerados em {datetime.date.today().isoformat()}\n")
        f.write("# Conferência dos CSVs individuais: dados/manifesto/manifesto_arquivos.csv (SHA-256)\n")
        f.write("\n".join(linhas_sums) + "\n")
    print("\nPublicação (exemplos):")
    print("  gh release create v1.0.0 distribuicao/*.zip -t 'Dados brutos CAT/INSS 2018-2025' "
          "-n 'CSVs originais do INSS/PDA; conferir hashes em metadados/SHA256SUMS_distribuicao.txt'")
    print("  (ou depósito Zenodo, obtendo DOI; citar a política de dados abertos do INSS)")

if __name__ == "__main__":
    main()
