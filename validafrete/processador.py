"""Processamento de planilhas CSV de cadastros de fretes.

Entrada: arquivo CSV com cabeçalho contendo as colunas cnpj, placa, telefone,
data e valor (a coluna id é opcional). Separador ';' ou ','.
Saída: resultado por registro/campo, resumo por ER e um CSV de relatório.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from .expressoes import EXPRESSOES, por_chave
from .validador import ErroEntrada, Resultado, validar

COLUNAS = tuple(er.chave for er in EXPRESSOES)
TAMANHO_MAXIMO_ARQUIVO = 1024 * 1024  # 1 MB
MAXIMO_REGISTROS = 5000


@dataclass
class Registro:
    linha: int  # linha no arquivo (o cabeçalho é a linha 1)
    identificador: str
    campos: dict[str, Resultado] = field(default_factory=dict)
    erro: str | None = None  # problema estrutural (ex.: número de colunas)

    @property
    def valido(self) -> bool:
        return self.erro is None and all(r.aceita for r in self.campos.values())


@dataclass
class Relatorio:
    registros: list[Registro]
    avisos: list[str]

    @property
    def total(self) -> int:
        return len(self.registros)

    @property
    def validos(self) -> int:
        return sum(1 for r in self.registros if r.valido)

    def resumo(self) -> list[dict]:
        """Quantidade de cadeias aceitas e rejeitadas por ER."""
        linhas = []
        for er in EXPRESSOES:
            resultados = [r.campos[er.chave] for r in self.registros if er.chave in r.campos]
            aceitas = sum(1 for r in resultados if r.aceita)
            linhas.append({"expressao": er, "aceitas": aceitas, "rejeitadas": len(resultados) - aceitas})
        return linhas

    def para_csv(self) -> str:
        """Relatório de saída: valor original, situação e motivo de cada campo."""
        saida = io.StringIO()
        escritor = csv.writer(saida, delimiter=";")
        cabecalho = ["linha", "id", "situacao"]
        for chave in COLUNAS:
            cabecalho += [chave, f"{chave}_ok", f"{chave}_motivo"]
        escritor.writerow(cabecalho)
        for reg in self.registros:
            situacao = "VALIDO" if reg.valido else ("ERRO_ESTRUTURA" if reg.erro else "INVALIDO")
            linha = [reg.linha, reg.identificador, situacao]
            for chave in COLUNAS:
                r = reg.campos.get(chave)
                if r is None:
                    linha += ["", "", reg.erro or ""]
                else:
                    linha += [r.cadeia, "sim" if r.aceita else "nao", "" if r.aceita else r.mensagem]
            escritor.writerow(linha)
        return saida.getvalue()


def decodificar(conteudo: bytes) -> str:
    """Aceita UTF-8 (com ou sem BOM) e Windows-1252, comum em planilhas do Excel."""
    if not conteudo:
        raise ErroEntrada("O arquivo enviado está vazio.")
    if len(conteudo) > TAMANHO_MAXIMO_ARQUIVO:
        raise ErroEntrada("O arquivo excede o limite de 1 MB.")
    if b"\x00" in conteudo:
        raise ErroEntrada("O arquivo não parece ser um texto CSV (contém bytes binários).")
    for codificacao in ("utf-8-sig", "cp1252"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ErroEntrada("Não foi possível ler o arquivo: use a codificação UTF-8.")


def processar_texto(texto: str) -> Relatorio:
    """Valida todas as linhas de um CSV já decodificado."""
    linhas = [linha for linha in texto.splitlines() if linha.strip()]
    if not linhas:
        raise ErroEntrada("O arquivo não contém nenhuma linha preenchida.")

    # ';' é o padrão do Excel em português; ',' também é aceito.
    delimitador = ";" if linhas[0].count(";") >= linhas[0].count(",") else ","
    leitor = csv.reader(io.StringIO(texto), delimiter=delimitador)

    cabecalho = [c.strip().lower() for c in next(leitor)]
    faltando = [c for c in COLUNAS if c not in cabecalho]
    if faltando:
        raise ErroEntrada(
            "Cabeçalho inválido. Colunas ausentes: " + ", ".join(faltando)
            + ". O cabeçalho esperado é: id;" + ";".join(COLUNAS)
        )
    if len(set(cabecalho)) != len(cabecalho):
        raise ErroEntrada("O cabeçalho possui colunas repetidas.")

    avisos = []
    extras = [c for c in cabecalho if c not in COLUNAS and c != "id"]
    if extras:
        avisos.append("Colunas ignoradas (não possuem ER associada): " + ", ".join(extras) + ".")
    indice = {nome: i for i, nome in enumerate(cabecalho)}

    registros = []
    for valores in leitor:
        if not any(v.strip() for v in valores):
            continue  # linha em branco
        if len(registros) >= MAXIMO_REGISTROS:
            avisos.append(f"Apenas os primeiros {MAXIMO_REGISTROS} registros foram processados.")
            break
        numero = leitor.line_num
        identificador = valores[indice["id"]] if "id" in indice and indice["id"] < len(valores) else str(len(registros) + 1)
        registro = Registro(numero, identificador)
        if len(valores) != len(cabecalho):
            registro.erro = (f"A linha tem {len(valores)} coluna(s), mas o cabeçalho tem "
                             f"{len(cabecalho)}. Verifique separadores sobrando ou faltando.")
        else:
            # Os valores NÃO são aparados (strip): um espaço extra faz parte da
            # cadeia e deve ser rejeitado pela ER, exatamente como nos testes.
            for chave in COLUNAS:
                valor = valores[indice[chave]]
                try:
                    registro.campos[chave] = validar(chave, valor)
                except ErroEntrada as erro:
                    registro.campos[chave] = Resultado(por_chave(chave), valor, False, str(erro))
        registros.append(registro)

    if not registros:
        raise ErroEntrada("O arquivo tem cabeçalho, mas nenhum registro de frete.")
    return Relatorio(registros, avisos)


def processar_arquivo(conteudo: bytes) -> Relatorio:
    return processar_texto(decodificar(conteudo))
