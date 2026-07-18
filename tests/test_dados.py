# -*- coding: utf-8 -*-
"""Testes de integridade dos DADOS reais versionados (nenhum dado sintético)."""
import csv, json, os, datetime
import pandas as pd
import pytest
from conftest import sha256_arquivo, RAIZ


def _manifesto():
    with open("dados/manifesto/manifesto_arquivos.csv", encoding="utf-8-sig") as f:
        return {r["caminho_relativo"]: r for r in csv.DictReader(f, delimiter=";")}


def test_manifesto_hashes_dos_arquivos_versionados():
    """Hashes SHA-256 do manifesto conferem com os arquivos SIDRA presentes no repositório."""
    man = _manifesto()
    conferidos = 0
    for rel, r in man.items():
        if "sidra-campos" in rel and rel.endswith(".csv") and os.path.exists(rel):
            assert sha256_arquivo(rel) == r["sha256"], f"hash divergente: {rel}"
            conferidos += 1
    assert conferidos >= 10


def test_filtro_municipal_integro(base_processada):
    b = base_processada
    assert (b["municipio_empregador_codigo"] == "330100").all()
    assert (b["uf_municipio_empregador"] == "Rio de Janeiro").all()
    nomes = b["municipio_empregador_nome"].str.lower()
    for proibido in ("jordão", "novos", "júlio", "bernardo", "josé dos campos", "mário"):
        assert not nomes.str.contains(proibido).any(), f"homônimo indevido: {proibido}"


def test_controle_homonimos_excluidos():
    with open("dados/processados/controle_localidades_campo.csv", encoding="utf-8-sig") as f:
        nomes = [r["municipio_empregador_bruto"] for r in csv.DictReader(f, delimiter=";")]
    txt = " | ".join(nomes)
    # os homônimos existem na fonte (e portanto foram vistos e excluídos pelo filtro)
    for esperado in ("Campos Novos", "Campos do Jor", "Campos de Júl", "São José dos Campos", "Mário Campos"):
        assert esperado in txt, f"controle deveria listar {esperado}"


def test_periodo_e_derivacao_de_datas(base_processada):
    b = base_processada
    d = pd.to_datetime(b["data_acidente"], format="%Y-%m-%d", errors="raise")
    assert d.min() >= pd.Timestamp("2018-01-01") and d.max() <= pd.Timestamp("2025-12-31")
    assert (b["ano_acidente"].astype(int) == d.dt.year).all()
    assert (b["mes_acidente"] == d.dt.strftime("%Y-%m")).all()


def test_deduplicacao_entre_arquivos(base_classificada):
    """Após a deduplicação, um mesmo hash de linha bruta só pode ocorrer em UM arquivo."""
    g = base_classificada.groupby("hash_registro")["arquivo_origem"].nunique()
    assert (g == 1).all()


def test_universos_somam_base_municipal(base_classificada):
    c = base_classificada["universo"].value_counts().to_dict()
    assert c == {"apoio_ou_outra": 3712, "principal": 1144,
                 "nao_classificado": 184, "multiprofissional": 26}
    assert len(base_classificada) == 5066


def test_idades_validas(base_processada):
    idades = pd.to_numeric(base_processada["idade"], errors="coerce").dropna()
    assert idades.between(14, 100).all()


def test_dominio_sexo_tipo(base_processada):
    s = base_processada[base_processada["universo"] == "principal"]
    assert set(s["sexo"].dropna().unique()) <= {"Feminino", "Masculino"}
    assert set(s["tipo_acidente"].dropna().unique()) <= {"Típico", "Trajeto", "Doença"}


def test_validacao_independente_convergente():
    j = json.load(open("logs/validacao_independente.json", encoding="utf-8"))
    assert "CONVERGENTE" in j["RESULTADO"]
    assert j["V4_saude_principal"]["validacao"] == j["V4_saude_principal"]["pipeline"] == 1144


def test_fluxo_selecao_consistente():
    t19 = pd.read_csv("saidas/tabelas/T19_fluxo_selecao.csv", sep=";", encoding="utf-8-sig")
    n = dict(zip(t19["etapa"], t19["n"]))
    base = [v for k, v in n.items() if k.startswith("Base Campos")][0]
    partes = sum(v for k, v in n.items() if k.startswith("→"))
    assert base == partes == 5066
