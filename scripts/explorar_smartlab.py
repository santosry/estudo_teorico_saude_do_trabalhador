# -*- coding: utf-8 -*-
"""Explora modulos do SmartLab com listener corrigido."""
import json, csv, os
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(RAIZ)
DIR_OUT = os.path.join("dados", "processados")
os.makedirs(DIR_OUT, exist_ok=True)

MUN_COD = "3301009"

MODULOS = [
    ("trabalhoinfantil", "Trabalho Infantil"),
    ("igualdade", "Igualdade no Trabalho"),
    ("inspecaodotrabalho", "Inspecao do Trabalho"),
    ("covid19", "COVID-19 e Trabalho"),
    ("liberdadesindical", "Liberdade Sindical"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])

    for mod_id, mod_nome in MODULOS:
        print(f"\n{'='*60}")
        print(f"MODULO: {mod_nome}")
        print(f"{'='*60}")

        page = browser.new_page()
        api_data = {}

        def capture_response(response):
            if "datahub" in response.url and response.status == 200:
                try:
                    body = response.json()
                    if isinstance(body, dict) and "dataset" in body:
                        key = response.url.split("?")[0].split("/")[-1]
                        if key not in ["municipios"]:  # skip the 5570-row municipality list
                            if key not in api_data:
                                api_data[key] = []
                            api_data[key].extend(body["dataset"])
                except:
                    pass

        page.on("response", capture_response)

        url = f"https://smartlab.mpt.mp.br/{mod_id}/localidade/{MUN_COD}"
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(8000)

            tem_campos = "Campos" in page.locator("body").inner_text()

            n_datasets = len(api_data)
            n_rows = sum(len(ds) for ds in api_data.values())

            print(f"  Status: {resp.status} | Campos: {tem_campos} | Datasets: {n_datasets} | Linhas: {n_rows}")

            if api_data:
                all_rows = []
                for endpoint, dataset in api_data.items():
                    for row in dataset:
                        row["_modulo"] = mod_id
                        row["_endpoint"] = endpoint
                        all_rows.append(row)

                for endpoint, dataset in list(api_data.items())[:3]:
                    print(f"    {endpoint}: {len(dataset)} rows")
                    if dataset:
                        print(f"    Ex: {json.dumps(dataset[0], ensure_ascii=False)[:150]}")

                if all_rows:
                    cols = sorted(set().union(*[set(r.keys()) for r in all_rows]))
                    path = os.path.join(DIR_OUT, f"smartlab_{mod_id}_campos.csv")
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
                        w.writeheader()
                        w.writerows(all_rows)
                    print(f"    CSV: {path} ({len(all_rows)} linhas)")
            else:
                # Check page text for any indicators
                body = page.locator("body").inner_text()
                lines = [l.strip() for l in body.split("\n") if l.strip()]
                # Look for numeric values that might be indicators
                import re
                indic = [(lines[i], lines[i+1]) for i in range(len(lines)-1)
                         if re.match(r'^[\d.,]+\s*(%|MIL|R\$)?$', lines[i]) and len(lines[i+1]) > 5]
                if indic:
                    print(f"    Indicadores no DOM: {len(indic)}")
                    for val, label in indic[:10]:
                        print(f"      {val:>12} | {label[:100]}")
                else:
                    print(f"    Sem indicadores (modulo sem dados municipais)")

        except Exception as e:
            print(f"  ERRO: {e}")

        page.close()

    browser.close()

print("\n[DONE]")
