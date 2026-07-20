# -*- coding: utf-8 -*-
"""
06_validacao_independente.py — Segunda rotina, independente da cadeia 02→05 (pandas),
que reconta os principais totais DIRETAMENTE dos 58 CSV brutos:
  V1 total de linhas lidas; V2 registros 330100+UF RJ (antes da deduplicação);
  V3 após deduplicação entre arquivos (linha bruta idêntica, 1ª competência);
  V4 universo principal saúde; V5 por categoria; V6 por ano.
Compara com os resultados do pipeline e FALHA (exit 1) em caso de divergência.
"""
import os, re, sys, glob, hashlib, unicodedata, datetime, json
import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

def enc_de(path):
    with open(path, "rb") as f:
        return "utf-8-sig" if f.read(4).startswith(b"\xef\xbb\xbf") else "latin-1"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()

FAM_PRINCIPAL = {"2231", "2251", "2252", "2253", "2235", "2232", "2234", "2236", "2237", "2238",
                 "2239", "2261", "2263", "3222", "3224", "3241", "3242", "3251", "5151", "5152", "2212"}
COD_EXCLUIR = {"515225", "519305", "223310"}   # overrides não-principais
COD_INCLUIR = {"322225", "515140", "515210", "223305"}

def categoria(cbo):
    fam = cbo[:4]
    mapa = {"2231": "Medicina", "2251": "Medicina", "2252": "Medicina", "2253": "Medicina",
            "2235": "Enfermagem – enfermeiros", "3222": "Enfermagem – técnicos e auxiliares",
            "2232": "Odontologia e saúde bucal", "3224": "Odontologia e saúde bucal",
            "2234": "Farmácia", "3251": "Farmácia – técnicos e auxiliares",
            "2236": "Fisioterapia", "2237": "Nutrição", "2238": "Fonoaudiologia",
            "3241": "Diagnóstico e laboratório – técnicos e auxiliares",
            "3242": "Diagnóstico e laboratório – técnicos e auxiliares",
            "5152": "Diagnóstico e laboratório – técnicos e auxiliares",
            "5151": "Agentes comunitários de saúde e afins", "2212": "Biomedicina"}
    if cbo == "322225": return "Instrumentação cirúrgica"
    if cbo == "515210": return "Farmácia – técnicos e auxiliares"
    if cbo == "515140": return "Agentes de combate às endemias"
    if cbo == "223305": return "Medicina veterinária"
    return mapa.get(fam)

def eh_principal(cbo):
    if not cbo: return False
    if cbo in COD_EXCLUIR: return False
    if cbo in COD_INCLUIR: return True
    return cbo[:4] in FAM_PRINCIPAL

def ordem_arquivo(nome):
    n = os.path.splitext(os.path.basename(nome))[0].lower()
    m = re.search(r"(20\d{4})", n)
    if m: return m.group(1)
    mapa = {"cat-jul-ago-set-2018": "201807", "cat-comp-outnovdez-2018": "201810",
            "cat2018-comp01-02-03-2019": "201901", "cat-comp04-05-06-2019": "201904",
            "cat-comp07-08-09-2019": "201907", "cat-comp10-11-12-2019": "201910",
            "cat-comp01-02-03-2020": "202001", "cat-competencia-04-05-06-2020": "202004",
            "cat-competencia-07-08-09-2020": "202007", "cat-comp10-11-12-2020": "202010"}
    return mapa.get(n, "999999")


def main():
    tot_linhas = 0
    frames = []
    for path in sorted(glob.glob(os.path.join("dados", "brutos", "banco de dados/cat-inss", "*.csv"))):
        df = pd.read_csv(path, sep=";", dtype=str, header=0, encoding=enc_de(path),
                         quoting=3, keep_default_na=False, engine="c")
        tot_linhas += len(df)
        ncol = df.shape[1]
        cols = list(df.columns)
        if ncol == 25:
            i_mun, i_uf, i_cbo_c, i_cbo_d, i_dat = 12, 19, 2, 3, 22
        elif ncol == 27:
            i_mun, i_uf, i_cbo_c, i_cbo_d, i_dat = 12, 19, 2, 3, 22
        elif ncol == 24 and cols[3].strip().upper().startswith("CID"):
            i_mun, i_uf, i_cbo_c, i_cbo_d, i_dat = 10, 17, 2, 2, 20
        elif ncol == 24:
            i_mun, i_uf, i_cbo_c, i_cbo_d, i_dat = 12, 19, 2, 3, 21
        else:
            sys.exit(f"esquema inesperado: {path}")
        mun = df.iloc[:, i_mun].str.strip()
        sel = mun.str.slice(0, 6).eq("330100")
        if not sel.any(): continue
        sub = df.loc[sel]
        linha_bruta = sub.apply(lambda r: ";".join(str(x).strip() for x in r), axis=1)
        esq = {25: "S25", 27: "S27"}.get(ncol) or ("S24A" if cols[3].strip().upper().startswith("CID") else "S24B")
        frames.append(pd.DataFrame({
            "arquivo": os.path.basename(path), "ordem": ordem_arquivo(path), "esquema": esq,
            "uf": sub.iloc[:, i_uf].str.strip(),
            "cbo": sub.iloc[:, i_cbo_c].str.strip().str.extract(r"^(\d{6})", expand=False).fillna(""),
            "data": sub.iloc[:, i_dat].str.strip(),
            "hash": [hashlib.sha256((esq + "|" + lb).encode("utf-8")).hexdigest() for lb in linha_bruta]}))

    v = pd.concat(frames, ignore_index=True)
    v = v[v["uf"].map(norm) == "rio de janeiro"]
    V2 = len(v)
    # dedup entre arquivos: mantém todas as linhas do arquivo de menor 'ordem' por hash
    primeira = v.groupby("hash")["ordem"].transform("min")
    v3 = v[v["ordem"] == primeira]
    V3 = len(v3)
    v3 = v3.assign(data_dt=pd.to_datetime(v3["data"], format="%d/%m/%Y", errors="coerce"))
    v3 = v3[(v3["data_dt"] >= "2018-01-01") & (v3["data_dt"] <= "2025-12-31")]
    V3p = len(v3)
    v3 = v3.assign(principal=v3["cbo"].map(eh_principal), ano=v3["data_dt"].dt.year)
    V4 = int(v3["principal"].sum())
    V5 = v3[v3["principal"]].assign(cat=lambda d: d["cbo"].map(categoria)).groupby("cat").size().to_dict()
    V6 = v3[v3["principal"]].groupby("ano").size().to_dict()

    # ---- comparação com o pipeline ------------------------------------------------
    base = pd.read_csv("dados/processados/base_cat_campos_profissoes_saude_processada.csv", sep=";", dtype=str, encoding="utf-8-sig")
    P4 = int((base["universo"] == "principal").sum())
    p5 = base[base["universo"] == "principal"].groupby("categoria_profissional").size().to_dict()
    p6 = base[base["universo"] == "principal"].groupby(base["ano_acidente"].astype(int)).size().to_dict()
    fluxo = json.load(open("logs/fluxo_03_processamento.json", encoding="utf-8"))["fluxo"]

    res = {
        "V1_total_linhas_lidas": {"validacao": tot_linhas, "pipeline": 3902905},
        "V2_campos_uf_rj_antes_dedup": {"validacao": V2,
                                        "nota": "registros 330100+UF RJ antes da deduplicação; V2 - V3 = duplicidades removidas neste recorte"},
        "V3_apos_dedup": {"validacao": V3, "pipeline": fluxo["campos_330100_uf_rj"]},
        "V3p_periodo": {"validacao": V3p, "pipeline": fluxo["campos_periodo_2018_2025"]},
        "V4_saude_principal": {"validacao": V4, "pipeline": P4},
        "V5_categorias": {"validacao": V5, "pipeline": p5},
        "V6_por_ano": {"validacao": {int(k): int(x) for k, x in V6.items()}, "pipeline": {int(k): int(x) for k, x in p6.items()}},
    }
    ok = (V4 == P4 and {k: int(x) for k, x in V5.items()} == {k: int(x) for k, x in p5.items()}
          and {int(k): int(x) for k, x in V6.items()} == {int(k): int(x) for k, x in p6.items()}
          and V3p == fluxo["campos_periodo_2018_2025"] and tot_linhas == 3902905)
    res["RESULTADO"] = "CONVERGENTE — publicação liberada" if ok else "DIVERGENTE — publicação bloqueada"
    with open("logs/validacao_independente.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
