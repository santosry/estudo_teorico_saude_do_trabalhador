"""Extrai dados SST do SmartLab via DOM scraping da página renderizada."""
import json, csv, os, re
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)
DIR_OUT = os.path.join("dados", "processados")
os.makedirs(DIR_OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
    page = browser.new_page()

    print("Acessando SmartLab SST...")
    page.goto("https://smartlab.mpt.mp.br/sst", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(8000)

    # Clicar no botão de selecionar município e digitar Campos
    print("Selecionando Campos dos Goytacazes...")
    try:
        # Clicar no seletor de localidade
        page.locator('text=Brasil').first.click(timeout=5000)
        page.wait_for_timeout(2000)
        # Digitar Campos
        page.locator('input[type="text"]').first.fill("Campos dos Goytacazes")
        page.wait_for_timeout(2000)
        # Selecionar primeira opção
        page.locator('text=Campos dos Goytacazes').first.click(timeout=5000)
        page.wait_for_timeout(8000)
    except Exception as e:
        print(f"  Não foi possível selecionar Campos: {e}")

    # Extrair todo texto visível
    body = page.locator("body").inner_text()
    lines = [l.strip() for l in body.split("\n") if l.strip()]

    print(f"\nTotal de linhas extraídas: {len(lines)}")

    # Salvar raw
    with open(os.path.join(DIR_OUT, "smartlab_sst_campos_raw.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Parse estruturado: extrair números + labels
    resultados = []
    i = 0
    while i < len(lines):
        l = lines[i]
        # Valor numérico (possivelmente com %, MIL, etc.)
        match = re.match(r'^([\d.,]+\s*(?:%|MIL|MILH|mil|BIL|R\$|habitantes)?)$', l)
        if match and i + 1 < len(lines):
            valor = match.group(1)
            nome = lines[i + 1]
            fonte = ""
            if i + 2 < len(lines) and lines[i + 2].startswith("("):
                fonte = lines[i + 2]
            if len(nome) > 3 and not re.match(r'^[\d.,\s]+$', nome):
                resultados.append({"valor": valor, "indicador": nome, "fonte": fonte})
            i += 1
        i += 1

    if resultados:
        path_csv = os.path.join(DIR_OUT, "smartlab_sst_campos.csv")
        with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["valor", "indicador", "fonte"], delimiter=";")
            w.writeheader()
            w.writerows(resultados)
        print(f"\nCSV: {path_csv}")
        print(f"Indicadores extraídos: {len(resultados)}")
        for r in resultados[:20]:
            print(f"  {r['valor']:>10} | {r['indicador'][:80]}")
    else:
        print("Nenhum indicador extraído.")

    browser.close()
