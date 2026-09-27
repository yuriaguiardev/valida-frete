# Resultados dos testes

> Gerado por `scripts/gerar_documentacao.py` em 27/09/2026.

## Como executar

```bash
python -m pytest -v
```

Os resultados também podem ser vistos ao vivo na página **Testes** da aplicação.

## Resultado da última execução

```
223 passed in 0.27s
```

## O que é testado

| Arquivo | Conteúdo |
|---|---|
| `tests/test_expressoes.py` | Os 80 casos de teste das 5 ERs, executados com `re.fullmatch` **e** com o AFNε; mínimo de 6 aceitas/6 rejeitadas e caso-limite por ER; Σ documentado igual ao Σ do AFNε; equivalência AFNε × regex em 15.000 cadeias geradas |
| `tests/test_afn.py` | Construção de Thompson para cada operador (união, concatenação, `*`, `+`, `?`, `{m}`, `{m,n}`, classes, escapes) e rejeição de recursos não regulares (`\1`, lookaround, `\d`, `.`, âncoras, classes negadas) |
| `tests/test_aplicacao.py` | Mensagens de diagnóstico, identificação automática do tipo, entradas inválidas (vazia, nula, longa, tipo desconhecido), processamento de CSV (exemplo, separador vírgula, arquivo vazio, só cabeçalho, cabeçalho errado, colunas quebradas, binário) e todas as rotas da interface web |

## Análise dos resultados

| ER | Aceitas | Rejeitadas | Casos-limite | Acertos (re) | Acertos (AFNε) |
|---|---|---|---|---|---|
| ER-01 | 8 | 8 | 4 | 16/16 | 16/16 |
| ER-02 | 8 | 8 | 4 | 16/16 | 16/16 |
| ER-03 | 8 | 8 | 3 | 16/16 | 16/16 |
| ER-04 | 8 | 8 | 5 | 16/16 | 16/16 |
| ER-05 | 8 | 8 | 4 | 16/16 | 16/16 |

Todos os casos produziram o resultado esperado. Os falsos resultados conhecidos são **intencionais e documentados** como limitações — a ER descreve apenas o formato:

- **ER-01:** `00.000.000/0000-00` é aceito, pois os dígitos verificadores não são calculados.
- **ER-03:** números com DDD existente, mas inativos, são aceitos.
- **ER-04:** `29/02/2023` é aceito, pois a ER não distingue anos bissextos.

O arquivo `dados/fretes_exemplo.csv` (15 registros) resulta em 5 registros totalmente válidos e 10 com pelo menos um campo rejeitado, cada um com a posição exata da falha indicada pelo AFNε.
