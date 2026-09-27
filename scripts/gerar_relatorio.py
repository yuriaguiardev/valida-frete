"""Gera o relatório técnico (HTML e PDF) a partir do código e dos testes.

Uso (na raiz do projeto):
    python scripts/gerar_relatorio.py

O PDF é produzido pelo Google Chrome/Chromium em modo headless. Sem o Chrome,
o HTML é gerado e pode ser impresso em PDF por qualquer navegador.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from jinja2 import Environment, FileSystemLoader  # noqa: E402

from validafrete.afn import construir_afn  # noqa: E402
from validafrete.casos_teste import CASOS  # noqa: E402
from validafrete.expressoes import EXPRESSOES  # noqa: E402
from validafrete.processador import processar_arquivo  # noqa: E402
from validafrete.validador import validar  # noqa: E402

SAIDA = RAIZ / "docs" / "entrega"
CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def exibir(cadeia: str) -> str:
    return "ε (vazia)" if cadeia == "" else cadeia.replace(" ", "␣")


def dados():
    fichas = []
    for er in EXPRESSOES:
        afn = construir_afn(er.padrao)
        arquivo = f"{er.codigo.lower()}-{er.chave}"
        svg = (RAIZ / "docs" / "afn" / f"{arquivo}.svg").read_text(encoding="utf-8")
        casos = [{"caso": c, "exibida": exibir(c.cadeia), "re": er.reconhece(c.cadeia),
                  "afn": afn.aceita(c.cadeia)} for c in CASOS[er.chave]]
        fichas.append({
            "er": er, "afn": afn, "arquivo": arquivo, "svg": svg[svg.find("<svg"):],
            "sigma": ", ".join(sorted("␣" if s == " " else s for s in afn.alfabeto)),
            "casos": casos,
            "aceitas": sum(c.aceita for c in CASOS[er.chave]),
            "rejeitadas": sum(not c.aceita for c in CASOS[er.chave]),
            "limites": sum(c.limite for c in CASOS[er.chave]),
        })

    pytest = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                            cwd=RAIZ, capture_output=True, text=True)
    resumo = pytest.stdout.strip().splitlines()[-1]

    exemplos = [("cnpj", "12ABC345/01DE-35"), ("placa", "ABC-1D23"), ("telefone", "(23) 91234-5678"),
                ("data", "31/04/2026"), ("valor", "R$ 1.23,45"), ("cnpj", "33.000.167/0001-01 ")]
    mensagens = [(exibir(v), validar(k, v).mensagem) for k, v in exemplos]

    return {
        "fichas": fichas, "resumo_pytest": resumo,
        "total_casos": sum(len(c) for c in CASOS.values()),
        "exemplo": processar_arquivo((RAIZ / "dados" / "fretes_exemplo.csv").read_bytes()),
        "exemplos_mensagens": mensagens,
    }


def localizar_chrome():
    for candidato in CHROME:
        if os.path.exists(candidato) or shutil.which(candidato):
            return candidato
    return None


def main() -> int:
    ambiente = Environment(loader=FileSystemLoader(RAIZ / "scripts" / "modelos"), autoescape=True)
    html = ambiente.get_template("relatorio.html").render(**dados())
    SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo_html = SAIDA / "relatorio_tecnico.html"
    arquivo_html.write_text(html, encoding="utf-8")
    print(f"HTML: {arquivo_html.relative_to(RAIZ)}")

    chrome = localizar_chrome()
    if chrome is None:
        print("Chrome não encontrado: abra o HTML no navegador e use Imprimir > Salvar como PDF.")
        return 0
    arquivo_pdf = SAIDA / "relatorio_tecnico.pdf"
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={arquivo_pdf}", arquivo_html.as_uri()],
                   check=True, capture_output=True)
    print(f"PDF:  {arquivo_pdf.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
