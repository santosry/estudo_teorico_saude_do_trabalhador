# -*- coding: utf-8 -*-
"""
RAIS_genero.py — Extrai sexo, remuneração e natureza jurídica da RAIS 2018-2025
para as profissões da saúde em Campos dos Goytacazes (330100).
Autodetecta colunas pelos cabeçalhos (layout varia entre anos).
Produz 3 tabelas para a discussão de gênero.
"""
import os, csv, tempfile, py7zr, json, sys
from collections import defaultdict
from statistics import median

BASE = r'C:\Users\oorie\OneDrive\Documentos\TRABALHOS\SAÚDE DO TRABALHADOR'
RAIS_DIR = os.path.join(BASE, 'banco de dados', 'rais')
SAIDAS = os.path.join(BASE, 'saidas', 'tabelas')
os.makedirs(SAIDAS, exist_ok=True)

MUN_COD = "330100"
ANOS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Classificação de CBO — idêntica à do pipeline
def classifica(cbo):
    fam = cbo[:4] if cbo else ""
    mapa = {
        "2235": "Enfermagem — enfermeiros",
        "3222": "Enfermagem — técnicos e auxiliares",
        "2251": "Medicina", "2252": "Medicina", "2253": "Medicina", "2231": "Medicina",
        "2236": "Fisioterapia", "2234": "Farmácia",
        "3251": "Farmácia — técnicos e auxiliares",
        "2237": "Nutrição", "2238": "Fonoaudiologia",
        "2232": "Odontologia e saúde bucal", "3224": "Odontologia e saúde bucal",
        "3241": "Diagnóstico e laboratório — técnicos e auxiliares",
        "3242": "Diagnóstico e laboratório — técnicos e auxiliares",
        "5152": "Diagnóstico e laboratório — técnicos e auxiliares",
        "5151": "Agentes comunitários de saúde e afins",
        "3226": "Instrumentação cirúrgica",
        "2515": "Psicologia", "2516": "Serviço social",
        "2241": "Educação física", "2211": "Biologia", "2212": "Biomedicina"
    }
    if cbo in ("322225", "515140", "515210", "223305"):
        ov = {"322225": "Instrumentação cirúrgica",
              "515140": "Agentes de combate às endemias",
              "515210": "Farmácia — técnicos e auxiliares",
              "223305": "Medicina veterinária"}
        return ov[cbo]
    return mapa.get(fam)

def detectar_colunas(header_line):
    """Autodetecta posições das colunas pelos nomes no cabeçalho."""
    # Delimitador: 2018-2022 usa ';', 2023+ usa ','
    delim = ',' if header_line.count(',') > header_line.count(';') else ';'
    cols = [c.strip().strip('"') for c in header_line.split(delim)]
    idx = {}
    for i, nome in enumerate(cols):
        n = nome.upper()
        # CBO
        if 'CBO' in n and ('2002' in n or 'OCUPA' in n):
            idx['cbo'] = i
        # CNAE
        if ('CNAE' in n and '20' in n and 'CLASSE' in n):
            idx['cnae'] = i
        elif 'CNAE 2.0' in n:
            idx['cnae'] = i
        # Município
        if 'MUNIC' in n and 'IBGE' not in n:
            idx['mun'] = i
        if n == 'MUNICÍPIO':
            idx['mun'] = i
        # Ativo 31/12
        if 'ATIVO' in n and '31' in n:
            idx['ativo'] = i
        elif 'VÍNCULO ATIVO' in n:
            idx['ativo'] = i
        # Sexo
        if 'SEXO' in n and 'TRAB' in n:
            idx['sexo'] = i
        # Natureza Jurídica
        if 'NATUREZA' in n and 'JUR' in n:
            idx['natjur'] = i
        # Remuneração (valor nominal, não faixa)
        if 'VL REMUN' in n or 'VALOR REMUN' in n or 'REMUNERAÇÃO' in n:
            if 'MÉDIA' in n or 'DEZEM' in n:
                if 'remun_dez' not in idx:
                    idx['remun_dez'] = i
        # Faixa Remuneração Dezembro (SM) — para pré-2023
        if 'FAIXA REMUN' in n and 'DEZEM' in n:
            idx['faixa_remun'] = i
        # Hora contrato
        if ('HORA' in n and 'CONTR' in n) or 'HORAS CONTRATUAIS' in n:
            idx['horas'] = i
        # Idade / Faixa Etária
        if 'FAIXA ET' in n or 'IDADE' in n:
            idx['idade'] = i
        # Escolaridade
        if 'ESCOLARIDADE' in n or 'GRAU INSTRU' in n:
            idx['escolaridade'] = i

    # Fallbacks
    if 'cbo' not in idx:
        for i, nome in enumerate(cols):
            if 'CBO' in nome.upper():
                idx['cbo'] = i
                break

    print(f"  Delim='{delim}' | Cols detectadas: cbo={idx.get('cbo')}, cnae={idx.get('cnae')}, "
          f"sexo={idx.get('sexo')}, natjur={idx.get('natjur')}, remun_dez={idx.get('remun_dez')}, "
          f"faixa_remun={idx.get('faixa_remun')}, horas={idx.get('horas')}, "
          f"mun={idx.get('mun')}, ativo={idx.get('ativo')}")
    return delim, idx

def extrair_ano(ano, path_7z):
    """Extrai registros de saúde em Campos com sexo, remuneração, natjur."""
    with tempfile.TemporaryDirectory() as td:
        with py7zr.SevenZipFile(path_7z, 'r') as z:
            z.extractall(td)
        txts = [f for f in os.listdir(td) if f.upper().endswith(('.TXT', '.COMT'))]
        if not txts:
            txts = [f for f in os.listdir(td) if not f.startswith('.')]
        if not txts:
            raise RuntimeError(f"Nenhum arquivo no 7z de {ano}: {os.listdir(td)[:10]}")

        with open(os.path.join(td, txts[0]), 'r', encoding='latin-1', errors='replace') as fh:
            header = fh.readline()
            delim, idx = detectar_colunas(header)

            max_col = max(idx.values())
            registros = []

            for row in csv.reader(fh, delimiter=delim, quotechar='"'):
                try:
                    if len(row) <= max_col:
                        continue
                    # Filtro município
                    if row[idx['mun']].strip() != MUN_COD:
                        continue
                    # Filtro ativo
                    if 'ativo' in idx:
                        if row[idx['ativo']].strip() != '1':
                            continue
                    # CBO
                    cbo = row[idx['cbo']].strip()
                    if not cbo[:1].isdigit():
                        continue
                    cat = classifica(cbo)
                    if not cat:
                        continue
                    # CNAE (divisão)
                    cnae_div = row[idx['cnae']].strip()[:2] if 'cnae' in idx else ''

                    # Sexo
                    sexo_val = row[idx['sexo']].strip() if 'sexo' in idx else ''
                    if sexo_val in ('1', 'M', 'MASCULINO'):
                        sexo = 'M'
                    elif sexo_val in ('2', 'F', 'FEMININO'):
                        sexo = 'F'
                    else:
                        sexo = 'NI'

                    # Natureza Jurídica (estatutário vs celetista)
                    natjur = ''
                    if 'natjur' in idx:
                        nj = row[idx['natjur']].strip()
                        # Códigos de administração pública (estatutários):
                        # 1xxx = Adm Pública, mas precisa filtrar melhor
                        natjur = nj

                    # Remuneração nominal
                    remun = None
                    if 'remun_dez' in idx:
                        try:
                            val = row[idx['remun_dez']].strip().replace(',', '.')
                            if val and val != '':
                                remun = float(val)
                        except:
                            pass

                    # Horas contratadas
                    horas = None
                    if 'horas' in idx:
                        try:
                            h = row[idx['horas']].strip()
                            if h and h != '':
                                horas = int(float(h))
                        except:
                            pass

                    registros.append({
                        'cat': cat, 'sexo': sexo, 'natjur': natjur,
                        'remun': remun, 'horas': horas, 'cnae_div': cnae_div
                    })
                except Exception:
                    pass

    return registros

def main():
    # Acumuladores
    tab_sexo_cat = defaultdict(lambda: {'M': 0, 'F': 0, 'NI': 0, 'total': 0})  # Tabela A
    tab_sexo_cat_ano = defaultdict(lambda: defaultdict(lambda: {'M': 0, 'F': 0, 'NI': 0}))  # Tabela B (por ano)
    tab_remun = defaultdict(lambda: {'M': [], 'F': []})  # Tabela C (remuneração)

    # Natureza jurídica simplificada
    # Códigos RAIS: natureza jurídica 
    # 1xxx = Administração Pública (municipal = 1244, 1031, etc.)
    # Mas precisamos diferenciar CLT vs Estatutário.
    # Na RAIS, a natureza jurídica + tipo de vínculo indicam o regime.
    # Simplificando: NJ iniciando com '1' = público; demais = privado
    tab_nj_sexo_cat = defaultdict(lambda: {'pub_M': 0, 'pub_F': 0, 'priv_M': 0, 'priv_F': 0})

    for ano in ANOS:
        path = os.path.join(RAIS_DIR, f"RAIS_{ano}_MG_ES_RJ.7z")
        if not os.path.exists(path):
            print(f"  {ano}: arquivo não encontrado, pulando.")
            continue
        print(f"\n{ano}:")
        regs = extrair_ano(ano, path)
        n = len(regs)
        n_f = sum(1 for r in regs if r['sexo'] == 'F')
        n_m = sum(1 for r in regs if r['sexo'] == 'M')
        print(f"  Total saúde Campos: {n} (F={n_f}, M={n_m})")

        for r in regs:
            cat = r['cat']
            sx = r['sexo']
            tab_sexo_cat[cat][sx] = tab_sexo_cat[cat].get(sx, 0) + 1
            tab_sexo_cat[cat]['total'] += 1
            tab_sexo_cat_ano[ano][cat][sx] = tab_sexo_cat_ano[ano][cat].get(sx, 0) + 1

            # Remuneração
            if r['remun'] is not None and r['remun'] > 0:
                tab_remun[cat][sx].append(r['remun'])

            # Natureza jurídica
            nj = r['natjur']
            is_pub = nj.startswith('1') if nj else False
            if is_pub:
                if sx == 'F':
                    tab_nj_sexo_cat[cat]['pub_F'] += 1
                elif sx == 'M':
                    tab_nj_sexo_cat[cat]['pub_M'] += 1
            else:
                if sx == 'F':
                    tab_nj_sexo_cat[cat]['priv_F'] += 1
                elif sx == 'M':
                    tab_nj_sexo_cat[cat]['priv_M'] += 1

    # ============== SALVAR TABELAS ==============

    # TABELA A: Sexo por categoria profissional (total 2018-2025)
    cats_ordem = sorted(tab_sexo_cat.keys(),
                        key=lambda c: tab_sexo_cat[c]['total'], reverse=True)
    with open(os.path.join(SAIDAS, 'T_genero_sexo_por_categoria.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Categoria profissional', 'Feminino (n)', 'Feminino (%)',
                     'Masculino (n)', 'Masculino (%)', 'Total'])
        for cat in cats_ordem:
            d = tab_sexo_cat[cat]
            tot = d['total']
            pct_f = round(100 * d['F'] / tot, 1) if tot > 0 else 0
            pct_m = round(100 * d['M'] / tot, 1) if tot > 0 else 0
            w.writerow([cat, d['F'], pct_f, d['M'], pct_m, tot])

    print(f"\n✓ Tabela A: {len(cats_ordem)} categorias em {SAIDAS}/T_genero_sexo_por_categoria.csv")

    # TABELA B: Sexo por categoria E natureza jurídica (público vs privado)
    with open(os.path.join(SAIDAS, 'T_genero_natjur_por_categoria.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Categoria profissional', 'Privado F (n)', 'Privado F (%)',
                     'Privado M (n)', 'Privado M (%)',
                     'Público F (n)', 'Público F (%)',
                     'Público M (n)', 'Público M (%)', 'Total'])
        for cat in cats_ordem:
            d = tab_nj_sexo_cat[cat]
            tot = d['pub_F'] + d['pub_M'] + d['priv_F'] + d['priv_M']
            if tot == 0:
                continue
            w.writerow([
                cat,
                d['priv_F'], round(100 * d['priv_F'] / tot, 1) if tot else 0,
                d['priv_M'], round(100 * d['priv_M'] / tot, 1) if tot else 0,
                d['pub_F'], round(100 * d['pub_F'] / tot, 1) if tot else 0,
                d['pub_M'], round(100 * d['pub_M'] / tot, 1) if tot else 0,
                tot
            ])

    print(f"✓ Tabela B: natureza jurídica × sexo em {SAIDAS}/T_genero_natjur_por_categoria.csv")

    # TABELA C: Remuneração mediana por sexo e categoria
    with open(os.path.join(SAIDAS, 'T_genero_remuneracao_por_categoria.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Categoria profissional',
                     'Remun. mediana F (R$)', 'Remun. mediana M (R$)',
                     'n F', 'n M', 'Razão F/M'])
        for cat in cats_ordem:
            d = tab_remun[cat]
            med_f = round(median(d['F']), 2) if d['F'] else None
            med_m = round(median(d['M']), 2) if d['M'] else None
            razao = round(med_f / med_m, 2) if (med_f and med_m and med_m > 0) else None
            w.writerow([cat, med_f if med_f else '—', med_m if med_m else '—',
                         len(d['F']), len(d['M']), razao if razao else '—'])

    print(f"✓ Tabela C: remuneração em {SAIDAS}/T_genero_remuneracao_por_categoria.csv")

    # ===== SUMÁRIO para o texto =====
    print("\n===== SUMÁRIO PARA O ENSAIO =====")
    # Enfermagem técnica
    tec = tab_sexo_cat.get('Enfermagem — técnicos e auxiliares', {})
    enf = tab_sexo_cat.get('Enfermagem — enfermeiros', {})
    med = tab_sexo_cat.get('Medicina', {})
    for nome, d in [('Téc. enfermagem', tec), ('Enfermeiros', enf), ('Medicina', med)]:
        tot = d.get('total', 0)
        if tot > 0:
            print(f"  {nome}: {d.get('F',0)}F ({round(100*d.get('F',0)/tot,1)}%) / "
                  f"{d.get('M',0)}M ({round(100*d.get('M',0)/tot,1)}%) — total={tot}")

    # Natureza jurídica para as principais
    print("\nNatureza jurídica × sexo (principais categorias):")
    for cat in ['Enfermagem — técnicos e auxiliares', 'Enfermagem — enfermeiros', 'Medicina']:
        d = tab_nj_sexo_cat.get(cat, {})
        tot = d.get('pub_F', 0) + d.get('pub_M', 0) + d.get('priv_F', 0) + d.get('priv_M', 0)
        if tot > 0:
            print(f"  {cat}: privado F={d.get('priv_F',0)} M={d.get('priv_M',0)} | "
                  f"público F={d.get('pub_F',0)} M={d.get('pub_M',0)}")

    # Remuneração
    print("\nRemuneração mediana (principais categorias):")
    for cat in ['Enfermagem — técnicos e auxiliares', 'Enfermagem — enfermeiros', 'Medicina']:
        d = tab_remun.get(cat, {})
        mf = round(median(d['F']), 2) if d.get('F') else None
        mm = round(median(d['M']), 2) if d.get('M') else None
        if mf or mm:
            print(f"  {cat}: F R${mf} / M R${mm}")

    print("\n✓ Extração concluída.")

if __name__ == "__main__":
    main()
