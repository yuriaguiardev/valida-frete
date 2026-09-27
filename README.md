# ValidaFrete — Validador de Cadastros de Fretes com Expressões Regulares

Trabalho do 1º Bimestre de **Linguagens Formais e Autômatos** — turma **CC6NA**.

**Equipe:** Yuri Aguiar · Pedro Paulo · João Rath

**Repositório:** https://github.com/yuriaguiardev/valida-frete

---

## Problema

Transportadoras recebem planilhas de fretes digitadas à mão por diferentes filiais e
parceiros. Os dados chegam com erros de formatação — CNPJ com máscara incompleta, placas
em minúsculas, telefones com DDD inexistente, datas impossíveis (31/04) e valores
monetários mal escritos — que só são percebidos quando a coleta falha ou a nota fiscal é
recusada.

## Solução

O **ValidaFrete** é uma aplicação web (Python + Flask) que valida cada campo de um cadastro
de frete com uma Expressão Regular própria e explica **onde e por que** um valor foi
rejeitado, usando a simulação do AFNε equivalente.

| Entrada | Processamento | Saída |
|---|---|---|
| Um valor digitado, com o tipo escolhido ou identificado automaticamente | `re.fullmatch` com a ER do campo; em caso de rejeição, simulação do AFNε para localizar o símbolo que falhou | Aceita/rejeitada + mensagem com a posição do erro |
| Planilha CSV de fretes (`id;cnpj;placa;telefone;data;valor`) | Validação de todos os campos de todos os registros | Resumo por ER, tabela destacando os erros e relatório CSV para download |
| Uma cadeia qualquer na ficha de uma ER | Simulação passo a passo do AFNε | Conjunto de estados ativos após cada símbolo |

## As cinco Expressões Regulares

| ER | Campo | Sintaxe no código |
|---|---|---|
| ER-01 | CNPJ alfanumérico ou numérico (novo formato da Receita, 2026) | `[A-Z0-9]{2}\.[A-Z0-9]{3}\.[A-Z0-9]{3}/[A-Z0-9]{4}-[0-9]{2}\|[A-Z0-9]{12}[0-9]{2}` |
| ER-02 | Placa (padrão antigo ou Mercosul) | `[A-Z]{3}(-?[0-9]{4}\|[0-9][A-Z][0-9]{2})` |
| ER-03 | Telefone com os 67 DDDs válidos | `(\+55 ?)?(\((1[1-9]\|2[12478]\|…)\)\|(1[1-9]\|…)) ?(9[0-9]{4}\|[2-5][0-9]{3})-?[0-9]{4}` |
| ER-04 | Data DD/MM/AAAA com dia compatível com o mês | `((0[1-9]\|[12][0-9])/(0[1-9]\|1[0-2])\|30/(0[13-9]\|1[0-2])\|31/(0[13578]\|1[02]))/(19\|20)[0-9]{2}` |
| ER-05 | Valor em reais | `R\$ ?(0\|[1-9][0-9]{0,2}(\.[0-9]{3})*\|[1-9][0-9]*),[0-9]{2}` |

A documentação completa de cada ER (alfabeto, linguagem, notação formal, equivalência,
AFNε, testes e limitações) está em **[docs/EXPRESSOES.md](docs/EXPRESSOES.md)**.

## Instalação

Requisitos: **Python 3.10 ou superior**.

```bash
git clone https://github.com/yuriaguiardev/valida-frete.git
cd valida-frete

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
python -m validafrete
```

Abra **http://127.0.0.1:5050** no navegador. Páginas:

- **Validar valor** — digite um valor e escolha o tipo (ou deixe identificar automaticamente).
- **Processar planilha** — envie um CSV ou clique em *Usar arquivo de exemplo*.
- **Expressões e AFNε** — ficha de cada ER com diagrama e simulação passo a passo.
- **Testes** — executa ao vivo os 80 casos de teste (regex e AFNε).

## Testes

```bash
python -m pytest -v
```

São 223 testes automatizados: os 80 casos das ERs (16 por ER: 8 aceitas e 8 rejeitadas,
com casos-limite), a comparação AFNε × `re.fullmatch` em 15.000 cadeias geradas, a
construção de Thompson e o tratamento de entradas inválidas. Detalhes e análise em
[docs/RESULTADOS_TESTES.md](docs/RESULTADOS_TESTES.md).

## Regenerar diagramas e documentação

Os AFNε são gerados **a partir do próprio padrão do código** (construção de Thompson), o que
garante que ER, código, testes e autômato representem a mesma linguagem.

```bash
# requer Graphviz: brew install graphviz  |  sudo apt install graphviz
python scripts/gerar_afn.py            # docs/afn/*.dot|svg|png
python scripts/gerar_documentacao.py   # docs/EXPRESSOES.md e docs/RESULTADOS_TESTES.md
python scripts/gerar_relatorio.py      # docs/entrega/relatorio_tecnico.pdf (usa o Google Chrome)
pip install -r requirements-docs.txt
python scripts/gerar_slides.py         # docs/entrega/apresentacao.pptx
```

## Entregáveis

| Item | Arquivo |
|---|---|
| Relatório técnico (PDF) | [docs/entrega/relatorio_tecnico.pdf](docs/entrega/relatorio_tecnico.pdf) |
| Apresentação (PPTX e PDF) | [docs/entrega/apresentacao.pptx](docs/entrega/apresentacao.pptx) · [PDF](docs/entrega/apresentacao.pdf) — roteiro de fala nas notas do orador |
| Expressões Regulares documentadas | [docs/EXPRESSOES.md](docs/EXPRESSOES.md) |
| Diagramas dos AFNε | [docs/afn/](docs/afn/) |
| Testes e análise | [tests/](tests/) · [docs/RESULTADOS_TESTES.md](docs/RESULTADOS_TESTES.md) |
| Contribuições | [CONTRIBUICOES.md](CONTRIBUICOES.md) |
| Planejamento (Etapa 1) | [docs/PLANEJAMENTO_ETAPA1.md](docs/PLANEJAMENTO_ETAPA1.md) |

## Estrutura do repositório

```
validafrete/
├── expressoes.py      # as 5 ERs (fonte única: formal, sintaxe, alfabeto, limitações)
├── casos_teste.py     # 16 casos de teste por ER
├── afn.py             # analisador do padrão, construção de Thompson, simulação do AFNε
├── validador.py       # validação de um valor + diagnóstico da rejeição
├── processador.py     # leitura e validação de planilhas CSV
├── app.py             # rotas da aplicação web (Flask)
├── templates/         # páginas HTML
└── static/            # CSS e diagramas SVG
tests/                 # testes automatizados (pytest)
dados/                 # CSVs de exemplo (válidos, com erros e inválidos)
docs/
├── EXPRESSOES.md      # fichas das ERs
├── RESULTADOS_TESTES.md
├── afn/               # diagramas dos AFNε (DOT, SVG, PNG)
└── entrega/           # relatório técnico e apresentação
scripts/               # geração de diagramas, documentação, relatório e slides
CONTRIBUICOES.md       # registro das contribuições dos integrantes
```

## Dados de exemplo

| Arquivo | Conteúdo |
|---|---|
| `dados/fretes_exemplo.csv` | 15 fretes: 5 totalmente válidos e 10 com erros variados |
| `dados/fretes_validos.csv` | 5 fretes sem nenhum erro |
| `dados/fretes_separador_virgula.csv` | Mesmo formato, com `,` como separador |
| `dados/invalidos/*.csv` | Arquivo vazio, só cabeçalho, cabeçalho errado e colunas quebradas |

## Dependências

| Pacote | Uso |
|---|---|
| Flask ≥ 3.0 | Interface web |
| pytest ≥ 8.0 | Testes automatizados |
| `re` (biblioteca padrão) | Motor de Expressões Regulares |
| Graphviz *(opcional)* | Desenhar os AFNε a partir dos arquivos `.dot` |
| python-pptx *(opcional)* | Gerar a apresentação (`scripts/gerar_slides.py`) |

## Referências

- Python Software Foundation. *re — Regular expression operations*. https://docs.python.org/3/library/re.html
- HOPCROFT, J. E.; MOTWANI, R.; ULLMAN, J. D. *Introdução à Teoria de Autômatos, Linguagens e Computação*. Elsevier.
- THOMPSON, K. *Regular expression search algorithm*. Communications of the ACM, 11(6), 1968.
- Receita Federal do Brasil. Instrução Normativa RFB nº 2.229/2024 (CNPJ alfanumérico).
- Anatel. Plano de numeração — códigos nacionais (DDD).
- Resolução CONTRAN nº 729/2018 (placas no padrão Mercosul).

## Uso de Inteligência Artificial

Conforme exigido pelas orientações do trabalho, declaramos o uso do assistente **Claude
Code (Anthropic)** como ferramenta de apoio nas seguintes tarefas:

- sugestão da estrutura inicial do projeto e das páginas web;
- apoio na implementação do módulo `afn.py` (construção de Thompson e simulação);
- geração dos scripts de diagramas e de documentação;
- revisão dos casos de teste e redação inicial do README, do relatório e dos slides.

Todo o conteúdo foi revisado pela equipe. Os integrantes compreendem, sabem explicar e
conseguem modificar as expressões, os autômatos e o código apresentados. A escolha do tema,
das linguagens reconhecidas e a validação dos resultados são de responsabilidade da equipe.

## Licença

Projeto acadêmico, sem fins comerciais.
