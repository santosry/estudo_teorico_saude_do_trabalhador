# -*- coding: utf-8 -*-
"""
14_redes_associacao.py — Análise de redes de associação entre ocupação, CNAE, CID-10,
agente causador, tipo de acidente e natureza da lesão nas CATs de profissões da saúde
de Campos dos Goytacazes (RJ), 2018-2025.

Técnicas:
1. Matrizes de co-ocorrência (occupation × CID, occupation × agent, CID × agent)
2. Regras de associação (Apriori) — suporte, confiança e lift
3. Grafo bipartido e projeções (networkx) com centralidade
4. Análise de correspondência múltipla (MCA)
"""
import os, json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter
import warnings
warnings.filterwarnings("ignore")

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

# ========== CARREGAR DADOS ==========
df = pd.read_csv("dados/processados/base_cat_campos_classificada.csv", sep=";", dtype=str, encoding="utf-8-sig")
saude = df[df["universo"] == "principal"].copy()

# Simplificar e recodificar variáveis para análise de associação
def simplificar_cid(cod):
    """Agrupar CID-10 em categorias clinicamente significativas."""
    if pd.isna(cod) or cod == "":
        return "Sem registro"
    cod = str(cod).strip()
    if cod.startswith("S61"):
        return "Ferimento punho/mão (S61)"
    if cod.startswith("S6"):
        return "Traumatismo punho/mão (S60-S69)"
    if cod.startswith("Z20"):
        return "Exposição doenças transmissíveis (Z20)"
    if cod.startswith("Z2"):
        return "Exposição doenças (Z20-Z29)"
    if cod.startswith("S80") or cod.startswith("S8"):
        return "Traumatismo joelho/perna (S80-S89)"
    if cod.startswith("S93") or cod.startswith("S934"):
        return "Entorse tornozelo (S93)"
    if cod.startswith("S40") or cod.startswith("S4"):
        return "Traumatismo ombro/braço (S40-S49)"
    if cod.startswith("S"):
        return "Outros traumatismos (S00-T98)"
    if cod.startswith("Y"):
        return "Causas externas (Y)"
    if cod.startswith("M"):
        return "Doenças osteomusculares (M)"
    if cod.startswith("F"):
        return "Transtornos mentais (F)"
    if cod.startswith("B") or cod.startswith("A"):
        return "Doenças infecciosas (A-B)"
    return f"Outros ({cod[:3]})"

def simplificar_agente(ag):
    """Agrupar agentes causadores em categorias."""
    if pd.isna(ag) or ag == "":
        return "Não informado"
    ag = str(ag).strip().lower()
    if "infeccioso" in ag or "biologico" in ag or "biológico" in ag or "soro" in ag or "toxina" in ag or "virus" in ag or "vírus" in ag or "bacteria" in ag:
        return "Agente biológico/infeccioso"
    if "ferramenta manual" in ag:
        return "Ferramenta manual"
    if "perfurocortante" in ag or "agulha" in ag or "lanceta" in ag or "bisturi" in ag or "seringa" in ag:
        return "Perfurocortante"
    if "veiculo" in ag or "veículo" in ag or "motocicleta" in ag or "automovel" in ag:
        return "Veículo/transporte"
    if "mobiliario" in ag or "mobiliário" in ag or "cama" in ag or "mesa" in ag or "cadeira" in ag:
        return "Mobiliário/acessórios"
    if "chao" in ag or "chão" in ag or "superficie" in ag or "superfície" in ag or "piso" in ag or "escada" in ag:
        return "Superfície/piso/escada"
    if "quimico" in ag or "químico" in ag or "substancia" in ag:
        return "Agente químico"
    if "paciente" in ag or "pessoa" in ag:
        return "Paciente/pessoa"
    if "maquina" in ag or "máquina" in ag or "equipamento" in ag:
        return "Máquina/equipamento"
    if "animal" in ag:
        return "Animal"
    return "Outros agentes"

def simplificar_categoria(cat):
    """Agrupar categorias profissionais em 5 grandes grupos."""
    if "enfermagem" in cat.lower() and "técnico" in cat.lower() or "auxiliar" in cat.lower():
        return "Enfermagem (nível técnico)"
    if "enfermagem" in cat.lower() and "enfermeiro" in cat.lower():
        return "Enfermagem (nível superior)"
    if "medicina" in cat.lower():
        return "Medicina"
    if "fisioterapia" in cat.lower():
        return "Fisioterapia"
    if "diagnóstico" in cat.lower() or "laboratório" in cat.lower():
        return "Diagnóstico/laboratório"
    return "Demais profissões"

saude["cid_grupo"] = saude["cid10_codigo"].apply(simplificar_cid)
saude["agente_grupo"] = saude["agente_causador"].apply(simplificar_agente)
saude["cat_grupo"] = saude["categoria_profissional"].apply(simplificar_categoria)
saude["cnae_grupo"] = saude["cnae_classe"].apply(
    lambda x: "Hospitalar (8610)" if str(x).startswith("8610")
    else ("Atenção ambulatorial (8630)" if str(x).startswith("8630")
          else ("Diagnóstico/terapia (8640)" if str(x).startswith("8640")
                else ("Outros serviços saúde (86-87)"))))

os.makedirs("saidas/tabelas", exist_ok=True)
os.makedirs("saidas/figuras", exist_ok=True)

print("n =", len(saude))
print("CID grupos:", saude["cid_grupo"].nunique())
print("Agente grupos:", saude["agente_grupo"].nunique())
print("CAT grupos:", saude["cat_grupo"].nunique())

# ========== 1. MATRIZES DE CO-OCORRÊNCIA ==========
print("\n=== 1. Matrizes de co-ocorrência ===")

# Ocupação × CID (top categorias)
cross_cat_cid = pd.crosstab(saude["cat_grupo"], saude["cid_grupo"])
# Normalizar por linha (perfil de CID por categoria)
cross_cat_cid_pct = cross_cat_cid.div(cross_cat_cid.sum(axis=1), axis=0) * 100

# Ocupação × Agente
cross_cat_agente = pd.crosstab(saude["cat_grupo"], saude["agente_grupo"])
cross_cat_agente_pct = cross_cat_agente.div(cross_cat_agente.sum(axis=1), axis=0) * 100

# CID × Agente (para os mais frequentes)
top_cids = saude["cid_grupo"].value_counts().head(8).index
top_agentes = saude["agente_grupo"].value_counts().head(8).index
cross_cid_agente = pd.crosstab(
    saude[saude["cid_grupo"].isin(top_cids)]["cid_grupo"],
    saude[saude["agente_grupo"].isin(top_agentes)]["agente_grupo"]
)

# Salvar matrizes
cross_cat_cid_pct.round(1).to_csv("saidas/tabelas/T29_matriz_ocupacao_cid_pct.csv", sep=";", encoding="utf-8-sig", lineterminator="\n")
cross_cat_agente_pct.round(1).to_csv("saidas/tabelas/T30_matriz_ocupacao_agente_pct.csv", sep=";", encoding="utf-8-sig", lineterminator="\n")
cross_cid_agente.to_csv("saidas/tabelas/T31_matriz_cid_agente.csv", sep=";", encoding="utf-8-sig", lineterminator="\n")

# ========== 2. REGRAS DE ASSOCIAÇÃO (APRIORI) ==========
print("\n=== 2. Regras de associação ===")
try:
    from mlxtend.frequent_patterns import apriori, association_rules

    # Criar matriz binária (one-hot)
    # Usar as 4 dimensões: categoria, CID grupo, agente grupo, tipo acidente
    variaveis = []
    for _, row in saude.iterrows():
        items = [
            f"OCUP={row['cat_grupo']}",
            f"CID={row['cid_grupo']}",
            f"AGENTE={row['agente_grupo']}",
            f"TIPO={row['tipo_acidente']}",
            f"NATUREZA={row['natureza_lesao'][:40] if pd.notna(row['natureza_lesao']) else 'NI'}",
        ]
        variaveis.append(items)

    # Criar DataFrame binário (transaction format)
    from mlxtend.preprocessing import TransactionEncoder
    te = TransactionEncoder()
    te_ary = te.fit(variaveis).transform(variaveis)
    df_bin = pd.DataFrame(te_ary, columns=te.columns_)

    # Apriori: min_support=0.03 (~35 registros), max_len=4
    frequent_itemsets = apriori(df_bin, min_support=0.03, use_colnames=True, max_len=4)
    print(f"  Itemsets frequentes: {len(frequent_itemsets)} (suporte >= 3%)")

    # Regras com lift > 1.5 e confiança > 0.3
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.2, num_itemsets=len(frequent_itemsets))
    rules = rules[rules["confidence"] >= 0.30].sort_values("lift", ascending=False)
    print(f"  Regras (lift>=1.2, conf>=0.30): {len(rules)}")

    # Selecionar top 30 regras mais fortes
    top_rules = rules.head(30).copy()
    top_rules["antecedents_str"] = top_rules["antecedents"].apply(lambda x: ", ".join(sorted(x)))
    top_rules["consequents_str"] = top_rules["consequents"].apply(lambda x: ", ".join(sorted(x)))
    cols_out = ["antecedents_str", "consequents_str", "support", "confidence", "lift",
                "leverage", "conviction"]
    top_rules[cols_out].round(4).to_csv(
        "saidas/tabelas/T32_regras_associacao_top30.csv", sep=";", index=False,
        encoding="utf-8-sig", lineterminator="\n")
    print(f"  Top regras exportadas (T32)")

    # Estatísticas de redes
    print(f"\n  Regras de maior lift:")
    for _, r in rules.head(8).iterrows():
        ant = ", ".join(sorted(r["antecedents"]))
        con = ", ".join(sorted(r["consequents"]))
        print(f"    {ant} -> {con}  (lift={r['lift']:.2f}, conf={r['confidence']:.2f}, sup={r['support']:.3f})")

except ImportError:
    print("  mlxtend não disponível. Pulando Apriori.")
    rules = None
    frequent_itemsets = None

# ========== 3. GRAFO DE ASSOCIAÇÕES (se networkx disponível) ==========
print("\n=== 3. Grafo bipartido ===")
try:
    import networkx as nx

    # Construir grafo bipartido: ocupação — CID (arestas ponderadas por frequência)
    G = nx.Graph()
    # Adicionar nós de ocupação
    ocupacoes = saude["cat_grupo"].unique()
    for o in ocupacoes:
        G.add_node(o, tipo="ocupacao", size=int((saude["cat_grupo"] == o).sum()))

    # Adicionar nós de CID
    cids = saude["cid_grupo"].value_counts().head(12).index
    for c in cids:
        G.add_node(c, tipo="cid", size=int((saude["cid_grupo"] == c).sum()))

    # Arestas
    for o in ocupacoes:
        sub = saude[saude["cat_grupo"] == o]
        for c in cids:
            peso = int((sub["cid_grupo"] == c).sum())
            if peso >= 3:  # pelo menos 3 co-ocorrências
                G.add_edge(o, c, weight=peso)

    # Grau de centralidade
    centrality = nx.degree_centrality(G)
    print(f"  Nós: {G.number_of_nodes()}, Arestas: {G.number_of_edges()}")

    # Projeção no espaço das ocupações
    ocup_nodes = [n for n, d in G.nodes(data=True) if d.get("tipo") == "ocupacao"]
    G_ocup = nx.bipartite.weighted_projected_graph(G, ocup_nodes)

    # Projeção no espaço dos CIDs
    cid_nodes = [n for n, d in G.nodes(data=True) if d.get("tipo") == "cid"]
    G_cid = nx.bipartite.weighted_projected_graph(G, cid_nodes)

    # Salvar arestas das projeções
    edges_ocup = [(u, v, d["weight"]) for u, v, d in G_ocup.edges(data=True)]
    pd.DataFrame(edges_ocup, columns=["ocupacao1", "ocupacao2", "peso_coocorrencia"]).sort_values(
        "peso_coocorrencia", ascending=False).to_csv(
        "saidas/tabelas/T33_grafo_ocupacoes.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

    edges_cid = [(u, v, d["weight"]) for u, v, d in G_cid.edges(data=True)]
    pd.DataFrame(edges_cid, columns=["cid1", "cid2", "peso_coocorrencia"]).sort_values(
        "peso_coocorrencia", ascending=False).to_csv(
        "saidas/tabelas/T34_grafo_cids.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

    print(f"  Projeção ocupações: {G_ocup.number_of_nodes()} nós, {G_ocup.number_of_edges()} arestas")
    print(f"  Projeção CIDs: {G_cid.number_of_nodes()} nós, {G_cid.number_of_edges()} arestas")

    # ========== FIGURA: Grafo bipartido simplificado ==========
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=600)
    # Layout bipartido
    pos = {}
    ocup_list = sorted(ocup_nodes)
    cid_list = sorted(cid_nodes)
    for i, o in enumerate(ocup_list):
        pos[o] = (0, i - len(ocup_list) / 2)
    for i, c in enumerate(cid_list):
        pos[c] = (2, i - len(cid_list) / 2)

    # Tamanhos dos nós
    node_sizes_ocup = [G.nodes[n]["size"] * 0.8 for n in ocup_list]
    node_sizes_cid = [G.nodes[n]["size"] * 0.8 for n in cid_list]

    # Desenhar
    nx.draw_networkx_nodes(G, pos, nodelist=ocup_list, node_color="#2166AC", node_size=node_sizes_ocup,
                           alpha=0.85, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=cid_list, node_color="#B2182B", node_size=node_sizes_cid,
                           alpha=0.85, ax=ax)

    # Arestas com espessura proporcional ao peso
    edge_widths = [0.3 + 0.3 * G[u][v]["weight"] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, alpha=0.35, width=edge_widths, edge_color="#757575", ax=ax)

    # Rótulos
    labels_ocup = {n: n.replace("Enfermagem", "Enf.").replace("(nível técnico)", "(técn.)")
                   .replace("(nível superior)", "(sup.)").replace("Diagnóstico/laboratório", "Diag./lab.")
                   .replace("Demais profissões", "Demais")[:25] for n in ocup_list}
    labels_cid = {n: n[:28] for n in cid_list}
    nx.draw_networkx_labels(G, pos, labels_ocup, font_size=5.5, font_color="#2166AC", ax=ax)
    nx.draw_networkx_labels(G, pos, labels_cid, font_size=5.5, font_color="#B2182B", ax=ax)

    ax.set_xlim(-0.8, 2.8)
    ax.axis("off")
    ax.set_title("Ocupações ↔ Diagnósticos (CID-10)", fontsize=7.5, pad=6)
    # Legenda
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2166AC", markersize=7, label="Ocupações"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#B2182B", markersize=7, label="CID-10"),
    ]
    ax.legend(handles=legend_elements, fontsize=6, loc="lower right")
    fig.tight_layout(pad=0.4)
    fig.savefig("saidas/figuras/F6_grafo_ocupacao_cid.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  Figura F6 gerada.")

except ImportError:
    print("  networkx não disponível. Pulando grafo.")
    G, G_ocup, G_cid = None, None, None

# ========== 4. MAPA DE CALOR: Ocupação × CID (perfil percentual) ==========
print("\n=== 4. Mapa de calor ocupação × CID ===")
# Selecionar apenas categorias com n >= 10
cats_validas = saude["cat_grupo"].value_counts()
cats_validas = cats_validas[cats_validas >= 10].index.tolist()
cids_validos = saude["cid_grupo"].value_counts().head(10).index.tolist()

heatmap_data = pd.crosstab(
    saude[saude["cat_grupo"].isin(cats_validas)]["cat_grupo"],
    saude[saude["cid_grupo"].isin(cids_validos)]["cid_grupo"]
)
heatmap_pct = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=600)
im = ax.imshow(heatmap_pct.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=heatmap_pct.values.max())
ax.set_xticks(range(len(heatmap_pct.columns)))
ax.set_xticklabels([c[:22] for c in heatmap_pct.columns], rotation=45, ha="right", fontsize=5.8)
ax.set_yticks(range(len(heatmap_pct.index)))
ax.set_yticklabels([c[:30] for c in heatmap_pct.index], fontsize=5.8)
# Anotar valores
for i in range(len(heatmap_pct.index)):
    for j in range(len(heatmap_pct.columns)):
        val = heatmap_pct.values[i, j]
        if val > 0:
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=5.2,
                    color="white" if val > heatmap_pct.values.max() * 0.5 else "black")
cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("%", fontsize=6.5)
ax.set_title("Perfil de diagnósticos (CID-10) por categoria profissional", fontsize=7, pad=6)
fig.tight_layout(pad=0.4)
fig.savefig("saidas/figuras/F7_heatmap_ocupacao_cid.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ========== 5. ESTATÍSTICAS DE ASSOCIAÇÃO (Chi^2, V de Cramér) ==========
print("\n=== 5. Testes de associação ===")
from scipy.stats import chi2_contingency

associacoes = []
for nome, tab in [("Ocupação × CID", cross_cat_cid.loc[cross_cat_cid.sum(axis=1) >= 5]),
                   ("Ocupação × Agente", cross_cat_agente.loc[cross_cat_agente.sum(axis=1) >= 5]),
                   ("Ocupação × Tipo de acidente", pd.crosstab(saude["cat_grupo"], saude["tipo_acidente"]))]:
    try:
        chi2, p, dof, expected = chi2_contingency(tab)
        n = tab.sum().sum()
        min_dim = min(tab.shape) - 1
        cramer_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        associacoes.append({
            "comparacao": nome,
            "chi2": round(chi2, 2),
            "gl": dof,
            "p_valor": round(p, 6),
            "v_cramer": round(cramer_v, 4),
            "significativo": "Sim" if p < 0.05 else "Não",
            "n": int(n),
        })
        print(f"  {nome}: chi^2={chi2:.1f}, gl={dof}, p={p:.6f}, V de Cramér={cramer_v:.4f}")
    except Exception as e:
        print(f"  {nome}: erro — {e}")

pd.DataFrame(associacoes).to_csv(
    "saidas/tabelas/T35_testes_associacao.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# ========== 6. PERFIL DIFERENCIAL: Enfermagem técnica vs demais ==========
print("\n=== 6. Perfil diferencial da enfermagem técnica ===")
enf_tec = saude[saude["cat_grupo"] == "Enfermagem (nível técnico)"]
outros_saude = saude[saude["cat_grupo"] != "Enfermagem (nível técnico)"]

# Razão de prevalência dos CIDs
cid_enf = enf_tec["cid_grupo"].value_counts(normalize=True) * 100
cid_outros = outros_saude["cid_grupo"].value_counts(normalize=True) * 100
rp_cid = (cid_enf / cid_outros.replace(0, np.nan)).dropna().sort_values(ascending=False)
print("  Razão de prevalência CID (enf. técnica / demais):")
for cid, rp in rp_cid.head(8).items():
    print(f"    {cid[:55]}: RP={rp:.2f} (enf={cid_enf.get(cid, 0):.1f}%, outros={cid_outros.get(cid, 0):.1f}%)")

# Salvar razões de prevalência
rp_df = pd.DataFrame({
    "cid_grupo": rp_cid.index,
    "rp_enf_tec_vs_demais": rp_cid.values.round(2),
    "pct_enf_tec": [cid_enf.get(c, 0) for c in rp_cid.index],
    "pct_demais": [cid_outros.get(c, 0) for c in rp_cid.index],
}).head(20)
rp_df.to_csv("saidas/tabelas/T36_razao_prevalencia_cid_enfermagem.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# ========== 7. REDE DE ACIDENTES: Ocupação → Agente → CID → Natureza ==========
print("\n=== 7. Cadeias de acidentes mais frequentes ===")
cadeias = saude.groupby(["cat_grupo", "agente_grupo", "cid_grupo", "tipo_acidente"]).size().rename("n").reset_index()
cadeias = cadeias.sort_values("n", ascending=False).head(25)
cadeias.to_csv("saidas/tabelas/T37_cadeias_acidente_top25.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
print("  Top 5 cadeias ocupação→agente→CID→tipo:")
for _, row in cadeias.head(8).iterrows():
    print(f"    {row['cat_grupo'][:30]} → {row['agente_grupo'][:30]} → {row['cid_grupo'][:30]} → {row['tipo_acidente']}: n={int(row['n'])}")

# ========== FIGURA: Sankey simplificado (barras empilhadas de associação) ==========
# Mostrar fluxo ocupação → agente → CID como barras empilhadas
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.8), dpi=600, gridspec_kw={"width_ratios": [1, 1.2]})

# Painel esquerdo: ocupação × agente
top_agentes_plot = saude["agente_grupo"].value_counts().head(5).index
cross_plot1 = pd.crosstab(saude["cat_grupo"], saude["agente_grupo"])
cross_plot1 = cross_plot1[top_agentes_plot]
cross_plot1_pct = cross_plot1.div(cross_plot1.sum(axis=1), axis=0) * 100

cores_agente = ["#2166AC", "#92C5DE", "#F4A582", "#B2182B", "#BDBDBD"]
cross_plot1_pct.plot(kind="barh", stacked=True, ax=ax1, color=cores_agente, width=0.7, edgecolor="white", linewidth=0.3)
ax1.set_xlabel("% dos acidentes na categoria")
ax1.set_title("Ocupação → Agente causador", fontsize=7, pad=4)
ax1.legend(fontsize=5, loc="lower right", ncol=1, title="Agente", title_fontsize=5.5)
ax1.spines[["top", "right"]].set_visible(False)
ax1.tick_params(labelsize=5.8)

# Painel direito: agente × CID
top_cids_plot = saude["cid_grupo"].value_counts().head(5).index
cross_plot2 = pd.crosstab(saude["agente_grupo"], saude["cid_grupo"])
cross_plot2 = cross_plot2.reindex(top_agentes_plot)[top_cids_plot].fillna(0).astype(int)
cross_plot2_pct = cross_plot2.div(cross_plot2.sum(axis=1), axis=0) * 100

cores_cid = ["#1B7837", "#5AAE61", "#A6DBA0", "#762A83", "#C2A5CF"]
cross_plot2_pct.plot(kind="barh", stacked=True, ax=ax2, color=cores_cid, width=0.7, edgecolor="white", linewidth=0.3)
ax2.set_xlabel("% dos acidentes com o agente")
ax2.set_title("Agente causador → Diagnóstico (CID-10)", fontsize=7, pad=4)
ax2.legend(fontsize=5, loc="lower right", ncol=1, title="CID-10", title_fontsize=5.5)
ax2.spines[["top", "right"]].set_visible(False)
ax2.tick_params(labelsize=5.8)

fig.tight_layout(pad=1.5)
fig.savefig("saidas/figuras/F8_fluxo_ocupacao_agente_cid.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ========== LOG ==========
log = {
    "execucao": pd.Timestamp.now().isoformat(),
    "n_registros": int(len(saude)),
    "n_cid_grupos": int(saude["cid_grupo"].nunique()),
    "n_agente_grupos": int(saude["agente_grupo"].nunique()),
    "n_cat_grupos": int(saude["cat_grupo"].nunique()),
    "regras_associacao": len(rules) if rules is not None else 0,
    "grafo": {"nos": G.number_of_nodes(), "arestas": G.number_of_edges()} if G is not None else None,
}
json.dump(log, open("logs/log_14_redes_associacao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\nOK Análise de redes de associação concluída.")
print("  Tabelas: T29 a T37")
print("  Figuras: F6, F7, F8")
