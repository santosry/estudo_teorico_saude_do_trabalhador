# -*- coding: utf-8 -*-
"""
smartlab_completo.py
====================
Extrai TODOS os indicadores do SmartLab - Observatorio do Trabalho Decente
para Campos dos Goytacazes (3301009).

Dimensoes: oportunidade, rendimento, jornada, conciliacao,
           trabalhoabolido, estabilidade, igualdade,
           ambienteseguro, seguridadesocial, dialogosocial

Fonte: https://smartlab.mpt.mp.br/trabalhodecente/localidade/3301009
Metodo: Playwright (browser automation) - pagina renderizada no Chromium
"""
import os, re, csv, json, time
from playwright.sync_api import sync_playwright

MUN_COD = "3301009"
DIR_PROC = os.path.join("dados", "processados")
os.makedirs(DIR_PROC, exist_ok=True)

DIMENSOES = [
    ("oportunidade", "Oportunidades de Emprego"),
    ("rendimento", "Rendimentos e Trabalho Produtivo"),
    ("jornada", "Jornada de Trabalho Decente"),
    ("conciliacao", "Conciliacao Trabalho-Vida Pessoal"),
    ("trabalhoabolido", "Trabalho a ser Abolido"),
    ("estabilidade", "Estabilidade e Seguranca no Trabalho"),
    ("igualdade", "Igualdade de Oportunidades"),
    ("ambienteseguro", "Ambiente de Trabalho Seguro"),
    ("seguridadesocial", "Seguridade Social"),
    ("dialogosocial", "Dialogo Social"),
]

BASE_URL = "https://smartlab.mpt.mp.br/trabalhodecente/localidade"


def parse_indicadores(lines):
    """Parse lista de linhas de texto em indicadores (valor, nome, fonte)."""
    indicadores = []
    i = 0
    while i < len(lines):
        l = lines[i].strip()
        # Valor: numero, porcentagem, ou valor monetario
        if re.match(r"^[\d.,]+\s*(?:MIL|MILH|%|mil|BIL|bil|R\$|habitantes)?$", l, re.IGNORECASE):
            valor = l
            # Nome do indicador
            nome = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # Subtitle e fonte
            sub = ""
            fonte = ""
            if i + 2 < len(lines):
                l2 = lines[i + 2].strip()
                if l2.startswith("("):
                    fonte = l2
                else:
                    sub = l2
                    if i + 3 < len(lines) and lines[i + 3].strip().startswith("("):
                        fonte = lines[i + 3].strip()

            # Filtrar ruido: nome deve ter pelo menos 3 caracteres e nao ser so numero
            if len(nome) >= 3 and not re.match(r"^[\d.,\s]+$", nome):
                indicadores.append({
                    "valor": valor,
                    "indicador": f"{nome} {sub}".strip(),
                    "fonte": fonte,
                })
                i += 3 if fonte else 2
            else:
                i += 1
        else:
            i += 1
    return indicadores


def extrair_dimensao(page, dim_id, dim_nome):
    """Extrai indicadores de uma dimensao do SmartLab."""
    url = f"{BASE_URL}/{MUN_COD}?dimensao={dim_id}"
    print(f"  {dim_nome}...", end=" ", flush=True)

    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000)

    # Clicar nos dots de paginacao para carregar todos os cards
    for _ in range(10):
        try:
            dots = page.locator('[class*="dot"], .v-item--active, [role="tab"]').all()
            for dot in dots:
                try:
                    dot.click()
                    page.wait_for_timeout(800)
                except:
                    pass
        except:
            pass
        page.wait_for_timeout(500)

    # Extrair texto
    body = page.locator("body").inner_text()
    lines = [l.strip() for l in body.split("\n") if l.strip()]

    # Encontrar a secao da dimensao e pegar linhas ate a proxima dimensao
    dim_names_upper = [d[1].upper() for d in DIMENSOES]
    start_idx = None
    end_idx = None

    for i, l in enumerate(lines):
        ul = l.upper()
        if dim_nome.upper() in ul and start_idx is None:
            start_idx = i
        elif start_idx is not None and any(d in ul for d in dim_names_upper if d != dim_nome.upper()):
            end_idx = i
            break

    if start_idx is not None:
        section = lines[start_idx:end_idx] if end_idx else lines[start_idx:start_idx + 60]
    else:
        section = lines

    indicadores = parse_indicadores(section)
    print(f"{len(indicadores)} ind.")

    # Adicionar metadados
    for ind in indicadores:
        ind["dimensao"] = dim_nome
        ind["dimensao_id"] = dim_id

    return indicadores


def main():
    print("=" * 60)
    print("SMARTLAB - OBSERVATORIO DO TRABALHO DECENTE")
    print("Campos dos Goytacazes (3301009)")
    print("=" * 60)

    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors", "--disable-web-security"],
        )
        page = browser.new_page()
        page.set_default_timeout(15000)

        for dim_id, dim_nome in DIMENSOES:
            try:
                inds = extrair_dimensao(page, dim_id, dim_nome)
                todos.extend(inds)
            except Exception as e:
                print(f"    ERRO: {e}")

        browser.close()

    # Salvar
    if todos:
        # CSV
        path_csv = os.path.join(DIR_PROC, "smartlab_campos_indicadores.csv")
        cols = ["dimensao", "dimensao_id", "valor", "indicador", "fonte"]
        with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
            w.writeheader()
            w.writerows(todos)

        # JSON
        path_json = os.path.join(DIR_PROC, "smartlab_campos_indicadores.json")
        with open(path_json, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)

        print(f"\nCSV: {path_csv}")
        print(f"JSON: {path_json}")
        print(f"Total: {len(todos)} indicadores em {len(set(i['dimensao_id'] for i in todos))} dimensoes")

        # Resumo por dimensao
        from collections import Counter
        por_dim = Counter(i["dimensao_id"] for i in todos)
        for dim_id, dim_nome in DIMENSOES:
            n = por_dim.get(dim_id, 0)
            if n > 0:
                print(f"  {dim_nome}: {n} indicadores")
                for i in todos:
                    if i["dimensao_id"] == dim_id:
                        print(f"    {i['valor']:>10} | {i['indicador'][:60]} | {i['fonte'][:40]}")
            else:
                print(f"  {dim_nome}: 0 indicadores (dados nao encontrados ou secao vazia)")


if __name__ == "__main__":
    main()
