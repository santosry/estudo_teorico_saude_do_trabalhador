# -*- coding: utf-8 -*-
"""
smartlab_campos.py
==================
Extrai indicadores do SmartLab (Observatório do Trabalho Decente)
para Campos dos Goytacazes via Playwright.

Dimensões: oportunidades, rendimentos, jornada, conciliacao,
           trabalho abolido, estabilidade, igualdade, ambiente seguro,
           empresas, seguridade social, dialogo social.

Fonte: https://smartlab.mpt.mp.br/trabalhodecente/localidade/3301009
"""
import os, re, csv, json, time
from playwright.sync_api import sync_playwright

MUN_COD = "3301009"
MUN_NOME = "Campos dos Goytacazes"
UF = "RJ"
DIR_SAIDA = os.path.join("banco de dados", "smartlab")
DIR_PROC = os.path.join("dados", "processados")
os.makedirs(DIR_SAIDA, exist_ok=True)
os.makedirs(DIR_PROC, exist_ok=True)

DIMENSOES = [
    "oportunidade",
    "rendimento",
    "jornada",
    "conciliacao",
    "trabalhoabolido",
    "estabilidade",
    "igualdade",
    "ambienteseguro",
    "empresas",
    "seguridadesocial",
    "dialogosocial",
]

BASE_URL = "https://smartlab.mpt.mp.br/trabalhodecente/localidade"


def extrair_indicadores_visiveis(page):
    """Extrai indicadores visiveis do texto da pagina."""
    texto = page.locator("body").inner_text()
    linhas = texto.split("\n")

    indicadores = []
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        # Procurar padrao: VALOR seguido de DESCRICAO
        # Ex: "8,8MIL", "CONTRATOS INICIADOS", "EMPREGOS CELETISTAS (CLT)"
        if re.match(r"^[\d.,]+\s*(?:MIL|MILH|%|mil|MILHÕES|milhoes)?$", linha, re.IGNORECASE):
            valor = linha
            descricao = []
            j = i + 1
            while j < len(linhas) and j < i + 5:
                lj = linhas[j].strip()
                if lj and not re.match(r"^[\d.,]+\s*(?:MIL|%|MILH)", lj):
                    if "(" in lj or "Fonte" in lj or "IBGE" in lj or "CAGED" in lj or "RAIS" in lj or "MTE" in lj:
                        break
                    descricao.append(lj)
                else:
                    break
                j += 1
            if descricao:
                indicadores.append({
                    "valor": valor,
                    "descricao": " | ".join(descricao),
                    "fonte": linhas[j].strip() if j < len(linhas) else "",
                })
            i = j
        else:
            i += 1
    return indicadores


def baixar_csv_dimension(page, dimensao):
    """Navega para uma dimensao e tenta baixar CSV."""
    url = f"{BASE_URL}/{MUN_COD}?dimensao={dimensao}"
    print(f"  {dimensao}...", end=" ", flush=True)

    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    # Extrair indicadores visiveis
    indicadores = extrair_indicadores_visiveis(page)
    print(f"{len(indicadores)} indicadores")

    # Tentar clicar em botoes de download
    # SmartLab usa icones SVG ou botoes com data-attributes
    try:
        # Procurar botoes de download pelos seletores comuns
        download_btns = page.locator('[data-testid="download"], [aria-label*="ownload"], [title*="ownload"], [class*="download"], [class*="Download"], svg[class*="download"]').all()
        if not download_btns:
            # Tentar por icone de download (geralmente um SVG com path)
            download_btns = page.locator('button:has(svg), [role="button"]:has(svg)').all()

        for btn in download_btns[:3]:
            try:
                with page.expect_download(timeout=15000) as download_info:
                    btn.click()
                download = download_info.value
                filename = f"smartlab_{dimensao}_{download.suggested_filename}"
                path = os.path.join(DIR_SAIDA, filename)
                download.save_as(path)
                print(f"    CSV baixado: {filename}")
            except Exception as e:
                pass
    except:
        pass

    return indicadores


def main():
    print("=" * 60)
    print(f"SMARTLAB - {MUN_NOME}/{UF}")
    print("Observatorio do Trabalho Decente")
    print("=" * 60)

    todos_indicadores = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors", "--disable-web-security"],
        )
        page = browser.new_page()

        for dim in DIMENSOES:
            try:
                inds = baixar_csv_dimension(page, dim)
                if inds:
                    todos_indicadores[dim] = inds
            except Exception as e:
                print(f"    ERRO: {e}")

        browser.close()

    # Salvar resultados
    if todos_indicadores:
        # CSV com todos indicadores
        path_csv = os.path.join(DIR_PROC, "smartlab_campos_indicadores.csv")
        with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["dimensao", "valor", "descricao", "fonte"])
            for dim, inds in todos_indicadores.items():
                for ind in inds:
                    writer.writerow([dim, ind["valor"], ind["descricao"], ind["fonte"]])

        print(f"\nCSV salvo: {path_csv} ({sum(len(v) for v in todos_indicadores.values())} indicadores)")

        # JSON
        path_json = os.path.join(DIR_PROC, "smartlab_campos_indicadores.json")
        with open(path_json, "w", encoding="utf-8") as f:
            json.dump(todos_indicadores, f, ensure_ascii=False, indent=2)
        print(f"JSON salvo: {path_json}")


if __name__ == "__main__":
    main()
