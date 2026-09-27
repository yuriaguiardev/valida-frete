"""Gera os diagramas dos AFNε (DOT, SVG e PNG) a partir dos padrões do código.

Uso (na raiz do projeto):
    python scripts/gerar_afn.py

Requer o Graphviz instalado (comando ``dot``). Os arquivos são gravados em
docs/afn/ (documentação) e validafrete/static/afn/ (interface web).
"""

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from validafrete.afn import construir_afn  # noqa: E402
from validafrete.expressoes import EXPRESSOES  # noqa: E402

DESTINO_DOCS = RAIZ / "docs" / "afn"
DESTINO_WEB = RAIZ / "validafrete" / "static" / "afn"


def main() -> int:
    if shutil.which("dot") is None:
        print("Erro: Graphviz não encontrado. Instale com 'brew install graphviz' "
              "ou 'sudo apt install graphviz' e rode novamente.")
        return 1
    DESTINO_DOCS.mkdir(parents=True, exist_ok=True)
    DESTINO_WEB.mkdir(parents=True, exist_ok=True)

    for er in EXPRESSOES:
        afn = construir_afn(er.padrao)
        nome = f"{er.codigo.lower()}-{er.chave}"
        arquivo_dot = DESTINO_DOCS / f"{nome}.dot"
        arquivo_dot.write_text(afn.para_dot(f"{er.codigo} {er.nome}"), encoding="utf-8")
        for formato, extra in (("svg", []), ("png", ["-Gdpi=200"])):
            saida = DESTINO_DOCS / f"{nome}.{formato}"
            subprocess.run(["dot", f"-T{formato}", *extra, str(arquivo_dot), "-o", str(saida)], check=True)
        shutil.copy(DESTINO_DOCS / f"{nome}.svg", DESTINO_WEB / f"{nome}.svg")
        print(f"{er.codigo}: {afn.num_estados} estados, {len(afn.transicoes)} transições "
              f"({afn.total_vazias} movimentos ε) -> docs/afn/{nome}.[dot|svg|png]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
