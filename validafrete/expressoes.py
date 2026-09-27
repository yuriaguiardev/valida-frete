"""As cinco Expressões Regulares do ValidaFrete.

Cada ER é definida uma única vez neste módulo. O validador, a interface web,
os testes automatizados, os diagramas AFNε e a documentação leem daqui, o que
garante que todos representem a mesma linguagem.

Convenções da notação formal (campo ``formal``):
    - juxtaposição = concatenação; ``|`` = união; ``*`` = fecho de Kleene;
      ``r{m}`` = m cópias de r; ``r{m,n}`` = união de r^m, ..., r^n;
    - ε é a palavra vazia;
    - letras e dígitos são escritos diretamente; símbolos de pontuação
      aparecem entre aspas simples para não se confundirem com operadores;
    - ␣ representa o caractere espaço;
    - letras maiúsculas isoladas em itálico nos slides (D, P, M, A, F, K) são
      conjuntos/abreviações definidos no campo ``alfabeto``.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressaoRegular:
    codigo: str  # identificação (ER-01, ...)
    chave: str  # nome do campo/coluna no programa
    nome: str
    finalidade: str
    alfabeto: tuple[str, ...]  # definições dos conjuntos usados
    sigma: frozenset[str]  # Σ exato, conferido pelos testes contra o AFNε
    linguagem: str
    formal: str
    padrao: str  # sintaxe exatamente como é usada em re.fullmatch
    equivalencias: tuple[tuple[str, str], ...]  # (trecho da sintaxe, significado formal)
    limitacoes: tuple[str, ...]
    exemplo: str

    def reconhece(self, cadeia: str) -> bool:
        """Correspondência completa: a cadeia inteira deve pertencer a L."""
        return re.fullmatch(self.padrao, cadeia) is not None


_D = "D = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9} (dígitos)"
_P = "P = D − {0} = {1, 2, …, 9} (dígitos sem o zero)"
_M = "M = {A, B, C, …, Z} (26 letras maiúsculas, sem acento)"
_FULLMATCH = (
    "re.fullmatch",
    "Correspondência completa: equivale a ancorar o padrão no início (^) e no fim ($); "
    "a cadeia inteira precisa pertencer a L.",
)


CNPJ = ExpressaoRegular(
    codigo="ER-01",
    chave="cnpj",
    nome="CNPJ do cliente (alfanumérico ou numérico)",
    finalidade=(
        "Validar o CNPJ da empresa que contrata o frete. Aceita o novo CNPJ alfanumérico "
        "(IN RFB nº 2.229/2024, em uso desde julho de 2026) e o formato numérico tradicional, "
        "com a máscara XX.XXX.XXX/XXXX-DD ou sem máscara."
    ),
    alfabeto=(
        _D,
        _M,
        "A = M ∪ D (símbolos permitidos na raiz e na ordem do CNPJ)",
        "Σ = M ∪ D ∪ {'.', '/', '-'}",
    ),
    sigma=frozenset(string.ascii_uppercase + string.digits + "./-"),
    linguagem=(
        "Cadeias com 14 caracteres significativos: os 12 primeiros pertencem a A (letras "
        "maiúsculas ou dígitos) e os 2 últimos, os dígitos verificadores, pertencem a D. "
        "A cadeia é escrita sem máscara (14 símbolos seguidos) ou com a máscara completa "
        "AA.AAA.AAA/AAAA-DD; máscaras parciais não pertencem a L."
    ),
    formal="A{2} '.' A{3} '.' A{3} '/' A{4} '-' D{2}  |  A{12} D{2}",
    padrao=r"[A-Z0-9]{2}\.[A-Z0-9]{3}\.[A-Z0-9]{3}/[A-Z0-9]{4}-[0-9]{2}|[A-Z0-9]{12}[0-9]{2}",
    equivalencias=(
        ("[A-Z0-9]", "Classe finita: A = M ∪ D = (A | B | … | Z | 0 | 1 | … | 9)"),
        ("[0-9]", "Intervalo finito: D = (0 | 1 | … | 9)"),
        ("{2}, {3}, {4}, {12}", "Repetição exata: r{m} = r r … r (m cópias concatenadas)"),
        ("\\.", "Ponto literal '.' (o escape remove o significado de \"qualquer caractere\")"),
        ("/  e  -", "Símbolos literais '/' e '-' (fora de classes não são operadores)"),
        ("|", "União das duas formas: com máscara | sem máscara"),
        _FULLMATCH,
    ),
    limitacoes=(
        "Valida apenas o formato: os dígitos verificadores (cálculo módulo 11) não são "
        "conferidos. Assim, 00.000.000/0000-00 e 11.222.333/0001-00 são aceitos (falso positivo).",
        "Letras minúsculas são rejeitadas. O programa não converte a entrada para maiúsculas, "
        "para não alterar a linguagem reconhecida.",
        "Máscaras parciais (ex.: 12ABC345/01DE-35) são rejeitadas por decisão de projeto.",
    ),
    exemplo="12.ABC.345/01DE-35",
)


PLACA = ExpressaoRegular(
    codigo="ER-02",
    chave="placa",
    nome="Placa do veículo (padrão antigo ou Mercosul)",
    finalidade=(
        "Validar a placa do caminhão que fará a coleta. Aceita o padrão antigo brasileiro "
        "(LLL-NNNN, com hífen opcional) e o padrão Mercosul (LLLNLNN)."
    ),
    alfabeto=(_D, _M, "Σ = M ∪ D ∪ {'-'}"),
    sigma=frozenset(string.ascii_uppercase + string.digits + "-"),
    linguagem=(
        "Três letras maiúsculas seguidas de: (a) quatro dígitos, com ou sem um hífen entre "
        "as letras e os dígitos (padrão antigo); ou (b) dígito, letra e dois dígitos, sem "
        "hífen (padrão Mercosul)."
    ),
    formal="M{3} ( ('-' | ε) D{4}  |  D M D{2} )",
    padrao=r"[A-Z]{3}(-?[0-9]{4}|[0-9][A-Z][0-9]{2})",
    equivalencias=(
        ("[A-Z]", "Intervalo finito: M = (A | B | … | Z)"),
        ("[0-9]", "Intervalo finito: D = (0 | 1 | … | 9)"),
        ("{3}, {4}, {2}", "Repetição exata (concatenação de cópias)"),
        ("-?", "Opcionalidade: ('-' | ε)"),
        ("( … | … )", "Agrupamento da união entre padrão antigo e padrão Mercosul"),
        _FULLMATCH,
    ),
    limitacoes=(
        "Não consulta se a placa existe ou está registrada; apenas o formato é verificado.",
        "O padrão Mercosul com hífen (ABC-1D23) é rejeitado, pois a placa oficial não o possui.",
        "Letras minúsculas e espaços são rejeitados.",
    ),
    exemplo="BRA2E19",
)


TELEFONE = ExpressaoRegular(
    codigo="ER-03",
    chave="telefone",
    nome="Telefone do motorista (fixo ou celular, com DDD válido)",
    finalidade=(
        "Validar o telefone de contato do motorista. Exige um DDD realmente em uso no Brasil "
        "(67 códigos da Anatel), aceita o prefixo +55 e o DDD com ou sem parênteses — "
        "sempre balanceados — e distingue celular (9 + 8 dígitos) de fixo (2 a 5 + 7 dígitos)."
    ),
    alfabeto=(
        _D,
        _P,
        "F = {2, 3, 4, 5} (primeiro dígito de telefone fixo)",
        "K = 1P | 2(1|2|4|7|8) | 3(1|2|3|4|5|7|8) | 4P | 5(1|3|4|5) | 6P | 7(1|3|4|5|7|9) "
        "| 8P | 9P  (os 67 DDDs em uso)",
        "Σ = D ∪ {'+', '(', ')', '-', ␣}",
    ),
    sigma=frozenset(string.digits + "+()- "),
    linguagem=(
        "Números de telefone formados por: prefixo internacional +55 opcional (seguido ou não "
        "de espaço); DDD pertencente a K, entre parênteses ou sem eles; espaço opcional; "
        "número de celular (9 seguido de 8 dígitos) ou fixo (dígito de 2 a 5 seguido de 7 "
        "dígitos), com hífen opcional antes dos 4 últimos dígitos."
    ),
    formal=(
        "( '+' 55 (␣ | ε) | ε ) ( '(' K ')' | K ) (␣ | ε) ( 9 D{4} | F D{3} ) ('-' | ε) D{4}"
    ),
    padrao=(
        r"(\+55 ?)?(\((1[1-9]|2[12478]|3[1-578]|4[1-9]|5[1345]|6[1-9]|7[134579]|8[1-9]|9[1-9])\)"
        r"|(1[1-9]|2[12478]|3[1-578]|4[1-9]|5[1345]|6[1-9]|7[134579]|8[1-9]|9[1-9]))"
        r" ?(9[0-9]{4}|[2-5][0-9]{3})-?[0-9]{4}"
    ),
    equivalencias=(
        ("\\+  \\(  \\)", "Símbolos literais '+', '(' e ')' (escapados porque são operadores)"),
        ("(\\+55 ?)?", "Opcionalidade aninhada: ('+' 5 5 (␣ | ε) | ε)"),
        ("[1-9]", "Intervalo: P = (1 | 2 | … | 9)"),
        ("[12478], [1-578], [1345], [134579]", "Classes finitas: (1|2|4|7|8), (1|2|3|4|5|7|8), ..."),
        ("1[1-9]|2[12478]|…|9[1-9]", "União dos 67 DDDs válidos (abreviada por K na forma formal)"),
        ("\\(K\\)|K", "União que só aceita parênteses balanceados: o K aparece duas vezes, "
         "porque uma ER não tem memória para \"lembrar\" que abriu um parêntese"),
        ("[2-5]", "Intervalo: F = (2 | 3 | 4 | 5)"),
        (" ?  e  -?", "Opcionalidade: (␣ | ε) e ('-' | ε)"),
        _FULLMATCH,
    ),
    limitacoes=(
        "Não verifica se o número está ativo nem se o prefixo pertence a uma operadora.",
        "Aceita separadores em posições alternativas, como +5511912345678 ou (11)91234-5678, "
        "mas rejeita espaços duplos e hífens fora do lugar.",
        "Números 0800, 0300 e de serviços (190, 192) não pertencem à linguagem.",
    ),
    exemplo="+55 (11) 91234-5678",
)


DATA = ExpressaoRegular(
    codigo="ER-04",
    chave="data",
    nome="Data da coleta (DD/MM/AAAA com dia compatível com o mês)",
    finalidade=(
        "Validar a data agendada para a coleta. Além do formato, impede dias inexistentes "
        "como 31/04 ou 30/02, e restringe o ano ao intervalo 1900–2099."
    ),
    alfabeto=(_D, _P, "Σ = D ∪ {'/'}"),
    sigma=frozenset(string.digits + "/"),
    linguagem=(
        "Datas DD/MM/AAAA com ano entre 1900 e 2099 em que: os dias 01 a 29 ocorrem em "
        "qualquer mês; o dia 30 ocorre em todos os meses exceto fevereiro; e o dia 31 "
        "ocorre apenas em janeiro, março, maio, julho, agosto, outubro e dezembro."
    ),
    formal=(
        "( (0P | (1|2)D) '/' (0P | 1(0|1|2))  |  30 '/' (0(1|3|4|5|6|7|8|9) | 1(0|1|2))  "
        "|  31 '/' (0(1|3|5|7|8) | 1(0|2)) ) '/' (19 | 20) D{2}"
    ),
    padrao=r"((0[1-9]|[12][0-9])/(0[1-9]|1[0-2])|30/(0[13-9]|1[0-2])|31/(0[13578]|1[02]))/(19|20)[0-9]{2}",
    equivalencias=(
        ("0[1-9]|[12][0-9]", "Dias 01–29: (0P | (1|2)D)"),
        ("0[1-9]|1[0-2]", "Meses 01–12: (0P | 1(0|1|2))"),
        ("[13-9]", "Classe com intervalo: (1 | 3 | 4 | 5 | 6 | 7 | 8 | 9), ou seja, sem o 2 (fevereiro)"),
        ("[13578], [02]", "Classes finitas dos meses com 31 dias: (1|3|5|7|8) e (0|2)"),
        ("19|20", "União das duas possibilidades de século"),
        ("[0-9]{2}", "Repetição exata: D D"),
        _FULLMATCH,
    ),
    limitacoes=(
        "29/02 é aceito em qualquer ano (ex.: 29/02/2023, falso positivo). Como o intervalo de "
        "anos é finito, os bissextos até poderiam ser descritos por uma ER, mas ela ficaria "
        "enorme e ilegível; essa verificação fica para uma etapa posterior.",
        "Não verifica se a data é passada ou futura, nem aceita formatos como D/M/AAAA ou AAAA-MM-DD.",
    ),
    exemplo="15/10/2026",
)


VALOR = ExpressaoRegular(
    codigo="ER-05",
    chave="valor",
    nome="Valor do frete em reais (R$)",
    finalidade=(
        "Validar o valor cobrado pelo frete no padrão monetário brasileiro: prefixo R$, "
        "parte inteira sem zeros à esquerda, separador de milhar opcional (mas consistente) "
        "e exatamente dois centavos após a vírgula."
    ),
    alfabeto=(_D, _P, "Σ = D ∪ {R, '$', ␣, '.', ','}"),
    sigma=frozenset(string.digits + "R$ .,"),
    linguagem=(
        "Cadeias iniciadas por R$, com espaço opcional, seguidas da parte inteira — 0, ou um "
        "número sem zero à esquerda escrito inteiramente com separadores de milhar '.' em "
        "grupos de três dígitos, ou inteiramente sem separadores — e, por fim, vírgula e "
        "dois dígitos de centavos."
    ),
    formal="R '$' (␣ | ε) ( 0  |  P D{0,2} ('.' D{3})*  |  P D* ) ',' D{2}",
    padrao=r"R\$ ?(0|[1-9][0-9]{0,2}(\.[0-9]{3})*|[1-9][0-9]*),[0-9]{2}",
    equivalencias=(
        ("R\\$", "Símbolos literais R e '$' ($ é escapado porque é âncora de fim no motor)"),
        (" ?", "Opcionalidade do espaço: (␣ | ε)"),
        ("[1-9][0-9]{0,2}", "Repetição limitada: P D{0,2} = P (ε | D | DD)"),
        ("(\\.[0-9]{3})*", "Fecho de Kleene: zero ou mais grupos de milhar '.' D D D"),
        ("[1-9][0-9]*", "Fecho de Kleene: P D* (inteiro sem separadores)"),
        (",[0-9]{2}", "Vírgula literal seguida de exatamente dois dígitos"),
        _FULLMATCH,
    ),
    limitacoes=(
        "Não há valor máximo: qualquer quantidade de grupos de milhar é aceita.",
        "R$ 0,00 é aceito (frete cortesia); valores negativos e o formato americano "
        "(R$ 1,234.56) são rejeitados.",
        "Não aceita o símbolo sem o prefixo (1.234,56) nem 'R $' com espaço entre R e $.",
    ),
    exemplo="R$ 1.250,00",
)


EXPRESSOES: tuple[ExpressaoRegular, ...] = (CNPJ, PLACA, TELEFONE, DATA, VALOR)
_POR_CHAVE = {er.chave: er for er in EXPRESSOES}


def por_chave(chave: str) -> ExpressaoRegular:
    """Busca a ER pelo nome do campo (levanta KeyError se não existir)."""
    return _POR_CHAVE[chave]
