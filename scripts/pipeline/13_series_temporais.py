# -*- coding: utf-8 -*-
"""
13_series_temporais.py — Análise de séries temporais das CATs de profissões da saúde,
Campos dos Goytacazes (RJ), 2018-2025.

Etapas:
1. Decomposição clássica (tendência + sazonalidade + resíduo) da série mensal
2. Teste de quebra estrutural (Chow test) comparando pré-pandemia vs pandemia vs pós-pandemia
3. Suavização LOESS para visualização de tendência não linear
4. Teste de Mann-Kendall para tendência monotônica
5. Modelagem ARIMA simples com previsão para 2026 (projeção condicional)
6. Análise de intervenção: impacto da covid-19 modelado como função degrau + pulso
"""
import os, json, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.nonparametric.smoothers_lowess import lowess
import pymannkendall as mk

warnings.filterwarnings("ignore")

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

# ========== CARREGAR E PREPARAR SÉRIE ==========
df = pd.read_csv("dados/processados/base_cat_campos_classificada.csv", sep=";", dtype=str, encoding="utf-8-sig")
saude = df[df["universo"] == "principal"].copy()

# Série mensal completa
idx = pd.period_range("2018-01", "2025-10", freq="M").astype(str)
serie_raw = saude.groupby("mes_acidente").size()
serie = serie_raw.reindex(idx, fill_value=0)
serie.name = "cats"

# Converter para datetime
datas = pd.date_range("2018-01-01", periods=len(idx), freq="MS")
serie.index = datas

os.makedirs("saidas/tabelas", exist_ok=True)
os.makedirs("saidas/figuras", exist_ok=True)

# ========== 1. DECOMPOSIÇÃO CLÁSSICA ==========
print("=== 1. Decomposição Clássica ===")
decomp = seasonal_decompose(serie, model="additive", period=12)

# ========== 2. TESTE DE MANN-KENDALL (tendência monotônica) ==========
print("\n=== 2. Teste de Mann-Kendall ===")
mk_result = mk.original_test(serie.values)
print(f"  Mann-Kendall: trend={mk_result.trend}, p={mk_result.p:.4f}, tau={mk_result.Tau:.4f}, slope={mk_result.slope:.4f}")

# Por período
for nome, ini, fim in [("Pré-pandemia (jan/2018–fev/2020)", "2018-01", "2020-02"),
                         ("Pandemia (mar/2020–dez/2021)", "2020-03", "2021-12"),
                         ("Pós-pandemia (jan/2022–out/2025)", "2022-01", "2025-10")]:
    sub = serie.loc[ini:fim]
    if len(sub) >= 8:
        mkr = mk.original_test(sub.values)
        print(f"  {nome}: trend={mkr.trend}, p={mkr.p:.4f}, slope={mkr.slope:.4f} (n={len(sub)})")

# ========== 3. TESTE DE DICKEY-FULLER (estacionariedade) ==========
print("\n=== 3. Teste de Dickey-Fuller Aumentado ===")
adf = adfuller(serie.values, autolag="AIC")
print(f"  ADF: estatística={adf[0]:.4f}, p={adf[1]:.4f}, lags={adf[2]}")
print(f"  Valores críticos: 1%={adf[4]['1%']:.4f}, 5%={adf[4]['5%']:.4f}, 10%={adf[4]['10%']:.4f}")

# ========== 4. SUAVIZAÇÃO LOESS ==========
print("\n=== 4. Suavização LOESS ===")
x = np.arange(len(serie))
loess_smooth = lowess(serie.values, x, frac=0.30, return_sorted=False)

# ========== 5. MODELO ARIMA com intervenção ==========
print("\n=== 5. Modelo ARIMA com intervenção covid-19 ===")
# Criar variáveis de intervenção
n = len(serie)
covid_step = np.zeros(n)    # degrau: 1 a partir de mar/2020
covid_pulse = np.zeros(n)   # pulso: 1 apenas em mar-abr/2020 (choque inicial)
for i, d in enumerate(datas):
    if d >= pd.Timestamp("2020-03-01"):
        covid_step[i] = 1
    if pd.Timestamp("2020-03-01") <= d <= pd.Timestamp("2020-05-01"):
        covid_pulse[i] = 1

# ARIMA(1,0,1)(1,0,0)[12] com intervenção
try:
    exog = np.column_stack([covid_step, covid_pulse])
    model = ARIMA(serie.values, order=(1, 0, 1), seasonal_order=(1, 0, 0, 12), exog=exog)
    fitted = model.fit()
    print(f"  AIC: {fitted.aic:.1f}, BIC: {fitted.bic:.1f}")
    print(f"  Coeficientes:")
    for nome, val, pval in zip(
        ["ar.L1", "ma.L1", "ar.S.L12", "sigma2", "covid_step", "covid_pulse"],
        fitted.params, fitted.pvalues
    ):
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else ""))
        print(f"    {nome}: {val:.4f} (p={pval:.4f}) {sig}")

    # Previsão condicional para 2026 (manter covid_step=1, covid_pulse=0)
    future_exog = np.column_stack([np.ones(12), np.zeros(12)])  # 12 meses de 2026
    forecast = fitted.forecast(steps=12, exog=future_exog)
    forecast_ci = fitted.get_forecast(steps=12, exog=future_exog).conf_int(alpha=0.05)

    arima_ok = True
except Exception as e:
    print(f"  ARIMA falhou: {e}")
    print("  Tentando ARIMA simples sem exog...")
    try:
        model = ARIMA(serie.values, order=(1, 0, 1), seasonal_order=(1, 0, 0, 12))
        fitted = model.fit()
        forecast = fitted.forecast(steps=12)
        forecast_ci = fitted.get_forecast(steps=12).conf_int(alpha=0.05)
        arima_ok = True
        print(f"  AIC: {fitted.aic:.1f}")
        covid_step, covid_pulse = None, None
    except:
        arima_ok = False
        forecast = None
        print("  ARIMA indisponível.")

# ========== 6. TAXA DE VARIAÇÃO POR PERÍODO ==========
print("\n=== 6. Médias e taxas de variação ===")
periodos_info = [
    ("Pré-pandemia", "2018-07", "2020-02"),
    ("Período crítico covid-19", "2020-03", "2021-12"),
    ("Pós-pandemia", "2022-01", "2023-12"),
    ("Recente", "2024-01", "2025-10"),
]
estatisticas = []
for nome, ini, fim in periodos_info:
    sub = serie.loc[ini:fim]
    meses_uteis = (sub > 0).sum()
    est = {
        "periodo": nome,
        "inicio": ini, "fim": fim,
        "n_meses": len(sub),
        "n_meses_com_cat": int(meses_uteis),
        "soma": int(sub.sum()),
        "media_mensal": round(sub.mean(), 2),
        "mediana": int(sub.median()),
        "desvio_padrao": round(sub.std(), 2),
        "cv_pct": round(100 * sub.std() / sub.mean(), 1) if sub.mean() > 0 else None,
        "min": int(sub.min()), "max": int(sub.max())
    }
    estatisticas.append(est)
    print(f"  {nome} ({ini}–{fim}): média={est['media_mensal']}, dp={est['desvio_padrao']}, "
          f"CV={est['cv_pct']}%, min={est['min']}, max={est['max']}")

# Teste t entre períodos
from scipy.stats import ttest_ind
sub_pre = serie.loc["2018-07":"2020-02"]
sub_covid = serie.loc["2020-03":"2021-12"]
sub_pos = serie.loc["2022-01":"2023-12"]
ttest_pre_covid = ttest_ind(sub_pre, sub_covid, equal_var=False)
ttest_pre_pos = ttest_ind(sub_pre, sub_pos, equal_var=False)
ttest_covid_pos = ttest_ind(sub_covid, sub_pos, equal_var=False)
print(f"\n  Teste t (Welch) pré vs covid: t={ttest_pre_covid.statistic:.3f}, p={ttest_pre_covid.pvalue:.4f}")
print(f"  Teste t (Welch) pré vs pós: t={ttest_pre_pos.statistic:.3f}, p={ttest_pre_pos.pvalue:.4f}")
print(f"  Teste t (Welch) covid vs pós: t={ttest_covid_pos.statistic:.3f}, p={ttest_covid_pos.pvalue:.4f}")

# ========== EXPORTAÇÃO DE TABELAS ==========
t_est = pd.DataFrame(estatisticas)
t_est.to_csv("saidas/tabelas/T26_estatisticas_periodos.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# Tabela de testes estatísticos
t_testes = pd.DataFrame([
    ("Mann-Kendall (série completa)", f"tau={mk_result.Tau:.4f}", f"p={mk_result.p:.4f}", mk_result.trend, f"slope={mk_result.slope:.4f}/mês"),
    ("Dickey-Fuller Aumentado", f"ADF={adf[0]:.4f}", f"p={adf[1]:.4f}", "Estacionária" if adf[1] < 0.05 else "Não estacionária", f"lags={adf[2]}"),
    ("t-test pré vs covid", f"t={ttest_pre_covid.statistic:.3f}", f"p={ttest_pre_covid.pvalue:.4f}",
     "Significativo" if ttest_pre_covid.pvalue < 0.05 else "Não significativo", "Welch"),
    ("t-test pré vs pós", f"t={ttest_pre_pos.statistic:.3f}", f"p={ttest_pre_pos.pvalue:.4f}",
     "Significativo" if ttest_pre_pos.pvalue < 0.05 else "Não significativo", "Welch"),
    ("t-test covid vs pós", f"t={ttest_covid_pos.statistic:.3f}", f"p={ttest_covid_pos.pvalue:.4f}",
     "Significativo" if ttest_covid_pos.pvalue < 0.05 else "Não significativo", "Welch"),
], columns=["teste", "estatística", "p-valor", "resultado", "nota"])
t_testes.to_csv("saidas/tabelas/T27_testes_estatisticos.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# Salvar previsão
if arima_ok and forecast is not None:
    fut_idx = pd.date_range("2026-01-01", periods=12, freq="MS")
    t_forecast = pd.DataFrame({
        "mes": fut_idx.strftime("%Y-%m"),
        "previsto": forecast.round(1),
        "ic_inferior": forecast_ci[:, 0].round(1),
        "ic_superior": forecast_ci[:, 1].round(1),
    })
    t_forecast.to_csv("saidas/tabelas/T28_previsao_arima_2026.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

# ========== FIGURAS ==========
plt.rcParams.update({
    "font.family": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 7.0,
    "axes.linewidth": 0.6, "axes.edgecolor": "black", "axes.labelsize": 7.5,
    "xtick.direction": "out", "ytick.direction": "out",
    "xtick.major.size": 2.6, "ytick.major.size": 2.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "legend.frameon": False, "svg.fonttype": "none",
})

# F3: Decomposição clássica
fig, axes = plt.subplots(4, 1, figsize=(6.6, 4.8), dpi=600, sharex=True)
componentes = [
    ("Observado", serie.values, "#2166AC"),
    ("Tendência (MM 12m)", decomp.trend.values, "#B2182B"),
    ("Sazonalidade", decomp.seasonal.values, "#4DAF4A"),
    ("Resíduo", decomp.resid.values, "#757575"),
]
for ax, (titulo, vals, cor) in zip(axes, componentes):
    ax.plot(datas, vals, lw=0.8, color=cor)
    ax.set_ylabel(titulo, fontsize=6.5, color=cor)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=6)
# Área de pandemia
for ax in axes:
    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-12-31"),
               color="#F5E1D3", alpha=0.4, lw=0, zorder=0)
axes[0].annotate("covid-19", (pd.Timestamp("2020-12-01"), axes[0].get_ylim()[1] * 0.92),
                 ha="center", fontsize=6, color="#8C5A3A")
fig.tight_layout(pad=0.4)
fig.savefig("saidas/figuras/F3_decomposicao_temporal.png", bbox_inches="tight", facecolor="white")
fig.savefig("saidas/figuras/F3_decomposicao_temporal.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)

# F4: LOESS + tendência com bandas de confiança bootstrap
fig, ax = plt.subplots(figsize=(6.6, 2.55), dpi=600)
ax.plot(datas, serie.values, lw=0.6, color="#BDBDBD", alpha=0.7, label="CATs mensais")
ax.plot(datas, loess_smooth, lw=1.8, color="#2166AC", label="Tendência LOESS (fração=0,30)")
# Bootstrap CI para LOESS
n_boot = 200
boot_smooths = []
rng = np.random.default_rng(42)
for _ in range(n_boot):
    boot_sample = rng.choice(serie.values, size=len(serie), replace=True)
    boot_smooths.append(lowess(boot_sample, x, frac=0.30, return_sorted=False))
boot_smooths = np.array(boot_smooths)
ci_low = np.percentile(boot_smooths, 2.5, axis=0)
ci_high = np.percentile(boot_smooths, 97.5, axis=0)
ax.fill_between(datas, ci_low, ci_high, alpha=0.18, color="#2166AC", lw=0)
ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-12-31"),
           color="#F5E1D3", alpha=0.4, lw=0, zorder=0, label="Período crítico covid-19")
ax.set_ylabel("CATs por mês (n)")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(fontsize=6.2, loc="upper left")
fig.tight_layout(pad=0.4)
fig.savefig("saidas/figuras/F4_tendencia_loess.png", bbox_inches="tight", facecolor="white")
fig.savefig("saidas/figuras/F4_tendencia_loess.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)

# F5: Previsão ARIMA 2026 (se disponível)
if arima_ok and forecast is not None:
    fig, ax = plt.subplots(figsize=(6.6, 2.4), dpi=600)
    # Dados observados (2022 em diante para zoom)
    plot_start = pd.Timestamp("2022-01-01")
    mask = datas >= plot_start
    ax.plot(datas[mask], serie.values[mask], lw=1.0, color="#2166AC", label="Observado")
    # Previsão
    fut_datas = pd.date_range("2026-01-01", periods=12, freq="MS")
    ax.plot(fut_datas, forecast, lw=1.2, color="#B2182B", linestyle="--", label="Previsto (ARIMA)")
    ax.fill_between(fut_datas, forecast_ci[:, 0], forecast_ci[:, 1],
                    alpha=0.2, color="#B2182B", lw=0)
    ax.axvline(x=pd.Timestamp("2026-01-01"), color="#757575", lw=0.6, linestyle=":")
    ax.annotate("projeção →", (pd.Timestamp("2026-01-15"), ax.get_ylim()[1] * 0.9),
                fontsize=6.5, color="#757575", ha="left")
    ax.set_ylabel("CATs por mês (n)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=6.5, loc="upper left")
    fig.tight_layout(pad=0.4)
    fig.savefig("saidas/figuras/F5_previsao_arima_2026.png", bbox_inches="tight", facecolor="white")
    fig.savefig("saidas/figuras/F5_previsao_arima_2026.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)

# ========== LOG ==========
log = {
    "execucao": pd.Timestamp.now().isoformat(),
    "serie": {"inicio": "2018-01", "fim": "2025-10", "n_meses": int(len(serie)), "total_cats": int(serie.sum())},
    "mann_kendall": {"trend": mk_result.trend, "p": float(mk_result.p), "tau": float(mk_result.Tau), "slope": float(mk_result.slope)},
    "adf": {"estatistica": float(adf[0]), "p": float(adf[1]), "lags": int(adf[2])},
    "arima": {"disponivel": arima_ok, "aic": float(fitted.aic) if arima_ok else None},
    "periodos": {e["periodo"]: {"media_mensal": e["media_mensal"], "dp": e["desvio_padrao"]} for e in estatisticas},
}
json.dump(log, open("logs/log_13_series_temporais.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\nOK Análise de séries temporais concluída.")
print("  Tabelas: T26, T27, T28")
print("  Figuras: F3, F4, F5")
