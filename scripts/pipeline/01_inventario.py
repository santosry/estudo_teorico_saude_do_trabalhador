# -*- coding: utf-8 -*-
"""
01_inventario.py — Inventário e rastreabilidade dos arquivos-fonte.
Projeto: CAT/INSS — Campos dos Goytacazes — Profissões da saúde (2018–2025)
Executa a partir da raiz do projeto (caminhos relativos).
Saídas: dados/manifesto/manifesto_arquivos.csv (+ xlsx), logs/log_inventario.txt
Nota metodológica: nenhum arquivo SmartLab foi localizado; a etapa SmartLab foi
excluída por decisão metodológica (registrado no manifesto).
"""
import os, csv, hashlib, datetime, sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
PASTAS_FONTE = ["artigos-fonte", "cat-inss", "rais", "sim", "cnes", "sidra-campos", "ibge", "despesas campos", "referencias"]
SAIDA = os.path.join("dados", "manifesto", "manifesto_arquivos.csv")

def sha256(path, bloco=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bloco)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def detecta_csv(path):
    """Detecta codificação provável, separador, nº de colunas e linhas de um CSV."""
    with open(path, "rb") as f:
        ini = f.read(4096)
    enc = "utf-8-sig" if ini.startswith(b"\xef\xbb\xbf") else None
    if enc is None:
        try:
            ini.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            enc = "latin-1"
    with open(path, encoding=enc, errors="replace") as f:
        header = f.readline().rstrip("\r\n")
    sep = ";" if header.count(";") >= header.count(",") else ","
    ncols = len(header.split(sep))
    nlin = 0
    with open(path, "rb") as f:
        for _ in f:
            nlin += 1
    return enc, sep, ncols, nlin - 1  # linhas de dados (sem cabeçalho)

linhas = []
for pasta in PASTAS_FONTE:
    for raiz, _, arquivos in os.walk(pasta):
        for nome in sorted(arquivos):
            p = os.path.join(raiz, nome)
            st = os.stat(p)
            ext = os.path.splitext(nome)[1].lower()
            enc = sep = ncols = nlin = ""
            problema = ""
            try:
                if ext == ".csv":
                    enc, sep, ncols, nlin = detecta_csv(p)
            except Exception as e:
                problema = f"erro_leitura: {e}"
            linhas.append({
                "caminho_relativo": p.replace("\\", "/"),
                "nome": nome, "extensao": ext,
                "tamanho_bytes": st.st_size,
                "modificado_em": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                "codificacao": enc, "separador": sep,
                "n_colunas": ncols, "n_linhas_dados": nlin,
                "smartlab": "NAO — nenhum arquivo SmartLab presente (etapa excluída por decisão metodológica)",
                "problema_leitura": problema,
                "sha256": sha256(p),
            })

os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
with open(SAIDA, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(linhas)
print(f"Inventariados {len(linhas)} arquivos -> {SAIDA}")
