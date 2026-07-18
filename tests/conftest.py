# -*- coding: utf-8 -*-
"""Configuração dos testes: raiz do projeto como cwd e carregador de módulos do pipeline."""
import os, sys, hashlib, importlib.util
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(scope="session", autouse=True)
def _cwd_raiz():
    os.chdir(RAIZ)

def carregar_modulo(nome_arquivo):
    """Importa um script do pipeline (nomes iniciam com dígito => importlib)."""
    path = os.path.join(RAIZ, "scripts", "pipeline", nome_arquivo)
    spec = importlib.util.spec_from_file_location(nome_arquivo.replace(".py", "_mod"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # módulos refatorados: execução pesada só em main()
    return mod

def sha256_arquivo(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

@pytest.fixture(scope="session")
def mod04():
    return carregar_modulo("04_dicionario_cbo_classificacao.py")

@pytest.fixture(scope="session")
def mod06():
    return carregar_modulo("06_validacao_independente.py")

@pytest.fixture(scope="session")
def base_processada():
    import pandas as pd
    return pd.read_csv(os.path.join(RAIZ, "dados", "processados",
                       "base_cat_campos_profissoes_saude_processada.csv"),
                       sep=";", dtype=str, encoding="utf-8-sig")

@pytest.fixture(scope="session")
def base_classificada():
    import pandas as pd
    return pd.read_csv(os.path.join(RAIZ, "dados", "processados", "base_cat_campos_classificada.csv"),
                       sep=";", dtype=str, encoding="utf-8-sig")
