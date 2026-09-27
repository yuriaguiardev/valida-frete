"""Aplicação web (Flask) do ValidaFrete.

Páginas:
    /                    validar um valor digitado (por tipo ou identificação automática)
    /arquivo             processar uma planilha CSV de fretes
    /expressoes          fichas das cinco ERs, com AFNε e simulação passo a passo
    /testes              execução ao vivo dos casos de teste
"""

from __future__ import annotations

import base64
from pathlib import Path

from flask import Flask, abort, render_template, request

from .afn import rotulo_visivel
from .casos_teste import CASOS
from .expressoes import EXPRESSOES, por_chave
from .processador import COLUNAS, TAMANHO_MAXIMO_ARQUIVO, processar_arquivo
from .validador import ErroEntrada, afn_de, classificar, validar

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_EXEMPLO = RAIZ / "dados" / "fretes_exemplo.csv"


def create_app() -> Flask:
    app = Flask(__name__)
    # O Flask recusa uploads acima deste tamanho (erro 413, tratado abaixo).
    app.config["MAX_CONTENT_LENGTH"] = TAMANHO_MAXIMO_ARQUIVO + 64 * 1024

    @app.context_processor
    def globais():
        return {"expressoes": EXPRESSOES, "visivel": _visivel}

    @app.get("/")
    def inicio():
        # Também aceita /?cadeia=...&tipo=... para links diretos na demonstração.
        if "cadeia" in request.args:
            return _validar(request.args)
        return render_template("inicio.html")

    @app.post("/")
    def validar_valor():
        return _validar(request.form)

    def _validar(parametros):
        tipo = parametros.get("tipo", "auto")
        cadeia = parametros.get("cadeia")
        contexto = {"tipo": tipo, "cadeia": cadeia}
        try:
            if cadeia is None or cadeia == "":
                raise ErroEntrada("Entrada vazia: digite um valor para validar. "
                                  "(A palavra vazia ε não pertence a nenhuma das linguagens.)")
            if tipo == "auto":
                contexto["resultados"] = classificar(cadeia)
            else:
                contexto["resultados"] = [validar(tipo, cadeia)]
        except ErroEntrada as erro:
            contexto["erro"] = str(erro)
        return render_template("inicio.html", **contexto)

    @app.route("/arquivo", methods=["GET", "POST"])
    def arquivo():
        if request.method == "GET":
            return render_template("arquivo.html", colunas=COLUNAS)
        try:
            if "exemplo" in request.form:
                conteudo = ARQUIVO_EXEMPLO.read_bytes()
                nome = ARQUIVO_EXEMPLO.name
            else:
                enviado = request.files.get("planilha")
                if enviado is None or enviado.filename == "":
                    raise ErroEntrada("Nenhum arquivo foi selecionado.")
                if not enviado.filename.lower().endswith((".csv", ".txt")):
                    raise ErroEntrada("Formato não suportado: envie um arquivo .csv.")
                conteudo = enviado.read()
                nome = enviado.filename
            relatorio = processar_arquivo(conteudo)
        except ErroEntrada as erro:
            return render_template("arquivo.html", colunas=COLUNAS, erro=str(erro)), 400

        # BOM no início para o Excel abrir o relatório com acentos corretos.
        csv_bytes = ("﻿" + relatorio.para_csv()).encode("utf-8")
        download = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode("ascii")
        return render_template("arquivo.html", colunas=COLUNAS, relatorio=relatorio,
                               nome=nome, download=download)

    @app.get("/expressoes")
    def lista_expressoes():
        return render_template("expressoes.html")

    @app.get("/expressoes/<chave>")
    def ficha(chave):
        try:
            er = por_chave(chave)
        except KeyError:
            abort(404)
        afn = afn_de(chave)
        contexto = {"er": er, "afn": afn, "casos": CASOS[chave],
                    "svg": _ler_svg(er)}
        cadeia = request.args.get("cadeia")
        if cadeia is not None:
            if len(cadeia) > 100:
                contexto["erro"] = "Cadeia muito longa para simular (limite de 100 caracteres)."
            else:
                contexto.update(cadeia=cadeia, passos=afn.rastrear(cadeia),
                                aceita_afn=afn.aceita(cadeia), aceita_re=er.reconhece(cadeia))
        return render_template("ficha.html", **contexto)

    @app.get("/testes")
    def testes():
        tabelas = []
        falhas = 0
        for er in EXPRESSOES:
            afn = afn_de(er.chave)
            linhas = []
            for caso in CASOS[er.chave]:
                obtido_re = er.reconhece(caso.cadeia)
                obtido_afn = afn.aceita(caso.cadeia)
                ok = obtido_re == caso.aceita == obtido_afn
                falhas += not ok
                linhas.append({"caso": caso, "re": obtido_re, "afn": obtido_afn, "ok": ok})
            tabelas.append({"er": er, "linhas": linhas})
        total = sum(len(t["linhas"]) for t in tabelas)
        return render_template("testes.html", tabelas=tabelas, total=total, falhas=falhas)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erro.html", titulo="Página não encontrada",
                               mensagem="O endereço acessado não existe."), 404

    @app.errorhandler(413)
    def muito_grande(_erro):
        return render_template("arquivo.html", colunas=COLUNAS,
                               erro="O arquivo excede o limite de 1 MB."), 413

    @app.errorhandler(500)
    def erro_interno(_erro):
        return render_template("erro.html", titulo="Erro interno",
                               mensagem="Ocorreu um erro inesperado ao processar a requisição."), 500

    return app


def _visivel(cadeia: str) -> str:
    """Mostra espaços como ␣ e a palavra vazia como ε."""
    if cadeia == "":
        return "ε"
    return "".join(rotulo_visivel(c) if c == " " else c for c in cadeia)


def _ler_svg(er) -> str | None:
    caminho = Path(__file__).parent / "static" / "afn" / f"{er.codigo.lower()}-{er.chave}.svg"
    if not caminho.exists():
        return None
    texto = caminho.read_text(encoding="utf-8")
    return texto[texto.find("<svg"):]  # remove o cabeçalho XML para embutir no HTML


app = create_app()
