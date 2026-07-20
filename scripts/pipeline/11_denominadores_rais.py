# -*- coding: utf-8 -*-
"""
11_denominadores_rais.py — Denominadores REAIS de vínculos FORMAIS (celetistas) RAIS/PDET,
Campos dos Goytacazes (330100), 2018–2025. RAIS identificada (CSV, delimitador ";"), com
layout verificado empiricamente para 2018–2024 (colunas 7=CBO, 8=CNAE 2.0 classe,
11=vínculo ativo em 31/12, 24=município). Download de ftp.mtps.gov.br via FTP, extração
com py7zr e filtragem em streaming (arquivo salvo em disco temporário, removido ao final
a menos que KEEP_RAIS_7Z=1). Compatibilidade numerador–denominador DEMONSTRÁVEL: CAT e RAIS
são celetistas.
"""
import os, csv, json, datetime, ftplib, time, tempfile, py7zr
from collections import defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

FTP_HOST = "ftp.mtps.gov.br"
FTP_DIR = "pdet/microdados/RAIS"
ARQ_RAIS = "RAIS_VINC_PUB_MG_ES_RJ.7z"
MUN_COD = "330100"
DIR_RAIS = os.path.join("dados", "brutos", "banco de dados/rais")
os.makedirs(DIR_RAIS, exist_ok=True)
COL = {"cbo": 7, "cnae": 8, "ativo": 11, "mun": 24}

def classifica(cbo):
    fam = cbo[:4] if cbo else ""
    mapa = {"2235": "Enfermagem – enfermeiros", "3222": "Enfermagem – técnicos e auxiliares",
            "2251": "Medicina", "2252": "Medicina", "2253": "Medicina", "2231": "Medicina",
            "2236": "Fisioterapia", "2234": "Farmácia", "3251": "Farmácia – técnicos e auxiliares",
            "2237": "Nutrição", "2238": "Fonoaudiologia", "2232": "Odontologia e saúde bucal",
            "3224": "Odontologia e saúde bucal", "3241": "Diagnóstico e laboratório – técnicos e auxiliares",
            "3242": "Diagnóstico e laboratório – técnicos e auxiliares",
            "5152": "Diagnóstico e laboratório – técnicos e auxiliares",
            "5151": "Agentes comunitários de saúde e afins",
            "3226": "Instrumentação cirúrgica", "515140": "Agentes de combate às endemias",
            "515210": "Farmácia – técnicos e auxiliares",
            "2515": "Psicologia", "2516": "Serviço social",
            "2241": "Educação física", "2211": "Biologia", "2212": "Biomedicina"}
    if cbo in ("515225", "519305", "223310"): return ("apoio", None)
    if cbo in ("322225", "515140", "515210", "223305"):
        ov = {"322225": "Instrumentação cirúrgica", "515140": "Agentes de combate às endemias",
              "515210": "Farmácia – técnicos e auxiliares", "223305": "Medicina veterinária"}
        return ("principal", ov[cbo])
    r = mapa.get(fam)
    return ("principal", r) if r else ("apoio", None)

def baixar(ano):
    local = os.path.join(DIR_RAIS, f"RAIS_{ano}_MG_ES_RJ.7z")
    if os.path.exists(local):
        print(f"  {ano}: já existe ({round(os.path.getsize(local)/1e6,1)} MB)")
        return local
    print(f"  {ano}: baixando... ", end="", flush=True)
    f = ftplib.FTP(FTP_HOST, timeout=60); f.login(); f.cwd(f"{FTP_DIR}/{ano}")
    sz = f.size(ARQ_RAIS)
    tmp = local + ".part"
    with open(tmp, "wb") as fh:
        f.retrbinary(f"RETR {ARQ_RAIS}", fh.write, blocksize=1 << 20)
    f.quit()
    os.rename(tmp, local)
    print(f"concluído ({round(os.path.getsize(local)/1e6,1)} MB)")
    return local

def extrair(ano, path):
    inicio = time.time()
    contador = defaultdict(int)
    with tempfile.TemporaryDirectory() as td:
        with py7zr.SevenZipFile(path, "r") as z:
            z.extractall(td)
        txts = [f for f in os.listdir(td) if f.upper().endswith(".TXT") or f.upper().endswith(".COMT")]
        if not txts:
            txts = [f for f in os.listdir(td) if not f.startswith('.')]
        if not txts:
            raise RuntimeError(f"Nenhum arquivo no 7z de {ano}: {os.listdir(td)[:10]}")
        with open(os.path.join(td, txts[0]), "r", encoding="latin-1", errors="replace") as fh:
            header_line = fh.readline()
            # Auto-detectar delimitador: 2018-2022 usa ';', 2023+ usa ','
            delim = ',' if header_line.count(',') > header_line.count(';') else ';'
            fh.seek(0)
            rd = csv.reader(fh, delimiter=delim, quotechar='"')
            next(rd)  # cabeçalho
            for row in rd:
                try:
                    if len(row) <= max(COL.values()): continue
                    if row[COL["mun"]].strip() != MUN_COD: continue
                    if row[COL["ativo"]].strip() != "1": continue
                    cbo = row[COL["cbo"]].strip()
                    if not cbo[:1].isdigit(): continue
                    cnae_div = row[COL["cnae"]].strip()[:2]
                    u, cat = classifica(cbo)
                    if u != "principal" or cat is None: continue
                    contador[cat] += 1
                except Exception:
                    pass
    t = time.time() - inicio
    print(f"  {ano}: {sum(contador.values())} vínculos ativos de saúde em Campos (extraído em {t:.0f}s)")
    return contador

def main():
    prov = {"fonte": "RAIS/PDET/MTE (ftp.mtps.gov.br)", "layout": "CSV, delimitador ';', colunas verificadas empiricamente para 2018–2024",
            "filtro": "mun 330100, ativo 31/12 (col 11=1), categorias saúde CBO", "execucao": datetime.datetime.now().isoformat(), "bloqueios": []}
    anos = list(range(2018, 2026))
    rais = {}
    for ano in anos:
        try:
            path = baixar(ano)
            cont = extrair(ano, path)
            rais[ano] = cont
        except ftplib.error_perm as e:
            prov["bloqueios"].append(f"{ano}: FTP — {e}")
            print(f"  {ano}: BLOQUEIO FTP — {e}")
        except Exception as e:
            prov["bloqueios"].append(f"{ano}: {e}")
            print(f"  {ano}: BLOQUEIO — {e}")
        time.sleep(1)

    if not rais:
        json.dump(prov, open("logs/log_11_denominadores_rais.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        raise SystemExit("BLOQUEIO: nenhum denominador RAIS obtido.")

    # T23
    cats = sorted({c for d in rais.values() for c in d})
    with open("saidas/tabelas/T23_denominadores_rais.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["categoria_estudo"] + [str(a) for a in anos])
        for cat in cats:
            w.writerow([cat] + [rais.get(a, {}).get(cat, 0) for a in anos])

    # T24
    cat_cat = defaultdict(lambda: defaultdict(int))
    with open("dados/processados/base_cat_campos_profissoes_saude_processada.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["universo"] == "principal":
                cat_cat[row["categoria_profissional"]][int(row["ano_acidente"])] += 1
    PARCIAIS = {2018, 2022, 2024, 2025}
    t24_rows = []
    for cat in sorted(cats):
        for ano in anos:
            num = cat_cat[cat].get(ano, 0)
            den = rais.get(ano, {}).get(cat, 0)
            razao = round(1000 * num / den, 1) if den >= 30 and num >= 5 else "supresso (num<5 ou den<30)"
            t24_rows.append({"categoria": cat, "ano": ano, "cat_n": num, "rais_n": den,
                             "razao_por_1000": razao,
                             "cobertura_cat": "parcial*" if ano in PARCIAIS else "integral",
                             "advertencia": "numerador e denominador COMENSURÁVEIS (CAT e RAIS = celetistas)"})
    with open("saidas/tabelas/T24_razao_cat_1000_rais.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(t24_rows[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(t24_rows)

    if not os.environ.get("KEEP_RAIS_7Z"):
        removidos = 0
        for ano in anos:
            p = os.path.join(DIR_RAIS, f"RAIS_{ano}_MG_ES_RJ.7z")
            if os.path.exists(p):
                os.remove(p); removidos += 1
        if removidos:
            print(f"\n{removidos} arquivos 7z removidos (configure KEEP_RAIS_7Z=1 para mantê-los).")

    prov["arquivos"] = ["saidas/tabelas/T23_denominadores_rais.csv", "saidas/tabelas/T24_razao_cat_1000_rais.csv"]
    json.dump(prov, open("logs/log_11_denominadores_rais.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n✓ T23/T24 (RAIS/PDET, denominadores COMENSURÁVEIS) em saidas/tabelas/")

if __name__ == "__main__":
    main()
