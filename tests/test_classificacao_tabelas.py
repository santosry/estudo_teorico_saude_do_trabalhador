# -*- coding: utf-8 -*-
"""Testes da classificação CBO, das tabelas publicadas, dos denominadores CNES e do artigo."""
import csv, json, os
import pandas as pd
import pytest
from conftest import RAIZ


# ---------- classificação CBO (regras do script 04) ----------
CASOS = [
    ("322205", "principal", "Enfermagem – técnicos e auxiliares"),
    ("322230", "principal", "Enfermagem – técnicos e auxiliares"),
    ("223505", "principal", "Enfermagem – enfermeiros"),
    ("225125", "principal", "Medicina"),
    ("223115", "principal", "Medicina"),                    # família 2231 (versão anterior da CBO)
    ("223605", "principal", "Fisioterapia"),
    ("322225", "principal", "Instrumentação cirúrgica"),
    ("515105", "principal", "Agentes comunitários de saúde e afins"),
    ("515215", "principal", "Diagnóstico e laboratório – técnicos e auxiliares"),
    ("515210", "principal", "Farmácia – técnicos e auxiliares"),
    ("519305", "apoio_ou_outra", "Serviços veterinários (apoio)"),   # 'enfermeiro veterinário' na fonte
    ("515225", "apoio_ou_outra", "Produção industrial farmacêutica"),
    ("251510", "multiprofissional", "Psicologia"),
    ("221105", "multiprofissional", "Biologia"),
    ("221205", "principal", "Biomedicina"),
    ("", "nao_classificado", "CBO não classificado"),
    ("513220", "apoio_ou_outra", "Outras ocupações (fora do campo da saúde)"),  # cozinheiro de hospital
]


@pytest.mark.parametrize("cbo,universo,categoria", CASOS)
def test_regras_classificacao(mod04, cbo, universo, categoria):
    u, cat, _, _ = mod04.classifica(cbo)
    assert (u, cat) == (universo, categoria)


def test_classificacao_consistente_com_base(mod04, base_processada):
    amostra = base_processada.sample(n=300, random_state=42)   # semente fixa
    for _, r in amostra.iterrows():
        cbo = "" if pd.isna(r["cbo_codigo"]) else str(r["cbo_codigo"])
        u, cat, _, _ = mod04.classifica(cbo)
        assert u == r["universo"] and cat == r["categoria_profissional"], r["id_linha"]


def test_rotina_independente_concorda(mod06, base_processada):
    s = base_processada[base_processada["universo"] == "principal"]
    for _, r in s.sample(n=200, random_state=7).iterrows():
        assert mod06.eh_principal(str(r["cbo_codigo"]))
        assert mod06.categoria(str(r["cbo_codigo"])) == r["categoria_profissional"]


# ---------- tabelas publicadas ----------
def test_t01_total_igual_base(base_classificada):
    t01 = pd.read_csv("saidas/tabelas/T01_cat_por_ano_universo.csv", sep=";", encoding="utf-8-sig")
    assert int(t01["total"].sum()) == len(base_classificada) == 5066


def test_t03_categorias_somam_universo(base_processada):
    t03 = pd.read_csv("saidas/tabelas/T03_categorias_saude.csv", sep=";", encoding="utf-8-sig")
    assert int(t03["n"].sum()) == 1144
    assert int(t03.loc[t03["categoria_profissional"] == "Enfermagem – técnicos e auxiliares", "n"].iloc[0]) == 803


def test_supressao_celulas_pequenas():
    t = pd.read_csv("saidas/tabelas/T04b_ranking_cbo_publicavel.csv", sep=";", encoding="utf-8-sig")
    individuais = t[t["cbo_codigo"] != "(agregado)"]
    assert (individuais["n"].astype(int) >= 5).all()


# ---------- denominadores CNES (dados reais baixados; T21/T22) ----------
def test_t21_denominadores_estrutura():
    t21 = pd.read_csv("saidas/tabelas/T21_denominadores_cnes.csv", sep=";", encoding="utf-8-sig")
    assert [c for c in t21.columns[1:]] == [str(a) for a in range(2018, 2026)]
    enf = t21.loc[t21["categoria_estudo"] == "Enfermagem – enfermeiros"].iloc[0]
    assert int(enf["2018"]) == 783        # regressão contra o valor verificado no TabNet
    assert (t21[[str(a) for a in range(2018, 2026)]].astype(int) >= 0).all().all()


def test_t22_razoes_recalculam():
    t22 = pd.read_csv("saidas/tabelas/T22_razao_cat_1000_cnes.csv", sep=";", encoding="utf-8-sig")
    for _, r in t22.iterrows():
        num, den = int(r["cat_n"]), int(r["cnes_dez_n"])
        if str(r["razao_por_1000"]).startswith("supresso"):
            assert num < 5 or den < 30
        else:
            assert float(r["razao_por_1000"]) == round(1000 * num / den, 1)
        assert "NÃO é incidência" in r["advertencia"]


def test_proveniencia_cnes():
    j = json.load(open("logs/log_10_denominadores.json", encoding="utf-8"))
    assert j["verificacoes"]["2019"]["consistente"] is True
    assert "330100 CAMPOS DOS GOYTACAZES" in j["verificacoes"]["controle_2018"]
    # brutos preservados
    assert os.path.exists("dados/brutos/cnes-rh/cnes_rh_campos_201812_ocupacoes.prn")


# ---------- artigo ----------
def test_artigo_dentro_do_limite_de_paginas():
    if not os.path.exists("documentos/artigo.pdf"):
        pytest.skip("PDF de verificação ausente (LibreOffice indisponível)")
    from pypdf import PdfReader
    assert len(PdfReader("documentos/artigo.pdf").pages) <= 5


# ---------- dados brutos (executa somente se presentes) ----------
BRUTOS = os.path.join("dados", "brutos", "cat-inss")
tem_brutos = os.path.isdir(BRUTOS) and any(f.endswith(".csv") for f in os.listdir(BRUTOS)) \
    if os.path.isdir(BRUTOS) else False


@pytest.mark.skipif(not tem_brutos, reason="dados brutos CAT não presentes (não versionados)")
def test_esquemas_dos_arquivos_brutos(mod06):
    esq = json.load(open("logs/esquemas_por_arquivo.json", encoding="utf-8"))
    assert len(esq) == 58
    for nome, meta in esq.items():
        path = os.path.join(BRUTOS, nome)
        with open(path, encoding=mod06.enc_de(path), errors="replace") as f:
            header = f.readline().rstrip("\r\n").split(";")
        assert len(header) == meta["n_colunas"] and len(header) in (24, 25, 27), nome


@pytest.mark.skipif(not tem_brutos, reason="dados brutos CAT não presentes (não versionados)")
def test_contagem_linhas_arquivo_pequeno():
    est = pd.read_csv("dados/processados/estatisticas_por_arquivo.csv", sep=";", encoding="utf-8-sig")
    alvo = est.loc[est["arquivo"] == "D.SDA.PDA.005.CAT.202512.csv", "linhas_dados"].iloc[0]
    with open(os.path.join(BRUTOS, "D.SDA.PDA.005.CAT.202512.csv"), "rb") as f:
        n = sum(1 for _ in f) - 1
    assert int(alvo) == n == 126
