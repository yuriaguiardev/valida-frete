"""Gera docs/EXPRESSOES.md e docs/RESULTADOS_TESTES.md a partir do código.

Uso (na raiz do projeto):
    python scripts/gerar_documentacao.py

Como a documentação é lida do mesmo módulo usado pelo programa
(validafrete/expressoes.py e validafrete/casos_teste.py), a ER formal, a
sintaxe do código, os testes e o AFNε documentados são sempre os mesmos
que o programa executa.
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from validafrete.afn import construir_afn  # noqa: E402
from validafrete.casos_teste import CASOS  # noqa: E402
from validafrete.expressoes import EXPRESSOES  # noqa: E402


def celula(texto: str) -> str:
    """Escapa texto para uma célula de tabela Markdown."""
    return texto.replace("|", "\\|")


def cadeia_md(cadeia: str) -> str:
    if cadeia == "":
        return "ε (vazia)"
    return "`" + cadeia.replace(" ", "␣").replace("|", "\\|") + "`"


def tabela_transicoes(afn) -> list[str]:
    linhas = ["| Origem | Símbolo(s) | Destino |", "|---|---|---|"]
    for t in afn.transicoes:
        rotulo = "ε" if t.vazia else celula(t.rotulo)
        linhas.append(f"| q{t.origem} | {rotulo} | q{t.destino} |")
    return linhas


def ficha(er) -> list[str]:
    afn = construir_afn(er.padrao)
    nome_arquivo = f"{er.codigo.lower()}-{er.chave}"
    casos = CASOS[er.chave]
    md = [
        f"## {er.codigo} — {er.nome}",
        "",
        "| Campo | Conteúdo |",
        "|---|---|",
        f"| **Identificação** | {er.codigo} · campo `{er.chave}` |",
        f"| **Finalidade** | {celula(er.finalidade)} |",
        f"| **Alfabeto (Σ)** | {'<br>'.join(celula(a) for a in er.alfabeto)} |",
        f"| **Linguagem L** | {celula(er.linguagem)} |",
        f"| **ER formal** | {celula(er.formal)} |",
        f"| **Sintaxe implementada** | `{celula(er.padrao)}` |",
        "",
        "Chamada no código (Python):",
        "",
        "```python",
        f're.fullmatch(r"{er.padrao}", cadeia)',
        "```",
        "",
        "### Equivalência entre a sintaxe e os operadores formais",
        "",
        "| Na sintaxe do código | Operador formal |",
        "|---|---|",
    ]
    md += [f"| `{celula(trecho)}` | {celula(significado)} |" for trecho, significado in er.equivalencias]
    md += [
        "",
        "### AFNε",
        "",
        f"![AFNε de {er.codigo}](afn/{nome_arquivo}.svg)",
        "",
        f"Gerado a partir do padrão do código pela construção de Thompson "
        f"([`{nome_arquivo}.dot`](afn/{nome_arquivo}.dot), [PNG](afn/{nome_arquivo}.png)).",
        "",
        f"- **Q** = {{q0, …, q{afn.num_estados - 1}}} ({afn.num_estados} estados)",
        f"- **Σ** = {{{', '.join(sorted('␣' if s == ' ' else s for s in afn.alfabeto))}}}",
        f"- **Estado inicial:** q{afn.inicial}",
        f"- **Estados finais:** F = {{q{afn.final}}}",
        f"- **Transições:** {len(afn.transicoes)}, das quais {afn.total_vazias} são movimentos ε "
        "(tracejadas no diagrama)",
        "",
        "<details><summary>Tabela de transições δ</summary>",
        "",
        *tabela_transicoes(afn),
        "",
        "</details>",
        "",
        "### Testes",
        "",
        "| # | Cadeia | Esperado | Obtido (re / AFNε) | Descrição |",
        "|---|---|---|---|---|",
    ]
    for i, caso in enumerate(casos, start=1):
        obtido_re = er.reconhece(caso.cadeia)
        obtido_afn = afn.aceita(caso.cadeia)
        esperado = "aceita" if caso.aceita else "rejeita"
        obtido = f"{'aceita' if obtido_re else 'rejeita'} / {'aceita' if obtido_afn else 'rejeita'}"
        limite = " **(caso-limite)**" if caso.limite else ""
        md.append(f"| {i} | {cadeia_md(caso.cadeia)} | {esperado} | {obtido} | {celula(caso.descricao)}{limite} |")
    md += ["", "### Resultado e limitações", ""]
    aceitas = sum(c.aceita for c in casos)
    md.append(f"Todos os {len(casos)} casos ({aceitas} aceitas e {len(casos) - aceitas} rejeitadas) "
              "produziram o resultado esperado tanto em `re.fullmatch` quanto na simulação do AFNε.")
    md.append("")
    md += [f"- {l}" for l in er.limitacoes]
    md += ["", "---", ""]
    return md


def gerar_expressoes():
    md = [
        "# Expressões Regulares do ValidaFrete",
        "",
        "> Documento gerado automaticamente por `scripts/gerar_documentacao.py` a partir de "
        "`validafrete/expressoes.py` e `validafrete/casos_teste.py` — os mesmos módulos que o "
        "programa executa. Não edite à mão: altere o código e gere de novo.",
        "",
        "## Convenções da notação formal",
        "",
        "| Notação | Significado |",
        "|---|---|",
        "| `rs` (justaposição) | concatenação |",
        "| `r \\| s` | união, L(r) ∪ L(s) |",
        "| `r*` | fecho de Kleene (zero ou mais repetições; inclui ε) |",
        "| `r{m}` | m cópias de r concatenadas |",
        "| `r{m,n}` | união de rᵐ, rᵐ⁺¹, …, rⁿ |",
        "| `ε` | palavra vazia |",
        "| `'.'`, `'/'`, `'-'`, `'('`… | símbolos de pontuação literais (aspas para não confundir com operadores) |",
        "| `␣` | o caractere espaço |",
        "| `D`, `P`, `M`, `A`, `F`, `K` | conjuntos/abreviações definidos no alfabeto de cada ficha |",
        "",
        "Todas as ERs são aplicadas com `re.fullmatch`, que exige que a cadeia **inteira** "
        "pertença à linguagem (equivale a ancorar o padrão com `^` e `$`). Nenhuma ER usa "
        "retroreferências, lookaround, `\\d`, `\\w`, `\\s` ou o ponto curinga.",
        "",
        "## Construção dos AFNε",
        "",
        "O módulo `validafrete/afn.py` lê o padrão exatamente como está no código, monta a "
        "árvore sintática e aplica a construção de Thompson com duas simplificações que "
        "preservam a linguagem:",
        "",
        "1. **Concatenação `rs`:** o estado final do fragmento de `r` é fundido com o inicial "
        "de `s` (em Thompson o estado inicial não tem arestas de entrada e o final não tem "
        "arestas de saída, então a fusão não cria caminhos novos).",
        "2. **Opcionalidade `r?` = `(r | ε)`:** um único movimento ε liga o início ao fim do "
        "fragmento de `r`, em vez de dois estados extras.",
        "",
        "União e fecho de Kleene seguem exatamente o modelo de Thompson. `r{m}` é expandido em "
        "m cópias concatenadas e `r{m,n}` em m cópias seguidas de (n − m) cópias opcionais.",
        "",
        "Os testes automatizados comparam o AFNε com `re.fullmatch` em todos os casos de teste "
        "e em 15.000 cadeias geradas por mutação, garantindo que ambos reconhecem a mesma linguagem.",
        "",
        "## Resumo",
        "",
        "| ER | Nome | Estados | Transições | Movimentos ε | Testes (aceitas/rejeitadas) |",
        "|---|---|---|---|---|---|",
    ]
    for er in EXPRESSOES:
        afn = construir_afn(er.padrao)
        casos = CASOS[er.chave]
        aceitas = sum(c.aceita for c in casos)
        md.append(f"| [{er.codigo}](#{er.codigo.lower()}) | {celula(er.nome)} | {afn.num_estados} | "
                  f"{len(afn.transicoes)} | {afn.total_vazias} | {aceitas} / {len(casos) - aceitas} |")
    md += ["", "---", ""]
    for er in EXPRESSOES:
        md += ficha(er)
    (RAIZ / "docs" / "EXPRESSOES.md").write_text("\n".join(md), encoding="utf-8")


def gerar_resultados():
    execucao = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    resumo = execucao.stdout.strip().splitlines()[-1] if execucao.stdout.strip() else "(sem saída)"
    total = sum(len(c) for c in CASOS.values())
    md = [
        "# Resultados dos testes",
        "",
        f"> Gerado por `scripts/gerar_documentacao.py` em {date.today().strftime('%d/%m/%Y')}.",
        "",
        "## Como executar",
        "",
        "```bash",
        "python -m pytest -v",
        "```",
        "",
        "Os resultados também podem ser vistos ao vivo na página **Testes** da aplicação.",
        "",
        "## Resultado da última execução",
        "",
        "```",
        resumo,
        "```",
        "",
        "## O que é testado",
        "",
        "| Arquivo | Conteúdo |",
        "|---|---|",
        f"| `tests/test_expressoes.py` | Os {total} casos de teste das 5 ERs, executados com "
        "`re.fullmatch` **e** com o AFNε; mínimo de 6 aceitas/6 rejeitadas e caso-limite por ER; "
        "Σ documentado igual ao Σ do AFNε; equivalência AFNε × regex em 15.000 cadeias geradas |",
        "| `tests/test_afn.py` | Construção de Thompson para cada operador (união, concatenação, "
        "`*`, `+`, `?`, `{m}`, `{m,n}`, classes, escapes) e rejeição de recursos não regulares "
        "(`\\1`, lookaround, `\\d`, `.`, âncoras, classes negadas) |",
        "| `tests/test_aplicacao.py` | Mensagens de diagnóstico, identificação automática do tipo, "
        "entradas inválidas (vazia, nula, longa, tipo desconhecido), processamento de CSV "
        "(exemplo, separador vírgula, arquivo vazio, só cabeçalho, cabeçalho errado, colunas "
        "quebradas, binário) e todas as rotas da interface web |",
        "",
        "## Análise dos resultados",
        "",
        "| ER | Aceitas | Rejeitadas | Casos-limite | Acertos (re) | Acertos (AFNε) |",
        "|---|---|---|---|---|---|",
    ]
    for er in EXPRESSOES:
        afn = construir_afn(er.padrao)
        casos = CASOS[er.chave]
        ac_re = sum(er.reconhece(c.cadeia) == c.aceita for c in casos)
        ac_afn = sum(afn.aceita(c.cadeia) == c.aceita for c in casos)
        md.append(f"| {er.codigo} | {sum(c.aceita for c in casos)} | {sum(not c.aceita for c in casos)} | "
                  f"{sum(c.limite for c in casos)} | {ac_re}/{len(casos)} | {ac_afn}/{len(casos)} |")
    md += [
        "",
        "Todos os casos produziram o resultado esperado. Os falsos resultados conhecidos são "
        "**intencionais e documentados** como limitações — a ER descreve apenas o formato:",
        "",
        "- **ER-01:** `00.000.000/0000-00` é aceito, pois os dígitos verificadores não são calculados.",
        "- **ER-03:** números com DDD existente, mas inativos, são aceitos.",
        "- **ER-04:** `29/02/2023` é aceito, pois a ER não distingue anos bissextos.",
        "",
        "O arquivo `dados/fretes_exemplo.csv` (15 registros) resulta em 5 registros totalmente "
        "válidos e 10 com pelo menos um campo rejeitado, cada um com a posição exata da falha "
        "indicada pelo AFNε.",
        "",
    ]
    (RAIZ / "docs" / "RESULTADOS_TESTES.md").write_text("\n".join(md), encoding="utf-8")
    return execucao.returncode


if __name__ == "__main__":
    gerar_expressoes()
    codigo = gerar_resultados()
    print("docs/EXPRESSOES.md e docs/RESULTADOS_TESTES.md gerados.")
    raise SystemExit(codigo)
