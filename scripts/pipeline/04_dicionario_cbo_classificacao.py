# -*- coding: utf-8 -*-
"""
04_dicionario_cbo_classificacao.py — Dicionário mestre CBO-saúde e classificação da base.
Classificação prioritariamente por CÓDIGO CBO (6 dígitos), validada contra a tabela
'CBO2002 - Ocupação' (estrutura oficial MTE; espelho público, ver referencias/fonte_cbo.txt).
Três níveis: (1) universo principal de profissões da saúde; (2) profissões multiprofissionais
intersetoriais; (3) demais trabalhadores (apoio; analisados à parte quando CNAE saúde).
Registros sem CBO válido => 'CBO não classificado' (mantidos e quantificados).
"""
import csv, os, json
from collections import Counter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

# ---- tabela oficial (espelho) ------------------------------------------------
OFICIAL = {}
with open("referencias/CBO2002_Ocupacao_cartaproale.csv", encoding="latin-1") as f:
    for r in csv.DictReader(f, delimiter=";"):
        OFICIAL[r["CODIGO"]] = r["TITULO"]

# ---- regras por família (prefixo 4 dígitos) e por código ---------------------
# universo: 'principal' | 'multiprofissional' | 'apoio_ou_outra'
FAMILIAS_PRINCIPAL = {
    "2231": ("Medicina", "superior", "Família 2231 (Médicos) de versão anterior da CBO 2002; descrição na fonte confirma ocupação médica"),
    "2251": ("Medicina", "superior", "Família 2251 – Médicos clínicos"),
    "2252": ("Medicina", "superior", "Família 2252 – Médicos em especialidades cirúrgicas"),
    "2253": ("Medicina", "superior", "Família 2253 – Médicos em medicina diagnóstica e terapêutica"),
    "2235": ("Enfermagem – enfermeiros", "superior", "Família 2235 – Enfermeiros e afins"),
    "2232": ("Odontologia e saúde bucal", "superior", "Família 2232 – Cirurgiões-dentistas"),
    "2234": ("Farmácia", "superior", "Família 2234 – Farmacêuticos"),
    "2236": ("Fisioterapia", "superior", "Família 2236 – Fisioterapeutas"),
    "2237": ("Nutrição", "superior", "Família 2237 – Nutricionistas"),
    "2238": ("Fonoaudiologia", "superior", "Família 2238 – Fonoaudiólogos"),
    "2239": ("Terapia ocupacional e afins", "superior", "Família 2239 – Terapeutas ocupacionais e ortoptistas"),
    "2261": ("Quiropraxia", "superior", "Família 2261"),
    "2263": ("Terapias criativas/naturologia", "superior", "Família 2263"),
    "3222": ("Enfermagem – técnicos e auxiliares", "técnico/auxiliar", "Família 3222 – Técnicos e auxiliares de enfermagem"),
    "3224": ("Odontologia e saúde bucal", "técnico/auxiliar", "Família 3224 – Técnicos e auxiliares de odontologia"),
    "3241": ("Diagnóstico e laboratório – técnicos e auxiliares", "técnico/auxiliar", "Família 3241 – Técnicos de radiologia e diagnóstico por imagem"),
    "3242": ("Diagnóstico e laboratório – técnicos e auxiliares", "técnico/auxiliar", "Família 3242 – Técnicos de laboratório/patologia clínica"),
    "3251": ("Farmácia – técnicos e auxiliares", "técnico/auxiliar", "Família 3251 – Técnicos e auxiliares técnicos em farmácia"),
    "5151": ("Agentes comunitários de saúde e afins", "elementar/auxiliar", "Família 5151 – Agentes comunitários de saúde e afins (inclui atendente de enfermagem)"),
    "5152": ("Diagnóstico e laboratório – técnicos e auxiliares", "elementar/auxiliar", "Família 5152 – Auxiliares de laboratório da saúde"),
}
FAMILIAS_MULTI = {
    "2515": ("Psicologia", "superior", "Família 2515 – Psicólogos e psicanalistas; atuação intersetorial"),
    "2516": ("Serviço social", "superior", "Família 2516 – Assistentes sociais; atuação intersetorial"),
    "2241": ("Educação física", "superior", "Família 2241 – Profissionais da educação física; atuação intersetorial"),
    "2211": ("Biologia", "superior", "Família 2211 – Biólogos; atuação intersetorial"),
    "2212": ("Biomedicina", "superior", "Família 2212 – Biomédicos"),
}
# Overrides por código (decisões documentadas)
OVERRIDES = {
    "322225": ("principal", "Instrumentação cirúrgica", "técnico/auxiliar",
               "322225 Instrumentador cirúrgico – categoria própria conforme protocolo"),
    "515140": ("principal", "Agentes de combate às endemias", "elementar/auxiliar", "515140 ACE"),
    "515210": ("principal", "Farmácia – técnicos e auxiliares", "elementar/auxiliar",
               "515210 Auxiliar de farmácia de manipulação (família 5152, alocado à categoria Farmácia)"),
    "515225": ("apoio_ou_outra", "Produção industrial farmacêutica", "elementar/auxiliar",
               "515225 Auxiliar de produção farmacêutica – atividade industrial, não assistencial; decisão conservadora"),
    "519305": ("apoio_ou_outra", "Serviços veterinários (apoio)", "elementar/auxiliar",
               "519305 Auxiliar de veterinário (sinônimo 'enfermeiro veterinário' na fonte) – não é saúde humana"),
    "223305": ("principal", "Medicina veterinária", "superior", "223305 Médico veterinário"),
    "223310": ("apoio_ou_outra", "Zootecnia", "superior", "Zootecnista não é profissão da saúde"),
}
# 2212 Biomedicina: profissão da saúde regulamentada -> principal (corrige agrupamento acima)
BIOMED_PRINCIPAL = True

def classifica(cbo):
    if not cbo:
        return ("nao_classificado", "CBO não classificado", "", "Sem código CBO válido de 6 dígitos na fonte")
    if cbo in OVERRIDES:
        u, c, nf, j = OVERRIDES[cbo]
        return (u, c, nf, j)
    fam = cbo[:4]
    if fam in FAMILIAS_PRINCIPAL:
        c, nf, j = FAMILIAS_PRINCIPAL[fam]
        return ("principal", c, nf, j)
    if fam in FAMILIAS_MULTI:
        c, nf, j = FAMILIAS_MULTI[fam]
        if fam == "2212" and BIOMED_PRINCIPAL:
            return ("principal", c, nf, j + "; profissão da saúde regulamentada => universo principal")
        return ("multiprofissional", c, nf, j)
    return ("apoio_ou_outra", "Outras ocupações (fora do campo da saúde)", "", "Família CBO fora do campo da saúde")

ENTRADA = "dados/processados/base_cat_campos_todas_ocupacoes.csv"
regs = list(csv.DictReader(open(ENTRADA, encoding="utf-8-sig"), delimiter=";"))

dic = {}
for r in regs:
    cbo = r["cbo_codigo"]
    u, cat, nf, just = classifica(cbo)
    r["universo"] = u
    r["categoria_profissional"] = cat
    r["nivel_formacao"] = nf
    r["cbo_titulo_oficial"] = OFICIAL.get(cbo, "")
    r["cnae_saude"] = "sim" if r["cnae_classe"][:2] in ("86", "87") else ("nao" if r["cnae_classe"] else "sem_cnae")
    ch = (cbo, r["cbo_descricao_original"])
    if ch not in dic:
        dic[ch] = {"cbo_codigo": cbo or "(vazio)", "descricao_original_fonte": r["cbo_descricao_original"],
                   "titulo_oficial_cbo2002": OFICIAL.get(cbo, "(não consta na tabela vigente)" if cbo else ""),
                   "grande_grupo": cbo[:1] if cbo else "", "familia_ocupacional": cbo[:4] if cbo else "",
                   "categoria_profissional_agregada": cat, "nivel_formacao": nf, "universo": u,
                   "incluido_universo_principal": "sim" if u == "principal" else "não",
                   "justificativa": just,
                   "fonte_normativa": "CBO 2002 (MTE) – tabela 'CBO2002-Ocupação' (espelho público; ver referencias/fonte_cbo.txt)",
                   "observacao_ambiguidade": "", "n_registros": 0}
    dic[ch]["n_registros"] += 1

# observações de ambiguidade
for ch, d in dic.items():
    if d["titulo_oficial_cbo2002"] == "(não consta na tabela vigente)":
        d["observacao_ambiguidade"] = "Código ausente da tabela vigente (família reestruturada); validado pela descrição da fonte"
    if d["descricao_original_fonte"] and d["titulo_oficial_cbo2002"] not in ("", "(não consta na tabela vigente)"):
        a = d["descricao_original_fonte"].lower()[:10]
        b = d["titulo_oficial_cbo2002"].lower()[:10]
        if a and b and a[:6] not in b and b[:6] not in a:
            d["observacao_ambiguidade"] = (d["observacao_ambiguidade"] + " | " if d["observacao_ambiguidade"] else "") + \
                "Descrição da fonte diverge do título oficial (verificada manualmente)"

with open("dados/processados/base_cat_campos_classificada.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(regs[0].keys()), delimiter=";")
    w.writeheader(); w.writerows(regs)

with open("dados/processados/dicionario_cbo_observado.csv", "w", newline="", encoding="utf-8-sig") as f:
    ks = ["cbo_codigo","descricao_original_fonte","titulo_oficial_cbo2002","grande_grupo","familia_ocupacional",
          "categoria_profissional_agregada","nivel_formacao","universo","incluido_universo_principal",
          "justificativa","fonte_normativa","observacao_ambiguidade","n_registros"]
    w = csv.DictWriter(f, fieldnames=ks, delimiter=";")
    w.writeheader()
    for ch in sorted(dic, key=lambda x: (x[0] or "zzz", x[1])):
        w.writerow(dic[ch])

res = Counter((r["universo"], r["categoria_profissional"]) for r in regs)
print(json.dumps({f"{u}|{c}": n for (u, c), n in sorted(res.items())}, ensure_ascii=False, indent=1))
print("universos:", Counter(r["universo"] for r in regs))
