"""Testes do analisador de padrões e da construção de Thompson."""

import pytest

from validafrete.afn import ErroSintaxe, construir_afn


@pytest.mark.parametrize(
    "padrao, aceitas, rejeitadas",
    [
        ("ab", ["ab"], ["", "a", "abb"]),
        ("a|b", ["a", "b"], ["", "ab"]),
        ("a*", ["", "a", "aaaa"], ["b"]),
        ("a+", ["a", "aaa"], [""]),
        ("a?b", ["b", "ab"], ["aab"]),
        ("a{3}", ["aaa"], ["aa", "aaaa"]),
        ("a{1,3}", ["a", "aa", "aaa"], ["", "aaaa"]),
        ("(ab|c)*d", ["d", "abd", "cabcd"], ["ab", "acd"]),
        ("[a-c0-9]x", ["ax", "7x"], ["dx", "x"]),
        (r"\.\$\(", [".$("], ["a$("]),
        ("(a*)*", ["", "aaa"], ["b"]),
    ],
)
def test_construcao_de_thompson(padrao, aceitas, rejeitadas):
    afn = construir_afn(padrao)
    for cadeia in aceitas:
        assert afn.aceita(cadeia), cadeia
    for cadeia in rejeitadas:
        assert not afn.aceita(cadeia), cadeia


@pytest.mark.parametrize(
    "padrao",
    [
        r"\d{3}",  # classe abreviada
        r"(a)\1",  # retroreferência (não regular)
        "(?=a)a",  # lookahead
        "a.b",  # ponto curinga
        "^ab$",  # âncoras
        "[^a]",  # classe negada
        "(ab",  # parêntese aberto
        "ab)",  # parêntese fechado sobrando
        "*a",  # quantificador sem operando
        "a{3,1}",  # repetição inválida
        "a*?",  # quantificador preguiçoso
    ],
)
def test_recursos_fora_do_subconjunto_regular_sao_rejeitados(padrao):
    with pytest.raises(ErroSintaxe):
        construir_afn(padrao)


def test_rastreamento_mostra_rejeicao_por_conjunto_vazio():
    afn = construir_afn("ab")
    passos = afn.rastrear("ax")
    assert passos[-1]["simbolo"] == "x"
    assert passos[-1]["estados"] == frozenset()


def test_dot_marca_inicial_final_e_movimentos_vazios():
    dot = construir_afn("a|b").para_dot()
    assert "inicio -> q0" in dot
    assert "doublecircle" in dot
    assert 'label="ε"' in dot
