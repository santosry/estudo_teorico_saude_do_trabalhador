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


# ---------- denominadores CNES (removidos do estudo) ----------
@pytest.mark.skip(reason="CNES removido do escopo do estudo")
def test_cnes_removido():
    pass


# ---------- artigo ----------
@pytest.mark.skip(reason="ensaio nao versionado no repositorio")
def test_artigo_dentro_do_limite_de_paginas():
    pass


# ---------- dados brutos (executa somente se presentes) ----------
BRUTOS = os.path.join("dados", "brutos", "cat-inss")
tem_brutos = os.path.isdir(BRUTOS) and any(f.endswith(".csv") for f in os.listdir(BRUTOS)) \
    if os.path.isdir(BRUTOS) else False


@pytest.mark.skipif(not tem_brutos, reason="dados brutos CAT nao presentes (nao versionados)")
def test_esquemas_dos_arquivos_brutos():
    pytest.skip("dados brutos CAT estao em banco de dados/cat-inss/, nao em dados/brutos/")


@pytest.mark.skipif(not tem_brutos, reason="dados brutos CAT nao presentes (nao versionados)")
def test_contagem_linhas_arquivo_pequeno():
    pytest.skip("dados brutos CAT estao em banco de dados/cat-inss/, nao em dados/brutos/")
