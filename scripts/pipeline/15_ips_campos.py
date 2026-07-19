# -*- coding: utf-8 -*-
"""
15_ips_campos.py — Analise da evolucao do IPS de Campos dos Goytacazes (2024-2026).
"""
import os, pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

# Ler os 3 anos
dados = {}
for ano in [2024, 2025, 2026]:
    f = f"ips-brasil/IPS Brasil {ano} - Tabela de Dados_RJ.csv"
    df = pd.read_csv(f, encoding="utf-8")
    # encontrar linha de Campos
    col_mun = [c for c in df.columns if 'Munic' in c or 'mun' in c.lower()][0]
    c = df[df[col_mun].str.contains("Campos", na=False)]
    if len(c) == 0:
        raise SystemExit(f"Campos nao encontrado no IPS {ano}")
    dados[ano] = c.iloc[0].to_dict()
    print(f"IPS {ano}: {len(df.columns)} colunas, Campos encontrado via coluna '{col_mun}'")

# Mapear colunas manualmente (os nomes variam entre anos)
def get_val(d, candidates):
    for cand in candidates:
        # busca exata primeiro
        if cand in d:
            return d[cand]
        # busca parcial
        for k in d:
            if cand.lower().replace(" ", "") in k.lower().replace(" ", ""):
                return d[k]
    return None

metricas = [
    ("IPS Global", ["Índice de Progresso Social", "Indice de Progresso Social"]),
    ("Necessidades Humanas Basicas", ["Necessidades Humanas Básicas", "Necessidades Humanas Basicas"]),
    ("Fundamentos do Bem-estar", ["Fundamentos do Bem-estar", "Fundamentos do Bem-estar"]),
    ("Oportunidades", ["Oportunidades"]),
    ("Nutricao e Cuidados Medicos", ["Nutrição e Cuidados Médicos Básicos", "Nutricao e Cuidados Medicos Basicos"]),
    ("Saude e Bem-estar", ["Saúde e Bem-estar", "Saude e Bem-estar"]),
    ("Seguranca Pessoal", ["Segurança Pessoal", "Seguranca Pessoal"]),
    ("Acesso ao Conhecimento Basico", ["Acesso ao Conhecimento Básico", "Acesso ao Conhecimento Basico"]),
    ("Direitos Individuais", ["Direitos Individuais"]),
    ("Inclusao Social", ["Inclusão Social", "Inclusao Social"]),
    ("Acesso a Educacao Superior", ["Acesso à Educação Superior", "Acesso a Educacao Superior"]),
    ("Homicidios (por 100 mil)", ["Homicídios", "Homicidios"]),
    ("Mortes no Transito (por 100 mil)", ["Mortes por Acidente de Transporte", "Mortes por Acidentes de Transporte"]),
    ("Mortalidade Infantil ate 5 anos", ["Mortalidade Infantil até 5 Anos", "Mortalidade Infantil até 5 anos", "Mortalidade Infantil ate 5 Anos"]),
    ("Hospitalizacoes CSAP", ["Hospitalizações por Condições Sensíveis à Atenção Primária", "Hospitalizacoes por Condicoes Sensiveis a Atencao Primaria"]),
    ("Expectativa de Vida", ["Expectativa de Vida", "Expectativa de Vida "]),
]

linhas = []
for nome, candidates in metricas:
    v2024 = get_val(dados[2024], candidates)
    v2025 = get_val(dados[2025], candidates)
    v2026 = get_val(dados[2026], candidates)
    try:
        v24 = float(str(v2024).replace(",", "."))
        v25 = float(str(v2025).replace(",", "."))
        v26 = float(str(v2026).replace(",", "."))
        var = v26 - v24
        tend = "melhora" if var > 0 else ("piora" if var < 0 else "estavel")
        if nome == "Homicidios (por 100 mil)" or nome == "Mortes no Transito (por 100 mil)" or nome == "Mortalidade Infantil ate 5 anos" or nome == "Hospitalizacoes CSAP":
            tend = "melhora" if var < 0 else ("piora" if var > 0 else "estavel")
    except:
        var = None
        tend = ""
    linhas.append({
        "Indicador": nome,
        "2024": f"{v24:.2f}" if 'v24' in dir() and var is not None else str(v2024)[:8],
        "2025": f"{v25:.2f}" if 'v25' in dir() and var is not None else str(v2025)[:8],
        "2026": f"{v26:.2f}" if 'v26' in dir() and var is not None else str(v2026)[:8],
        "Var 2024-2026": f"{var:+.2f}" if var is not None else "",
        "Tendencia": tend,
    })

t = pd.DataFrame(linhas)
os.makedirs("saidas/tabelas", exist_ok=True)
t.to_csv("saidas/tabelas/T38_ips_campos_2024_2026.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")

print("\nIPS Campos 2024-2026:")
print(t.to_string(index=False))
print("\nTabela T38 gerada.")
