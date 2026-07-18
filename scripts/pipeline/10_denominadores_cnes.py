# -*- coding: utf-8 -*-
"""
10_denominadores_cnes.py — Denominadores REAIS de força de trabalho em saúde (CNES/DataSUS).

Fonte: TabNet/DataSUS — "CNES – Recursos Humanos – Profissionais – Indivíduos – segundo
CBO 2002 – Rio de Janeiro" (def cnes/cnv/prid02rj.def), competência DEZEMBRO de cada ano
2018–2025, município de atendimento Campos dos Goytacazes (330100).

Robustez:
- o índice do filtro municipal do TabNet é RESOLVIDO dinamicamente e VERIFICADO: a consulta
  de controle (Linha=Município) deve retornar exatamente a linha "330100 CAMPOS DOS GOYTACAZES";
- o Total da consulta por ocupações deve coincidir com o Total da consulta de controle;
- respostas brutas (.prn) são salvas em dados/brutos/cnes-rh/ com proveniência (URL, data/hora);
- retries com backoff; nenhuma imputação: falha => bloqueio registrado, sem dados inventados.

ADVERTÊNCIA DE COMPATIBILIDADE (obrigatória): o CNES conta profissionais (indivíduos) com
vínculo em estabelecimentos de saúde de QUALQUER natureza (estatutário, celetista, autônomo,
PJ; SUS e não SUS); a CAT cobre essencialmente o emprego formal celetista. As razões
CAT/1.000 profissionais CNES são EXPLORATÓRIAS (densidade de comunicação), NÃO incidência
nem risco ocupacional.
"""
import os, re, csv, json, html, time, datetime, unicodedata, urllib.request, urllib.parse

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

URL = "http://tabnet.datasus.gov.br/cgi/tabcgi.exe?cnes/cnv/prid02rj.def"
ANOS = list(range(2018, 2026))
ARQ = {a: f"pfrj{str(a)[2:]}12.dbf" for a in ANOS}          # dezembro de cada ano
DIR_BRUTO = os.path.join("dados", "brutos", "cnes-rh")
os.makedirs(DIR_BRUTO, exist_ok=True)
NL = chr(10)

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()

def post_tabnet(pares, tentativas=4):
    body = "&".join(f"{urllib.parse.quote(k.encode('latin-1'))}={urllib.parse.quote(v.encode('latin-1'))}"
                    for k, v in pares)
    for i in range(tentativas):
        try:
            req = urllib.request.Request(URL, data=body.encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
            t = urllib.request.urlopen(req, timeout=180).read().decode("latin-1")
            m = re.search(r"(?is)<pre>(.*?)</pre>", t)
            if m:
                return m.group(1)
        except Exception as e:
            print(f"  tentativa {i+1} falhou: {e}")
        time.sleep(3 * (i + 1))
    return None

def linhas_prn(pre):
    out = []
    for l in pre.splitlines():
        l = html.unescape(l).strip()
        m = re.match(r'^"(.*)";(-|\d+)$', l)
        if m:
            out.append((m.group(1), 0 if m.group(2) == "-" else int(m.group(2))))
    return out

def resolver_indice_municipio():
    """Descobre e verifica o índice do TabNet para 330100 (a ordem do servidor difere da página)."""
    for idx in list(range(14, 30)):
        pre = post_tabnet([("Linha", "Município"), ("Coluna", "--Não-Ativa--"), ("Incremento", "Quantidade"),
                           ("Arquivos", ARQ[2018]), ("SMunicípio", str(idx)), ("formato", "prn"), ("mostre", "Mostra")])
        rows = [r for r in linhas_prn(pre or "") if r[0] not in ("Total",) and not r[0].startswith("Munic")]
        if rows and rows[0][0].startswith("330100"):
            return idx, rows[0]
        time.sleep(1)
    return None, None

def main():
    prov = {"fonte": "TabNet/DataSUS CNES-RH prid02rj.def", "url": URL,
            "consulta_em": datetime.datetime.now().isoformat(timespec="seconds"),
            "competencias": {a: ARQ[a] for a in ANOS}, "verificacoes": {}, "bloqueios": []}

    idx, linha = resolver_indice_municipio()
    if idx is None:
        prov["bloqueios"].append("Não foi possível resolver o índice municipal 330100 no TabNet; nada foi calculado.")
        json.dump(prov, open("logs/log_10_denominadores.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        raise SystemExit("BLOQUEIO: TabNet indisponível ou estrutura alterada. Nenhum dado inventado.")
    prov["indice_municipio_tabnet"] = idx
    prov["verificacoes"]["controle_2018"] = f"{linha[0]} = {linha[1]}"
    print(f"Índice municipal resolvido e verificado: {idx} -> {linha[0]} ({linha[1]} profissionais em dez/2018)")

    registros = []
    for ano in ANOS:
        # 1) controle: total municipal
        pre_c = post_tabnet([("Linha", "Município"), ("Coluna", "--Não-Ativa--"), ("Incremento", "Quantidade"),
                             ("Arquivos", ARQ[ano]), ("SMunicípio", str(idx)), ("formato", "prn"), ("mostre", "Mostra")])
        rows_c = linhas_prn(pre_c or "")
        alvo = [r for r in rows_c if r[0].startswith("330100")]
        if not alvo:
            prov["bloqueios"].append(f"{ano}: controle municipal não retornou 330100; ano descartado.")
            continue
        total_ctrl = alvo[0][1]
        # 2) ocupações
        pre_o = post_tabnet([("Linha", "Ocupações_em_geral"), ("Coluna", "--Não-Ativa--"), ("Incremento", "Quantidade"),
                             ("Arquivos", ARQ[ano]), ("SMunicípio", str(idx)), ("formato", "prn"), ("mostre", "Mostra")])
        if not pre_o:
            prov["bloqueios"].append(f"{ano}: consulta de ocupações sem resposta; ano descartado.")
            continue
        open(os.path.join(DIR_BRUTO, f"cnes_rh_campos_{ano}12_ocupacoes.prn"), "w", encoding="utf-8").write(pre_o)
        open(os.path.join(DIR_BRUTO, f"cnes_rh_campos_{ano}12_controle.prn"), "w", encoding="utf-8").write(pre_c)
        rows_o = linhas_prn(pre_o)
        total_o = next((v for k, v in rows_o if k == "Total"), None)
        prov["verificacoes"][str(ano)] = {"total_controle": total_ctrl, "total_ocupacoes": total_o,
                                          "consistente": total_ctrl == total_o}
        if total_ctrl != total_o:
            prov["bloqueios"].append(f"{ano}: totais divergentes (controle {total_ctrl} x ocupações {total_o}); ano descartado.")
            continue
        # detalhe = linhas com minúsculas (títulos CBO); MAIÚSCULAS = seções/famílias do TabNet
        for nome, v in rows_o:
            if nome in ("Total",) or nome.lower().startswith("ocupa"):
                continue
            eh_detalhe = any(c.islower() for c in nome)
            registros.append({"ano": ano, "competencia": f"{ano}-12", "nivel": "ocupacao" if eh_detalhe else "secao",
                              "ocupacao_cnes": re.sub(r"\s+", " ", nome).strip(), "n_profissionais": v})
        print(f"{ano}: {total_ctrl} profissionais (indivíduos) CNES em Campos; {sum(1 for r in registros if r['ano']==ano and r['nivel']=='ocupacao')} ocupações")
        time.sleep(1.5)

    # ---- mapeamento explícito ocupação CNES -> categoria do estudo ------------
    def categoria(nome):
        n = norm(nome)
        if n.startswith("medico"): return ("principal", "Medicina")
        if n.startswith("enfermeiro"): return ("principal", "Enfermagem – enfermeiros")
        if n.startswith(("tecnico de enfermagem", "auxiliar de enfermagem")): return ("principal", "Enfermagem – técnicos e auxiliares")
        if n.startswith("instrumentador"): return ("principal", "Instrumentação cirúrgica")
        if n.startswith(("cirurgiao dentista", "tecnico em saude bucal", "auxiliar em saude bucal",
                         "atendente de consultorio dentario", "protetico", "tecnico de higiene dental",
                         "auxiliar de protese")): return ("principal", "Odontologia e saúde bucal")
        if n.startswith("farmaceutico"): return ("principal", "Farmácia")
        if n.startswith(("tecnico em farmacia", "auxiliar de farmacia", "auxiliar tecnico em laboratorio de farmacia")):
            return ("principal", "Farmácia – técnicos e auxiliares")
        if n.startswith("fisioterapeuta"): return ("principal", "Fisioterapia")
        if n.startswith("nutricionista"): return ("principal", "Nutrição")
        if n.startswith("fonoaudiologo"): return ("principal", "Fonoaudiologia")
        if n.startswith("terapeuta ocupacional"): return ("principal", "Terapia ocupacional e afins")
        if n.startswith("biomedico"): return ("principal", "Biomedicina")
        if n.startswith(("tecnico em radiologia", "tecnico em patologia", "auxiliar de laboratorio",
                         "citotecnico", "auxiliar de banco de sangue", "tecnico de laboratorio",
                         "auxiliar tecnico em patologia")): return ("principal", "Diagnóstico e laboratório – técnicos e auxiliares")
        if n.startswith(("agente comunitario de saude", "visitador sanitario", "atendente de enfermagem",
                         "parteira")): return ("principal", "Agentes comunitários de saúde e afins")
        if n.startswith("agente de combate as endemias") or n.startswith("agente de saude publica"):
            return ("principal", "Agentes de combate às endemias")
        if n.startswith("psicologo"): return ("multiprofissional", "Psicologia")
        if n.startswith("assistente social"): return ("multiprofissional", "Serviço social")
        if n.startswith(("profissional de educacao fisica", "preparador fisico", "avaliador fisico")):
            return ("multiprofissional", "Educação física")
        if n.startswith("biologo"): return ("multiprofissional", "Biologia")
        return ("nao_mapeada", "Outras ocupações CNES (não mapeadas ao estudo)")

    det = [r for r in registros if r["nivel"] == "ocupacao"]
    for r in det:
        r["universo"], r["categoria_estudo"] = categoria(r["ocupacao_cnes"])

    with open("dados/processados/cnes_profissionais_campos_2018_2025.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["ano", "competencia", "nivel", "ocupacao_cnes", "universo",
                                          "categoria_estudo", "n_profissionais"], delimiter=";")
        w.writeheader()
        for r in registros:
            w.writerow({**{"universo": "", "categoria_estudo": ""}, **r})

    # ---- T21: denominadores por categoria x ano -------------------------------
    from collections import defaultdict
    T21 = defaultdict(dict)
    anos_ok = sorted({r["ano"] for r in det})
    for r in det:
        T21[r["categoria_estudo"]][r["ano"]] = T21[r["categoria_estudo"]].get(r["ano"], 0) + r["n_profissionais"]
    with open("saidas/tabelas/T21_denominadores_cnes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["categoria_estudo"] + [str(a) for a in anos_ok])
        for cat in sorted(T21):
            w.writerow([cat] + [T21[cat].get(a, 0) for a in anos_ok])

    # ---- T22: razões exploratórias CAT / 1.000 profissionais CNES -------------
    cat_counts = defaultdict(lambda: defaultdict(int))
    with open("dados/processados/base_cat_campos_profissoes_saude_processada.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["universo"] == "principal":
                cat_counts[row["categoria_profissional"]][int(row["ano_acidente"])] += 1
    PARCIAIS = {2018, 2022, 2024, 2025}
    linhas22 = []
    for cat in sorted(set(cat_counts) | {"TOTAL universo principal"}):
        for ano in anos_ok:
            num = (sum(cat_counts[c][ano] for c in cat_counts) if cat.startswith("TOTAL")
                   else cat_counts[cat].get(ano, 0))
            den = (sum(v.get(ano, 0) for k, v in T21.items() if k not in
                       ("Outras ocupações CNES (não mapeadas ao estudo)", "Psicologia", "Serviço social",
                        "Educação física", "Biologia")) if cat.startswith("TOTAL") else T21.get(cat, {}).get(ano, 0))
            razao = round(1000 * num / den, 1) if den >= 30 and num >= 5 else None
            linhas22.append({"categoria": cat, "ano": ano, "cat_n": num, "cnes_dez_n": den,
                             "razao_por_1000": razao if razao is not None else "supresso (num<5 ou den<30)",
                             "cobertura_cat": "parcial*" if ano in PARCIAIS else "integral",
                             "advertencia": "exploratória: CNES inclui todos os vínculos (estatutário/PJ/autônomo); CAT cobre celetistas — NÃO é incidência"})
    with open("saidas/tabelas/T22_razao_cat_1000_cnes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas22[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(linhas22)

    prov["nota_rais"] = ("RAIS/eSocial (vínculos formais por CBO x município x ano): microdados disponíveis apenas via "
                         "ftp.mtps.gov.br/pdet/microdados (arquivos de vários GB por UF/ano, formato 7z) ou BigQuery com "
                         "credenciais — inviável nesta execução; BLOQUEIO registrado, sem qualquer imputação. "
                         "Prioridade para trabalho futuro.")
    json.dump(prov, open("logs/log_10_denominadores.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(NL + "Proveniência e verificações em logs/log_10_denominadores.json")
    print("T21 (denominadores) e T22 (razões exploratórias) gravadas em saidas/tabelas/")

if __name__ == "__main__":
    main()
