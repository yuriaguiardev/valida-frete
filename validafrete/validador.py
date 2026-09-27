"""Validação de valores isolados usando as Expressões Regulares.

A decisão de aceitar ou rejeitar é sempre tomada por ``re.fullmatch`` com o
padrão da ER. O AFNε equivalente é usado apenas para explicar ao usuário em
que ponto a cadeia foi rejeitada.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .afn import AFNe, construir_afn, rotulo_visivel
from .expressoes import EXPRESSOES, ExpressaoRegular, por_chave

TAMANHO_MAXIMO = 100


class ErroEntrada(ValueError):
    """Entrada que não pode ser processada (vazia, grande demais, tipo inválido)."""


@dataclass(frozen=True)
class Resultado:
    expressao: ExpressaoRegular
    cadeia: str
    aceita: bool
    mensagem: str


@lru_cache(maxsize=None)
def afn_de(chave: str) -> AFNe:
    """AFNε construído a partir do padrão da ER (calculado uma única vez)."""
    return construir_afn(por_chave(chave).padrao)


def _simbolo(c: str) -> str:
    return "␣" if c == " " else f"'{c}'"


def _exibir(cadeia: str) -> str:
    return "".join(rotulo_visivel(c) if c == " " else c for c in cadeia)


def diagnosticar(er: ExpressaoRegular, cadeia: str) -> str:
    """Explica, com base no AFNε, por que a cadeia foi rejeitada."""
    if cadeia == "":
        return "Entrada vazia (ε): a palavra vazia não pertence à linguagem desta ER."
    afn = afn_de(er.chave)
    estados = afn.inicio()
    for i, simbolo in enumerate(cadeia):
        if simbolo not in er.sigma:
            dica = " Verifique se há espaços sobrando no início ou no fim." if simbolo == " " else ""
            return (f"O símbolo {_simbolo(simbolo)} (posição {i + 1}) não pertence ao "
                    f"alfabeto Σ desta expressão.{dica}")
        proximos = afn.passo(estados, simbolo)
        if not proximos:
            lido = _exibir(cadeia[:i]) or "ε"
            return (f"Rejeitada na posição {i + 1}: depois de ler \"{lido}\", o AFNε não tem "
                    f"transição com o símbolo {_simbolo(simbolo)}.")
        estados = proximos
    return ("Cadeia incompleta: toda a entrada foi lida, mas o AFNε terminou apenas em "
            "estados não finais. Faltam símbolos para completar o formato.")


def _conferir_entrada(cadeia) -> str:
    if cadeia is None:
        raise ErroEntrada("Nenhum valor foi informado.")
    if not isinstance(cadeia, str):
        raise ErroEntrada("O valor informado precisa ser texto.")
    if len(cadeia) > TAMANHO_MAXIMO:
        raise ErroEntrada(f"Valor muito longo ({len(cadeia)} caracteres). "
                          f"O limite é de {TAMANHO_MAXIMO} caracteres.")
    return cadeia


def validar(chave: str, cadeia: str) -> Resultado:
    """Valida ``cadeia`` com a ER identificada por ``chave``."""
    try:
        er = por_chave(chave)
    except KeyError:
        raise ErroEntrada(f"Tipo de campo desconhecido: '{chave}'.") from None
    cadeia = _conferir_entrada(cadeia)
    if er.reconhece(cadeia):
        return Resultado(er, cadeia, True, f"Aceita: a cadeia pertence à linguagem de {er.codigo}.")
    return Resultado(er, cadeia, False, diagnosticar(er, cadeia))


def classificar(cadeia: str) -> list[Resultado]:
    """Testa a cadeia contra todas as ERs (identificação automática do tipo)."""
    cadeia = _conferir_entrada(cadeia)
    return [validar(er.chave, cadeia) for er in EXPRESSOES]
