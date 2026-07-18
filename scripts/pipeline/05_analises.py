# -*- coding: utf-8 -*-
"""
05_analises.py — Análises descritivas, sensibilidade e qualidade.
Denominadores populacionais (RAIS/CNES) NÃO estão disponíveis na pasta do projeto;
portanto, apenas frequências e proporções DENTRO do conjunto de CAT são calculadas.
Supressão: células <5 são agregadas em categorias de resíduo nas tabelas de divulgação.
"""
import os, json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)
pd.set_option("display.width", 200)

df = pd.read_csv("dados/processados/base_cat_campos_classificada.csv", sep=";", dtype=str, encoding="utf-8-sig")
df["ano"] = df["ano_acidente"].astype(int)
df["idade_num"] = pd.to_numeric(df["idade"], errors="coerce")
df["tempo_emissao"] = pd.to_numeric(df["tempo_acidente_emissao_dias"], errors="coerce")
df["mes"] = df["mes_acidente"]

saude = df[df["universo"] == "principal"].copy()
multi = df[df["universo"] == "multiprofissional"].copy()
nclass = df[df["universo"] == "nao_classificado"].copy()
outros = df[df["universo"] == "apoio_ou_outra"].copy()

os.makedirs("saidas/tabelas", exist_ok=True); os.makedirs("saidas/figuras", exist_ok=True)
T = {}

# T01 — CAT por ano e universo
t01 = df.pivot_table(index="ano", columns="universo", values="id_linha", aggfunc="count", fill_value=0)
t01["total"] = t01.sum(axis=1)
t01.index = [f"{a}*" if a in (2018, 2022, 2024, 2025) else str(a) for a in t01.index]
T["T01_cat_por_ano_universo"] = t01.reset_index().rename(columns={"index": "ano"})

# T02 — série mensal (saúde principal)
t02 = saude.groupby("mes").size().rename("n").reset_index()
T["T02_serie_mensal_saude"] = t02

# T03 — categorias profissionais
def tab_categoria(base, nome_total):
    t = base.groupby("categoria_profissional").size().sort_values(ascending=False).rename("n").reset_index()
    t["pct"] = (100 * t["n"] / t["n"].sum()).round(1)
    return t
T["T03_categorias_saude"] = tab_categoria(saude, "saude")
T["T03b_categorias_multi"] = tab_categoria(multi, "multi")

# T04 — ranking CBO (saúde), supressão <5
t04 = saude.groupby(["cbo_codigo", "cbo_titulo_oficial", "categoria_profissional"]).size().rename("n").reset_index().sort_values("n", ascending=False)
t04_pub = t04[t04["n"] >= 5].copy()
resid = t04[t04["n"] < 5]["n"].sum()
T["T04_ranking_cbo_saude"] = t04
T["T04b_ranking_cbo_publicavel"] = pd.concat([t04_pub, pd.DataFrame([{
    "cbo_codigo": "(agregado)", "cbo_titulo_oficial": f"Ocupações com n<5 ({len(t04) - len(t04_pub)} códigos)",
    "categoria_profissional": "—", "n": resid}])], ignore_index=True)

# T05/T06/T07 — sexo, faixa etária, tipo por grande grupo
saude["grupo4"] = saude["categoria_profissional"].where(
    saude["categoria_profissional"].isin(
        ["Enfermagem – técnicos e auxiliares", "Enfermagem – enfermeiros",
         "Diagnóstico e laboratório – técnicos e auxiliares", "Medicina"]), "Demais profissões da saúde")
bins = [14, 24, 34, 44, 54, 64, 200]
labs = ["15–24", "25–34", "35–44", "45–54", "55–64", "65+"]
saude["faixa_etaria"] = pd.cut(saude["idade_num"], bins=bins, labels=labs)
for var, nomet in [("sexo", "T05_sexo"), ("faixa_etaria", "T06_faixa_etaria"), ("tipo_acidente", "T07_tipo_acidente")]:
    t = saude.pivot_table(index=var, columns="grupo4", values="id_linha", aggfunc="count", fill_value=0, observed=False)
    t["Total"] = t.sum(axis=1)
    T[nomet] = t.reset_index()

# T08–T12 — tops (saúde, total)
def top_tab(base, col, n=12):
    t = base[col].fillna("(não informado)").replace("", "(não informado)").value_counts().rename("n").reset_index()
    t.columns = [col, "n"]
    t["pct"] = (100 * t["n"] / len(base)).round(1)
    return t.head(n)
T["T08_agente_causador"] = top_tab(saude, "agente_causador")
T["T09_natureza_lesao"] = top_tab(saude, "natureza_lesao")
T["T10_parte_corpo"] = top_tab(saude, "parte_corpo_atingida")
T["T11_cid10_grupo"] = top_tab(saude.assign(cid10=saude["cid10_grupo3"].fillna("") + " " + saude["cid10_descricao"].fillna("").str.slice(0, 40)), "cid10")
T["T12_cnae"] = top_tab(saude.assign(cnae=saude["cnae_classe"].fillna("") + " " + saude["cnae_descricao"].fillna("").str.slice(0, 45)), "cnae")
T["T13_emitente"] = top_tab(saude, "emitente_cat", 6)
T["T13b_origem_cadastramento"] = top_tab(saude, "origem_cadastramento_cat", 6)
T["T13c_filiacao"] = top_tab(saude, "filiacao_segurado", 6)
T["T13d_obito"] = top_tab(saude, "indica_obito_acidente", 4)

# T14 — tempo acidente->emissão por ano (nota: competências 2023-06 a 2023-10 sem data de emissão na fonte)
t14 = saude.groupby("ano")["tempo_emissao"].agg(n_validos="count", mediana="median",
                                                p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)).round(1)
t14["n_total"] = saude.groupby("ano").size()
T["T14_tempo_emissao"] = t14.reset_index()

# T15 — completude por variável e ano (base saúde)
vars_c = ["cbo_codigo", "cid10_codigo", "cnae_classe", "sexo", "idade", "tipo_acidente", "agente_causador",
          "natureza_lesao", "parte_corpo_atingida", "emitente_cat", "data_emissao_cat", "origem_cadastramento_cat"]
comp = {}
for v in vars_c:
    comp[v] = saude.assign(ok=saude[v].notna() & (saude[v] != "")).groupby("ano")["ok"].mean().mul(100).round(1)
T["T15_completude_pct"] = pd.DataFrame(comp).reset_index()

# T16 — períodos pandêmicos (saúde): médias mensais e % agente infeccioso
per = pd.Series(np.select(
    [saude["mes"] < "2020-03", (saude["mes"] >= "2020-03") & (saude["mes"] <= "2021-12")],
    ["pré-pandemia (jan/18–fev/20)", "período crítico (mar/20–dez/21)"], "pós-crítico (jan/22–out/25)"), index=saude.index)
saude["periodo_pandemia"] = per
infec = saude["agente_causador"].fillna("").str.contains("Infeccioso", case=False)
t16 = saude.groupby("periodo_pandemia").agg(n=("id_linha", "count"))
# meses de cobertura: jan/18–fev/20 = 26; mar/20–dez/21 = 22; jan/22–out/25 = 46 (mapeado por nome)
t16["meses_no_periodo"] = t16.index.map({"pré-pandemia (jan/18–fev/20)": 26,
                                         "período crítico (mar/20–dez/21)": 22,
                                         "pós-crítico (jan/22–out/25)": 46})
t16["media_mensal"] = (t16["n"] / t16["meses_no_periodo"]).round(1)
t16["pct_agente_infeccioso"] = saude.groupby("periodo_pandemia").apply(
    lambda g: round(100 * g["agente_causador"].fillna("").str.contains("Infeccioso", case=False).mean(), 1))
T["T16_periodos_pandemia"] = t16.reset_index()
t16b = saude.assign(infec=infec).groupby("ano")["infec"].mean().mul(100).round(1).rename("pct_agente_infeccioso")
T["T16b_infeccioso_por_ano"] = t16b.reset_index()

# T17 — sensibilidade
fluxo3 = json.load(open("logs/fluxo_03_processamento.json", encoding="utf-8"))
sens = []
def add(nome, base, nota=""):
    sens.append({"cenario": nome, "n_saude_principal": len(base), "nota": nota})
add("Base completa 2018–2025 (referência)", saude)
add("Excluindo 2025 (parcial)", saude[saude["ano"] < 2025])
add("Somente meses jan–out (todos os anos)", saude[saude["mes"].str.slice(5).astype(int) <= 10])
add("Excluindo acidentes de trajeto", saude[saude["tipo_acidente"] != "Trajeto"])
add("Somente acidentes típicos", saude[saude["tipo_acidente"] == "Típico"])
add("Universo restrito: profissões da saúde em CNAE 86/87", saude[saude["cnae_saude"] == "sim"])
add("Multiprofissionais (todas)", multi)
add("Multiprofissionais restritas a CNAE 86/87", multi[multi["cnae_saude"] == "sim"])
sens.append({"cenario": "Antes da remoção de duplicidades entre arquivos (candidatos brutos c/ código 330100)",
             "n_saude_principal": "-", "nota": f"{fluxo3['fluxo']['duplicidades_entre_arquivos_removidas']} duplicidades removidas na base geral de candidatos"})
T["T17_sensibilidade"] = pd.DataFrame(sens)

# T18 — apoio: outras ocupações em CNAE saúde (86/87)
apoio_cnae = outros[outros["cnae_saude"] == "sim"]
t18 = apoio_cnae.groupby(["cbo_codigo", "cbo_titulo_oficial"]).size().rename("n").reset_index().sort_values("n", ascending=False)
T["T18_apoio_em_cnae_saude"] = t18.head(25)
T["T18b_resumo_apoio"] = pd.DataFrame([{
    "outras_ocupacoes_total": len(outros),
    "outras_ocupacoes_em_cnae_saude": len(apoio_cnae),
    "nao_classificados_total": len(nclass),
    "nao_classificados_em_cnae_saude": int((nclass["cnae_saude"] == "sim").sum()),
    "saude_principal_fora_cnae_saude": int((saude["cnae_saude"] != "sim").sum()),
    "saude_principal_pct_em_cnae_saude": round(100 * (saude["cnae_saude"] == "sim").mean(), 1)}])

# T19 — fluxo de seleção
f = fluxo3["fluxo"]
T["T19_fluxo_selecao"] = pd.DataFrame([
    ("Linhas lidas nos 58 arquivos CAT/INSS (2018–2025)", 3902905),
    ("Registros candidatos (código 330100 ou nome contendo 'campos')", f["candidatos_lidos"]),
    ("Duplicidades exatas entre arquivos sobrepostos removidas", f["duplicidades_entre_arquivos_removidas"]),
    ("Excluídos: outros municípios com 'Campo(s)' no nome", f["excluidos_outros_municipios_com_campo_no_nome"]),
    ("Excluídos: código 330100 com UF do empregador ≠ RJ", f["excluidos_330100_uf_nao_rj"]),
    ("Base Campos dos Goytacazes (330100 + UF RJ), acidentes 2018–2025", f["campos_periodo_2018_2025"]),
    ("→ Profissões da saúde (universo principal)", len(saude)),
    ("→ Profissões multiprofissionais intersetoriais", len(multi)),
    ("→ CBO não classificado (mantidos, analisados à parte)", len(nclass)),
    ("→ Demais ocupações (fora do campo da saúde)", len(outros)),
], columns=["etapa", "n"])

# T20 — idade por categoria
t20 = saude.groupby("grupo4")["idade_num"].agg(n="count", media="mean", mediana="median").round(1)
T["T20_idade_por_grupo"] = t20.reset_index()

# ---- exportação ----
with pd.ExcelWriter("saidas/tabelas/tabelas_completas_cat_saude_campos.xlsx") as xw:
    for nome, tab in T.items():
        tab.to_excel(xw, sheet_name=nome[:31], index=False)
for nome, tab in T.items():
    tab.to_csv(f"saidas/tabelas/{nome}.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# base final processada (recorte saúde + multi + não classificado)
final = pd.concat([saude, multi, nclass]).drop(columns=["grupo4", "periodo_pandemia", "faixa_etaria"], errors="ignore")
final.to_csv("dados/processados/base_cat_campos_profissoes_saude_processada.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
try:
    final.to_parquet("dados/processados/base_cat_campos_profissoes_saude_processada.parquet", index=False)
except Exception as e:
    print("parquet indisponível:", e)

# ---- figuras (estilo Cell Press: Arial, eixos finos, ticks externos, sem moldura,
#      sem linhas de grade, paleta contida, rotulagem direta, 600 dpi) ----
plt.rcParams.update({
    "font.family": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 7.0,
    "axes.linewidth": 0.6, "axes.edgecolor": "black", "axes.labelsize": 7.5,
    "xtick.direction": "out", "ytick.direction": "out",
    "xtick.major.size": 2.6, "ytick.major.size": 2.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "legend.frameon": False, "svg.fonttype": "none",
})
CORES = ["#2166AC", "#92C5DE", "#F4A582", "#B2182B", "#BDBDBD"]  # paleta divergente contida

# F1: barras empilhadas por ano e grande categoria (rótulos sem travessão)
ordem = ["Enfermagem – técnicos e auxiliares", "Enfermagem – enfermeiros",
         "Diagnóstico e laboratório – técnicos e auxiliares", "Medicina", "Demais profissões da saúde"]
rotulos = ["Téc. e aux. de enfermagem", "Enfermeiros", "Diagnóstico e laboratório",
           "Medicina", "Demais profissões"]
p = saude.pivot_table(index="ano", columns="grupo4", values="id_linha", aggfunc="count", fill_value=0)[ordem]
anos_lbl = [str(a) + ("*" if a in (2018, 2022, 2024, 2025) else "") for a in p.index]
fig, ax = plt.subplots(figsize=(6.6, 2.55), dpi=600)
bot = np.zeros(len(p))
for c, cor, rot in zip(ordem, CORES, rotulos):
    ax.bar(anos_lbl, p[c], bottom=bot, label=rot, color=cor, width=0.62,
           edgecolor="white", linewidth=0.4)
    bot += p[c].values
for xi, tot in enumerate(p.sum(axis=1).values):          # rotulagem direta dos totais
    ax.annotate(f"{tot}", (xi, tot), xytext=(0, 2.5), textcoords="offset points",
                ha="center", va="bottom", fontsize=6.4, color="#4D4D4D")
ax.set_ylabel("CATs (n)")
ax.set_ylim(0, float(p.sum(axis=1).max()) * 1.16)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="x", length=0)
ax.legend(ncol=3, fontsize=6.2, loc="upper left", bbox_to_anchor=(0, 1.02),
          handlelength=1.0, handleheight=1.0, columnspacing=0.9, labelspacing=0.35,
          borderaxespad=0)
fig.tight_layout(pad=0.4)
fig.savefig("saidas/figuras/F1_cat_ano_categorias.png", bbox_inches="tight", facecolor="white")
fig.savefig("saidas/figuras/F1_cat_ano_categorias.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)

# F2: série mensal com faixa do período crítico e médias por período (rotulagem direta)
s = saude.groupby("mes").size()
idx = pd.period_range("2018-01", "2025-12", freq="M").astype(str)
s = s.reindex(idx, fill_value=0)
lidx = list(idx)
i0, i1 = lidx.index("2020-03"), lidx.index("2021-12")
fig, ax = plt.subplots(figsize=(6.6, 2.15), dpi=600)
ymax = float(s.max()) * 1.14
ax.axvspan(i0 - 0.5, i1 + 0.5, color="#F5E1D3", alpha=0.55, lw=0, zorder=0)
ax.annotate("período crítico da covid-19", ((i0 + i1) / 2, ymax * 0.95),
            ha="center", fontsize=6.2, color="#8C5A3A")
x = np.arange(len(s))
ax.plot(x, s.values, lw=1.1, color="#2166AC", solid_capstyle="round", zorder=3)
# médias por período (segmentos tracejados com rótulo direto)
periodos = [(0, i0 - 1, 10.7), (i0, i1, 14.5), (i1 + 1, lidx.index("2025-10"), 11.9)]
for a, b, m in periodos:
    ax.hlines(m, a, b, colors="#B2182B", linestyles=(0, (4, 2)), lw=0.9, zorder=4)
    ax.annotate(f"média {str(m).replace('.', ',')}", ((a + b) / 2, m), xytext=(0, 3),
                textcoords="offset points", ha="center", fontsize=6.0, color="#B2182B")
ax.set_xticks([lidx.index(f"{a}-01") for a in range(2018, 2026)])
ax.set_xticklabels([str(a) for a in range(2018, 2026)])
ax.set_xlim(-1, len(s))
ax.set_ylim(0, ymax)
ax.set_ylabel("CATs por mês (n)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(pad=0.4)
fig.savefig("saidas/figuras/F2_serie_mensal_saude.png", bbox_inches="tight", facecolor="white")
fig.savefig("saidas/figuras/F2_serie_mensal_saude.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)

print("tabelas:", len(T), "| saúde:", len(saude), "| multi:", len(multi), "| nclass:", len(nclass))
print(T["T03_categorias_saude"].to_string(index=False))
print(T["T16_periodos_pandemia"].to_string(index=False))
print(T["T16b_infeccioso_por_ano"].to_string(index=False))
print(T["T05_sexo"].to_string(index=False))
print(T["T08_agente_causador"].head(8).to_string(index=False))
print(T["T09_natureza_lesao"].head(6).to_string(index=False))
print(T["T10_parte_corpo"].head(6).to_string(index=False))
print(T["T07_tipo_acidente"].to_string(index=False))
print(T["T12_cnae"].head(8).to_string(index=False))
print(T["T18b_resumo_apoio"].to_string(index=False))
print(t14.to_string())
