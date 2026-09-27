"""Casos de teste de cada Expressão Regular.

Usados pelos testes automatizados (pytest), pela página "Testes" da aplicação
e pela documentação. Cada ER tem 8 cadeias aceitas e 8 rejeitadas; os
casos-limite estão marcados com ``limite=True``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Caso:
    cadeia: str
    aceita: bool
    descricao: str
    limite: bool = False


def _a(cadeia, descricao, limite=False):
    return Caso(cadeia, True, descricao, limite)


def _r(cadeia, descricao, limite=False):
    return Caso(cadeia, False, descricao, limite)


CASOS: dict[str, tuple[Caso, ...]] = {
    "cnpj": (
        _a("12.ABC.345/01DE-35", "Alfanumérico com máscara (exemplo oficial da Receita Federal)"),
        _a("12ABC34501DE35", "Alfanumérico sem máscara"),
        _a("11.222.333/0001-81", "Numérico tradicional com máscara"),
        _a("11222333000181", "Numérico tradicional sem máscara"),
        _a("A1.B2C.3D4/E5F6-07", "Letras e dígitos intercalados"),
        _a("AB.CDE.FGH/IJKL-12", "Raiz e ordem só com letras, com máscara"),
        _a("ZZZZZZZZZZZZ99", "Limite: maior símbolo de A em todas as 12 posições", limite=True),
        _a("00.000.000/0000-00", "Limite: formato válido, DV não conferido (falso positivo conhecido)", limite=True),
        _r("", "Limite: palavra vazia ε", limite=True),
        _r("12.abc.345/01de-35", "Letras minúsculas não pertencem a Σ"),
        _r("12.ABC.345/01DE-3A", "Dígito verificador com letra (deve estar em D)"),
        _r("12ABC345/01DE-35", "Máscara parcial (faltam os pontos)"),
        _r("12.ABC.345/01DE35", "Máscara sem o hífen"),
        _r("12ABC34501DE3", "Limite: 13 caracteres (um a menos)", limite=True),
        _r("12ABC34501DE356", "15 caracteres (um a mais)"),
        _r(" 11222333000181", "Espaço antes do valor"),
    ),
    "placa": (
        _a("ABC-1234", "Padrão antigo com hífen"),
        _a("ABC1234", "Padrão antigo sem hífen"),
        _a("BRA2E19", "Padrão Mercosul"),
        _a("RIO2A18", "Padrão Mercosul"),
        _a("QWE0Z00", "Mercosul com zeros"),
        _a("MNO-5678", "Padrão antigo com hífen"),
        _a("AAA-0000", "Limite: menores símbolos em todas as posições", limite=True),
        _a("ZZZ9Z99", "Limite: maiores símbolos em todas as posições (Mercosul)", limite=True),
        _r("", "Limite: palavra vazia ε", limite=True),
        _r("abc1d23", "Letras minúsculas"),
        _r("ABC-1D23", "Mercosul não admite hífen"),
        _r("AB-1234", "Apenas duas letras"),
        _r("ABC12345", "Cinco dígitos"),
        _r("ABC 1234", "Espaço no lugar do hífen"),
        _r("ABC1DE3", "Duas letras na parte final"),
        _r("ABC-123", "Limite: um dígito a menos", limite=True),
    ),
    "telefone": (
        _a("+55 (11) 91234-5678", "Celular completo com DDI, DDD entre parênteses e hífen"),
        _a("(21) 3456-7890", "Fixo com DDD entre parênteses"),
        _a("11912345678", "Celular apenas com dígitos"),
        _a("+5561987654321", "DDI e DDD sem separadores"),
        _a("(47)98888-0000", "Sem espaço após o DDD"),
        _a("85 3222-1100", "Fixo com DDD sem parênteses"),
        _a("+55 31 2345-6789", "DDI com DDD sem parênteses"),
        _a("(99) 90000-0000", "Limite: maior DDD existente", limite=True),
        _r("", "Limite: palavra vazia ε", limite=True),
        _r("(11 91234-5678", "Parênteses desbalanceados"),
        _r("(23) 91234-5678", "DDD 23 não existe"),
        _r("11 81234-5678", "Nove dígitos sem começar por 9"),
        _r("11 6123-4567", "Fixo começando por 6"),
        _r("+55  11 91234-5678", "Dois espaços seguidos"),
        _r("11 91234-567", "Limite: um dígito a menos", limite=True),
        _r("+1 (11) 91234-5678", "DDI diferente de +55"),
    ),
    "data": (
        _a("01/01/2000", "Primeiro dia do ano"),
        _a("15/08/2025", "Data comum"),
        _a("29/02/2024", "29 de fevereiro em ano bissexto"),
        _a("30/04/2026", "Dia 30 em mês de 30 dias"),
        _a("31/12/1999", "Dia 31 em mês de 31 dias"),
        _a("31/01/1900", "Limite: menor ano aceito", limite=True),
        _a("28/02/2099", "Limite: maior ano aceito", limite=True),
        _a("29/02/2023", "Limite: aceito pela linguagem, embora 2023 não seja bissexto", limite=True),
        _r("", "Limite: palavra vazia ε", limite=True),
        _r("31/04/2025", "Abril não tem dia 31"),
        _r("30/02/2024", "Fevereiro não tem dia 30"),
        _r("00/10/2020", "Dia zero"),
        _r("15/13/2020", "Mês 13"),
        _r("1/1/2020", "Dia e mês sem zero à esquerda"),
        _r("15/08/2100", "Limite: ano acima de 2099", limite=True),
        _r("15-08-2020", "Separador '-' em vez de '/'"),
    ),
    "valor": (
        _a("R$ 1.234,56", "Com separador de milhar"),
        _a("R$1500,00", "Sem espaço e sem separador"),
        _a("R$ 0,99", "Parte inteira zero"),
        _a("R$ 12.345.678,90", "Vários grupos de milhar"),
        _a("R$ 1000000,00", "Inteiro grande sem separador"),
        _a("R$ 7,00", "Um único dígito inteiro"),
        _a("R$ 0,00", "Limite: menor valor", limite=True),
        _a("R$ 999,99", "Limite: maior valor sem grupo de milhar", limite=True),
        _r("", "Limite: palavra vazia ε", limite=True),
        _r("R$ 01,50", "Zero à esquerda"),
        _r("R$ 1.23,45", "Grupo de milhar com dois dígitos"),
        _r("R$ 1234.567,00", "Mistura de formatos (com e sem separador)"),
        _r("R$ 10,5", "Limite: só um dígito de centavos", limite=True),
        _r("1.234,56", "Sem o prefixo R$"),
        _r("R$ 1,234.56", "Formato americano"),
        _r("R$ -10,00", "Valor negativo"),
    ),
}
