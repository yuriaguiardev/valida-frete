"""Testes do validador, do processamento de CSV e da interface web."""

from pathlib import Path

import pytest

from validafrete.app import create_app
from validafrete.processador import processar_arquivo
from validafrete.validador import ErroEntrada, classificar, validar

DADOS = Path(__file__).resolve().parent.parent / "dados"


# --- validador -------------------------------------------------------------

def test_validar_aceita_e_rejeita_com_mensagem():
    assert validar("placa", "BRA2E19").aceita
    r = validar("placa", "BRA-2E19")
    assert not r.aceita
    assert "posição 6" in r.mensagem  # "BRA-2" é prefixo do padrão antigo


def test_diagnostico_de_simbolo_fora_do_alfabeto():
    r = validar("cnpj", " 11222333000181")
    assert "não pertence ao alfabeto" in r.mensagem
    assert "espaços" in r.mensagem


def test_diagnostico_de_cadeia_incompleta():
    assert "incompleta" in validar("data", "15/10/20").mensagem


def test_diagnostico_de_palavra_vazia():
    assert "ε" in validar("valor", "").mensagem


def test_classificar_identifica_o_tipo():
    aceitas = [r.expressao.chave for r in classificar("R$ 1.250,00") if r.aceita]
    assert aceitas == ["valor"]


def test_entradas_invalidas():
    with pytest.raises(ErroEntrada):
        validar("inexistente", "abc")
    with pytest.raises(ErroEntrada):
        validar("placa", None)
    with pytest.raises(ErroEntrada):
        validar("placa", "A" * 500)


# --- processamento de CSV ----------------------------------------------------

def test_processa_arquivo_de_exemplo():
    relatorio = processar_arquivo((DADOS / "fretes_exemplo.csv").read_bytes())
    assert relatorio.total == 15
    assert 0 < relatorio.validos < relatorio.total
    assert "linha;id;situacao" in relatorio.para_csv()


def test_arquivo_totalmente_valido():
    relatorio = processar_arquivo((DADOS / "fretes_validos.csv").read_bytes())
    assert relatorio.validos == relatorio.total == 5


def test_arquivo_com_virgula_como_separador():
    relatorio = processar_arquivo((DADOS / "fretes_separador_virgula.csv").read_bytes())
    assert relatorio.validos == 1


def test_valor_com_espaco_extra_nao_e_aparado():
    relatorio = processar_arquivo((DADOS / "fretes_exemplo.csv").read_bytes())
    f013 = next(r for r in relatorio.registros if r.identificador == "F013")
    assert not f013.campos["cnpj"].aceita


@pytest.mark.parametrize(
    "arquivo, trecho",
    [
        ("vazio.csv", "vazio"),
        ("so_cabecalho.csv", "nenhum registro"),
        ("cabecalho_errado.csv", "Colunas ausentes"),
    ],
)
def test_arquivos_invalidos(arquivo, trecho):
    with pytest.raises(ErroEntrada, match=trecho):
        processar_arquivo((DADOS / "invalidos" / arquivo).read_bytes())


def test_linhas_com_colunas_quebradas_sao_sinalizadas():
    relatorio = processar_arquivo((DADOS / "invalidos" / "colunas_quebradas.csv").read_bytes())
    assert all(r.erro and not r.valido for r in relatorio.registros)


def test_arquivo_binario_e_recusado():
    with pytest.raises(ErroEntrada, match="binários"):
        processar_arquivo(b"\x89PNG\r\n\x00\x00")


# --- interface web -----------------------------------------------------------

@pytest.fixture
def cliente():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_paginas_principais(cliente):
    for rota in ("/", "/arquivo", "/expressoes", "/testes", "/expressoes/telefone"):
        assert cliente.get(rota).status_code == 200


def test_validacao_pela_web(cliente):
    resposta = cliente.post("/", data={"tipo": "auto", "cadeia": "BRA2E19"})
    assert "ER-02" in resposta.get_data(as_text=True)
    assert "ACEITA" in resposta.get_data(as_text=True)


def test_entrada_vazia_pela_web(cliente):
    resposta = cliente.post("/", data={"tipo": "auto", "cadeia": ""})
    assert "Entrada vazia" in resposta.get_data(as_text=True)


def test_upload_sem_arquivo(cliente):
    resposta = cliente.post("/arquivo", data={})
    assert resposta.status_code == 400
    assert "Nenhum arquivo" in resposta.get_data(as_text=True)


def test_upload_de_exemplo(cliente):
    resposta = cliente.post("/arquivo", data={"exemplo": "1"})
    assert "registros lidos" in resposta.get_data(as_text=True)


def test_simulacao_do_afn(cliente):
    resposta = cliente.get("/expressoes/data?cadeia=31/04/2025")
    texto = resposta.get_data(as_text=True)
    assert "REJEITA" in texto and "∅" in texto


def test_pagina_de_testes_sem_falhas(cliente):
    assert "80 de 80 casos passaram" in cliente.get("/testes").get_data(as_text=True)


def test_rota_inexistente(cliente):
    assert cliente.get("/nao-existe").status_code == 404
