"""Testes das cinco Expressões Regulares.

Verificam a regra central do trabalho: a ER do código, os casos de teste e o
AFNε precisam representar a mesma linguagem.
"""

import random
import re

import pytest

from validafrete.afn import construir_afn
from validafrete.casos_teste import CASOS
from validafrete.expressoes import EXPRESSOES

TODOS_OS_CASOS = [
    pytest.param(er, caso, id=f"{er.codigo}-{'aceita' if caso.aceita else 'rejeita'}-{caso.cadeia!r}")
    for er in EXPRESSOES
    for caso in CASOS[er.chave]
]


@pytest.mark.parametrize("er, caso", TODOS_OS_CASOS)
def test_regex_do_codigo(er, caso):
    assert (re.fullmatch(er.padrao, caso.cadeia) is not None) == caso.aceita


@pytest.mark.parametrize("er, caso", TODOS_OS_CASOS)
def test_afn_concorda_com_o_caso(er, caso):
    assert construir_afn(er.padrao).aceita(caso.cadeia) == caso.aceita


@pytest.mark.parametrize("er", EXPRESSOES, ids=lambda er: er.codigo)
def test_quantidade_minima_de_casos(er):
    casos = CASOS[er.chave]
    assert sum(c.aceita for c in casos) >= 6, "mínimo de 6 cadeias aceitas"
    assert sum(not c.aceita for c in casos) >= 6, "mínimo de 6 cadeias rejeitadas"
    assert any(c.limite for c in casos), "pelo menos um caso-limite"


@pytest.mark.parametrize("er", EXPRESSOES, ids=lambda er: er.codigo)
def test_alfabeto_documentado_igual_ao_do_afn(er):
    assert construir_afn(er.padrao).alfabeto == er.sigma


@pytest.mark.parametrize("er", EXPRESSOES, ids=lambda er: er.codigo)
def test_afn_equivale_a_regex_em_cadeias_aleatorias(er):
    """Compara AFNε e re.fullmatch em milhares de cadeias geradas.

    As cadeias são mutações dos casos de teste (trocas, inserções e remoções
    de símbolos) para explorar a fronteira da linguagem, onde erros aparecem.
    """
    afn = construir_afn(er.padrao)
    gerador = random.Random(2026)
    simbolos = sorted(er.sigma) + ["a", " ", "#"]
    bases = [c.cadeia for c in CASOS[er.chave]]
    for _ in range(3000):
        cadeia = list(gerador.choice(bases))
        for _ in range(gerador.randint(0, 3)):
            operacao = gerador.choice(("trocar", "inserir", "remover"))
            posicao = gerador.randint(0, max(len(cadeia) - 1, 0))
            if operacao == "trocar" and cadeia:
                cadeia[posicao] = gerador.choice(simbolos)
            elif operacao == "inserir":
                cadeia.insert(posicao, gerador.choice(simbolos))
            elif cadeia:
                del cadeia[posicao]
        texto = "".join(cadeia)
        assert afn.aceita(texto) == (re.fullmatch(er.padrao, texto) is not None), texto


def test_estrutura_do_afn():
    for er in EXPRESSOES:
        afn = construir_afn(er.padrao)
        assert afn.inicial == 0
        assert afn.inicial != afn.final
        # Em Thompson o final não tem transições de saída.
        assert all(t.origem != afn.final for t in afn.transicoes)
