"""Construção e simulação de AFNε a partir da sintaxe das Expressões Regulares.

O módulo lê o padrão exatamente como está escrito no código (o mesmo texto
passado para ``re.fullmatch``), monta a árvore sintática e aplica a
construção de Thompson. Assim, o autômato desenhado nos diagramas é derivado
do próprio padrão implementado, e não de uma cópia manual.

Subconjunto aceito (o mesmo da notação formal estudada):
    literal  a        escape  \\. \\$ \\+ \\( \\)     classe  [A-Z0-9]
    grupo    (r)      união   r|s                     concatenação  rs
    fechos   r*  r+  r?  r{m}  r{m,n}

Recursos que não pertencem às ERs formais (\\d, \\w, ponto curinga, âncoras,
retroreferências, lookaround, classes negadas) são rejeitados com erro.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Árvore sintática
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Simbolo:
    """Um símbolo do alfabeto ou uma classe finita de símbolos ([abc])."""

    simbolos: frozenset[str]
    rotulo: str


@dataclass(frozen=True)
class Vazio:
    """A palavra vazia ε."""


@dataclass(frozen=True)
class Concatenacao:
    partes: tuple


@dataclass(frozen=True)
class Uniao:
    opcoes: tuple


@dataclass(frozen=True)
class Repeticao:
    """r{minimo,maximo}; maximo=None representa repetição ilimitada.

    r* = r{0,}   r+ = r{1,}   r? = r{0,1}
    """

    corpo: object
    minimo: int
    maximo: int | None


class ErroSintaxe(ValueError):
    """Padrão fora do subconjunto regular suportado."""


# Caracteres que podem aparecer escapados com '\' e viram literais.
_ESCAPAVEIS = set(".$+()[]{}*?|^/-\\ ,")


class _Analisador:
    """Analisador descendente recursivo.

    uniao      -> concat ('|' concat)*
    concat     -> quantif*
    quantif    -> atomo ('*' | '+' | '?' | '{m}' | '{m,n}')?
    atomo      -> literal | escape | classe | '(' uniao ')'
    """

    def __init__(self, padrao: str):
        self.padrao = padrao
        self.pos = 0

    def analisar(self):
        no = self._uniao()
        if self.pos != len(self.padrao):
            raise ErroSintaxe(f"')' sem '(' correspondente na posição {self.pos}")
        return no

    def _atual(self):
        return self.padrao[self.pos] if self.pos < len(self.padrao) else None

    def _uniao(self):
        opcoes = [self._concat()]
        while self._atual() == "|":
            self.pos += 1
            opcoes.append(self._concat())
        return opcoes[0] if len(opcoes) == 1 else Uniao(tuple(opcoes))

    def _concat(self):
        partes = []
        while self._atual() not in (None, "|", ")"):
            partes.append(self._quantificado())
        if not partes:
            return Vazio()
        return partes[0] if len(partes) == 1 else Concatenacao(tuple(partes))

    def _quantificado(self):
        base = self._atomo()
        c = self._atual()
        if c == "*":
            minimo, maximo = 0, None
            self.pos += 1
        elif c == "+":
            minimo, maximo = 1, None
            self.pos += 1
        elif c == "?":
            minimo, maximo = 0, 1
            self.pos += 1
        elif c == "{":
            minimo, maximo = self._chaves()
        else:
            return base
        if self._atual() in ("*", "+", "?", "{"):
            raise ErroSintaxe(
                f"quantificador duplo/preguiçoso na posição {self.pos} não é suportado"
            )
        return Repeticao(base, minimo, maximo)

    def _chaves(self):
        fim = self.padrao.find("}", self.pos)
        if fim == -1:
            raise ErroSintaxe(f"'{{' sem '}}' na posição {self.pos}")
        conteudo = self.padrao[self.pos + 1 : fim]
        partes = conteudo.split(",")
        if len(partes) > 2 or not all(p.isdigit() for p in partes):
            raise ErroSintaxe(f"repetição '{{{conteudo}}}' inválida")
        minimo = int(partes[0])
        maximo = int(partes[-1])
        if maximo < minimo:
            raise ErroSintaxe(f"repetição '{{{conteudo}}}' com máximo menor que mínimo")
        self.pos = fim + 1
        return minimo, maximo

    def _atomo(self):
        c = self._atual()
        if c == "(":
            self.pos += 1
            if self._atual() == "?":
                raise ErroSintaxe("grupos especiais '(?...)' (lookaround etc.) não são suportados")
            no = self._uniao()
            if self._atual() != ")":
                raise ErroSintaxe("'(' sem ')' correspondente")
            self.pos += 1
            return no
        if c == "[":
            return self._classe()
        if c == "\\":
            literal = self._escape()
            return Simbolo(frozenset(literal), literal)
        if c in ("*", "+", "?", "{"):
            raise ErroSintaxe(f"quantificador sem operando na posição {self.pos}")
        if c in (".", "^", "$"):
            raise ErroSintaxe(
                f"metacaractere '{c}' não suportado; use '\\{c}' para o símbolo literal"
            )
        self.pos += 1
        return Simbolo(frozenset(c), c)

    def _escape(self):
        self.pos += 1
        c = self._atual()
        if c is None:
            raise ErroSintaxe("'\\' no final do padrão")
        if c.isdigit():
            raise ErroSintaxe("retroreferências (\\1, \\2, ...) não são regulares")
        if c not in _ESCAPAVEIS:
            raise ErroSintaxe(f"classe abreviada '\\{c}' não suportada; expanda-a com [...]")
        self.pos += 1
        return c

    def _classe(self):
        inicio = self.pos
        self.pos += 1
        if self._atual() == "^":
            raise ErroSintaxe("classes negadas [^...] dependem do universo de caracteres")
        simbolos: set[str] = set()
        while self._atual() != "]":
            if self._atual() is None:
                raise ErroSintaxe("'[' sem ']' correspondente")
            a = self._escape() if self._atual() == "\\" else self._consumir()
            if self._atual() == "-" and self.pos + 1 < len(self.padrao) and self.padrao[self.pos + 1] != "]":
                self.pos += 1
                b = self._escape() if self._atual() == "\\" else self._consumir()
                if ord(b) < ord(a):
                    raise ErroSintaxe(f"intervalo invertido '{a}-{b}'")
                simbolos.update(chr(x) for x in range(ord(a), ord(b) + 1))
            else:
                simbolos.add(a)
        self.pos += 1
        if not simbolos:
            raise ErroSintaxe("classe vazia '[]'")
        return Simbolo(frozenset(simbolos), self.padrao[inicio : self.pos])

    def _consumir(self):
        c = self.padrao[self.pos]
        self.pos += 1
        return c


def analisar(padrao: str):
    """Converte o padrão em árvore sintática (levanta ErroSintaxe)."""
    return _Analisador(padrao).analisar()


# ---------------------------------------------------------------------------
# AFNε
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transicao:
    origem: int
    destino: int
    simbolos: frozenset[str] | None  # None representa um movimento ε
    rotulo: str

    @property
    def vazia(self) -> bool:
        return self.simbolos is None


class AFNe:
    """Autômato finito não determinístico com movimentos ε.

    Estados são inteiros 0..n-1, numerados em largura a partir do inicial
    (q0). Há exatamente um estado final, como na construção de Thompson.
    """

    def __init__(self, num_estados: int, inicial: int, final: int, transicoes: list[Transicao]):
        self.num_estados = num_estados
        self.inicial = inicial
        self.final = final
        self.transicoes = transicoes
        self._vazias: dict[int, list[int]] = {q: [] for q in range(num_estados)}
        self._simbolicas: dict[int, list[Transicao]] = {q: [] for q in range(num_estados)}
        for t in transicoes:
            if t.vazia:
                self._vazias[t.origem].append(t.destino)
            else:
                self._simbolicas[t.origem].append(t)

    @property
    def alfabeto(self) -> frozenset[str]:
        simbolos: set[str] = set()
        for t in self.transicoes:
            if not t.vazia:
                simbolos |= t.simbolos
        return frozenset(simbolos)

    @property
    def total_vazias(self) -> int:
        return sum(1 for t in self.transicoes if t.vazia)

    def fecho_vazio(self, estados) -> frozenset[int]:
        """ε-fecho: estados alcançáveis apenas por movimentos ε."""
        pilha = list(estados)
        fecho = set(estados)
        while pilha:
            q = pilha.pop()
            for destino in self._vazias[q]:
                if destino not in fecho:
                    fecho.add(destino)
                    pilha.append(destino)
        return frozenset(fecho)

    def inicio(self) -> frozenset[int]:
        return self.fecho_vazio({self.inicial})

    def passo(self, estados, simbolo: str) -> frozenset[int]:
        """δ̂: lê um símbolo a partir de um conjunto de estados e aplica o ε-fecho."""
        destinos = {
            t.destino
            for q in estados
            for t in self._simbolicas[q]
            if simbolo in t.simbolos
        }
        return self.fecho_vazio(destinos)

    def aceita(self, cadeia: str) -> bool:
        estados = self.inicio()
        for simbolo in cadeia:
            estados = self.passo(estados, simbolo)
            if not estados:
                return False
        return self.final in estados

    def rastrear(self, cadeia: str) -> list[dict]:
        """Sequência de conjuntos de estados ativos, passo a passo."""
        estados = self.inicio()
        passos = [{"passo": 0, "simbolo": "ε-fecho inicial", "estados": estados}]
        for i, simbolo in enumerate(cadeia, start=1):
            estados = self.passo(estados, simbolo)
            passos.append({"passo": i, "simbolo": simbolo, "estados": estados})
            if not estados:
                break
        return passos

    def para_dot(self, titulo: str = "AFNe") -> str:
        """Descrição Graphviz (DOT) do autômato."""
        linhas = [
            f'digraph "{_escapar_dot(titulo)}" {{',
            "  rankdir=LR;",
            '  graph [fontname="Helvetica", nodesep=0.25, ranksep=0.35];',
            '  node [shape=circle, fontname="Helvetica", fontsize=11, width=0.45, fixedsize=true];',
            '  edge [fontname="Helvetica", fontsize=11, arrowsize=0.7];',
            '  inicio [shape=none, label="início", fixedsize=false, fontsize=10];',
            f"  inicio -> q{self.inicial};",
            f"  q{self.final} [shape=doublecircle];",
        ]
        for t in self.transicoes:
            if t.vazia:
                estilo = 'label="ε", style=dashed, color="#6b7280", fontcolor="#6b7280"'
            else:
                estilo = f'label="{_escapar_dot(t.rotulo)}", color="#0f4c81", fontcolor="#0f4c81"'
            linhas.append(f"  q{t.origem} -> q{t.destino} [{estilo}];")
        linhas.append("}")
        return "\n".join(linhas)


def _escapar_dot(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def rotulo_visivel(simbolo: str) -> str:
    """Representação legível de um símbolo, igual à da notação formal.

    O espaço vira ␣ e a pontuação isolada fica entre aspas ('.', '-', '(').
    """
    if simbolo == " ":
        return "␣"
    if len(simbolo) == 1 and not simbolo.isalnum():
        return f"'{simbolo}'"
    return simbolo


class _Construtor:
    """Construção de Thompson com duas simplificações que preservam a linguagem:

    1. Concatenação rs: o estado final de r é fundido com o inicial de s
       (em Thompson o inicial não tem arestas de entrada e o final não tem
       arestas de saída, então a fusão não cria caminhos novos).
    2. r? = (r | ε): em vez de dois estados extras, um único movimento ε
       liga o início ao fim do fragmento de r.

    A união e o fecho de Kleene seguem exatamente o modelo de Thompson.
    """

    def __init__(self):
        self.num_estados = 0
        self.transicoes: list[tuple[int, int, frozenset | None, str]] = []

    def novo_estado(self) -> int:
        self.num_estados += 1
        return self.num_estados - 1

    def vazia(self, origem, destino):
        self.transicoes.append((origem, destino, None, "ε"))

    def construir(self, no, inicio: int) -> int:
        """Constrói o fragmento de ``no`` a partir de ``inicio``; devolve o final."""
        if isinstance(no, Simbolo):
            fim = self.novo_estado()
            self.transicoes.append((inicio, fim, no.simbolos, rotulo_visivel(no.rotulo)))
            return fim
        if isinstance(no, Vazio):
            fim = self.novo_estado()
            self.vazia(inicio, fim)
            return fim
        if isinstance(no, Concatenacao):
            atual = inicio
            for parte in no.partes:
                atual = self.construir(parte, atual)
            return atual
        if isinstance(no, Uniao):
            finais = []
            for opcao in no.opcoes:
                entrada = self.novo_estado()
                self.vazia(inicio, entrada)
                finais.append(self.construir(opcao, entrada))
            fim = self.novo_estado()
            for f in finais:
                self.vazia(f, fim)
            return fim
        if isinstance(no, Repeticao):
            atual = inicio
            for _ in range(no.minimo):
                atual = self.construir(no.corpo, atual)
            if no.maximo is None:
                return self._fecho_kleene(no.corpo, atual)
            for _ in range(no.maximo - no.minimo):
                atual = self._opcional(no.corpo, atual)
            return atual
        raise TypeError(f"nó desconhecido: {no!r}")

    def _fecho_kleene(self, corpo, inicio: int) -> int:
        entrada = self.novo_estado()
        self.vazia(inicio, entrada)
        saida = self.construir(corpo, entrada)
        fim = self.novo_estado()
        self.vazia(saida, entrada)  # repetir
        self.vazia(saida, fim)  # parar
        self.vazia(inicio, fim)  # zero ocorrências
        return fim

    def _opcional(self, corpo, inicio: int) -> int:
        fim = self.construir(corpo, inicio)
        self.vazia(inicio, fim)
        return fim


def construir_afn(padrao: str) -> AFNe:
    """Gera o AFNε correspondente ao padrão (renumerado em largura a partir de q0)."""
    construtor = _Construtor()
    inicial = construtor.novo_estado()
    final = construtor.construir(analisar(padrao), inicial)

    # Renumera os estados em ordem de visita (busca em largura), para que os
    # nomes q0, q1, ... acompanhem a leitura do diagrama da esquerda para a direita.
    saidas: dict[int, list] = {}
    for origem, destino, simbolos, rotulo in construtor.transicoes:
        saidas.setdefault(origem, []).append((destino, simbolos, rotulo))
    novo_nome = {inicial: 0}
    fila = deque([inicial])
    while fila:
        q = fila.popleft()
        for destino, _, _ in saidas.get(q, []):
            if destino not in novo_nome:
                novo_nome[destino] = len(novo_nome)
                fila.append(destino)

    transicoes = [
        Transicao(novo_nome[o], novo_nome[d], s, r)
        for o, d, s, r in construtor.transicoes
    ]
    transicoes.sort(key=lambda t: (t.origem, t.destino))
    return AFNe(len(novo_nome), novo_nome[inicial], novo_nome[final], transicoes)
