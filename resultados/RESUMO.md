# Resumo dos resultados

Gerado por `scripts/analyze.py`. Commits fixados em `subjects.lock.json`.

## QP1 — Suíte funcional (caixa-preta)

| Biblioteca | Requisitos | Testes* | Comandos | Desvios | Blocos `except` | Mutantes | Escore de mutação |
|---|---:|---:|---:|---:|---:|---:|---:|
| tinydb | 37 | 78 passed, 2 xfailed | 94.1% | 84.9% | 80.0% (4/5) | 764 | 65.0% |
| arrow | 32 | 203 passed, 3 xfailed | 86.2% | 69.5% | 41.7% (5/12) | 3510 | 63.0% |
| humanize | 17 | 123 passed, 1 xfailed | 87.4% | 77.1% | 78.6% (11/14) | 1348 | 68.1% |

\* contagem de casos de teste executados pelo pytest (inclui parametrizações e `xfail`).

Métricas por módulo: `resultados/qp1_modulos.csv`.

## QP2 — Categorias do código não coberto (Avaliador A)

| Categoria | tinydb | arrow | humanize | Total | % |
|---|---:|---:|---:|---:|---:|
| Tratamento de exceções | 1 | 5 | 2 | 8 | 4.1% |
| Validação defensiva | 10 | 28 | 12 | 50 | 25.4% |
| Configuração/ambiente | 1 | 51 | 3 | 55 | 27.9% |
| Casos-limite internos | 9 | 32 | 19 | 60 | 30.5% |
| Código morto | 5 | 4 | 4 | 13 | 6.6% |
| Outro | 8 | 3 | 0 | 11 | 5.6% |
| **Total** | 34 | 123 | 40 | 197 | 100% |

**Hipótese** (exceções + validações defensivas > 50% do não coberto): 58/197 = 29.4% na classificação A — **não sustentada**.
- tinydb: 11/34 = 32.4%
- arrow: 33/123 = 26.8%
- humanize: 14/40 = 35.0%

### Concordância entre avaliadores (antes da resolução de divergências)

Avaliador A e Avaliador B são duas instâncias de IA (Claude) que classificaram de forma independente;
B trabalhou numa pasta isolada, só com o livro de códigos, os trechos e o código-fonte, sem acesso à classificação A.

| Biblioteca | n | Concordância observada | Kappa de Cohen | Interpretação (Landis & Koch) |
|---|---:|---:|---:|---|
| tinydb | 34 | 79.4% | 0.726 | substancial |
| arrow | 123 | 91.1% | 0.873 | quase perfeita |
| humanize | 40 | 97.5% | 0.962 | quase perfeita |
| **todas** | 197 | 90.4% | 0.871 | quase perfeita |

Distribuição segundo o Avaliador B: Tratamento de exceções 7, Validação defensiva 53, Configuração/ambiente 53, Casos-limite internos 67, Código morto 8, Outro 9. Exceções + validações = 60/197 = 30.5% — hipótese também não sustentada pelo Avaliador B.

Matriz de confusão e lista de divergências: `python scripts/kappa.py --todas` e `classificacao/divergencias_todas.csv` (coluna `consenso` a preencher na reunião).

## QP3 — Ganho com testes estruturais direcionados

| Biblioteca | Métrica | Inicial | Final | Ganho (p.p.) |
|---|---|---:|---:|---:|
| tinydb | Comandos | 94.1% | 99.2% | +5.1 |
| tinydb | Desvios | 84.9% | 100.0% | +15.1 |
| tinydb | Blocos except | 80.0% | 100.0% | +20.0 |
| tinydb | Escore de mutação | 65.0% | 70.7% | +5.6 |
| tinydb | Mutantes (total) | 764 | 764 | |
| tinydb | Testes estruturais adicionados | — | 15 funções / 15 casos | |
| arrow | Comandos | 86.2% | 99.6% | +13.4 |
| arrow | Desvios | 69.5% | 98.8% | +29.3 |
| arrow | Blocos except | 41.7% | 83.3% | +41.7 |
| arrow | Escore de mutação | 63.0% | 72.2% | +9.3 |
| arrow | Mutantes (total) | 3510 | 3510 | |
| arrow | Testes estruturais adicionados | — | 45 funções / 235 casos | |
| humanize | Comandos | 87.4% | 99.5% | +12.0 |
| humanize | Desvios | 77.1% | 97.2% | +20.2 |
| humanize | Blocos except | 78.6% | 100.0% | +21.4 |
| humanize | Escore de mutação | 68.1% | 84.0% | +16.0 |
| humanize | Mutantes (total) | 1348 | 1348 | |
| humanize | Testes estruturais adicionados | — | 13 funções / 30 casos | |

### Código residual (não coberto após a QP3)

| Biblioteca | Trecho | Módulo | Linhas | Categoria (A) | Situação |
|---|---|---|---|---|---|
| tinydb | TDB-T013 | tinydb/storages.py | 57 | MORTO | previsto (inalcançável) |
| tinydb | TDB-T014 | tinydb/storages.py | 69 | MORTO | previsto (inalcançável) |
| tinydb | TDB-T030 | tinydb/utils.py | 128 | MORTO | previsto (inalcançável) |
| tinydb | TDB-T031 | tinydb/utils.py | 138 | MORTO | previsto (inalcançável) |
| tinydb | TDB-T032 | tinydb/utils.py | 141 | MORTO | previsto (inalcançável) |
| arrow | ARW-T024 | arrow/arrow.py | 1843-1847 | VAL | tentativa sem sucesso |
| arrow | ARW-T042 | arrow/locales.py | 257 | MORTO | previsto (inalcançável) |
| arrow | ARW-T093 | arrow/parser.py | 28-29 | CFG | previsto (inalcançável) |
| arrow | ARW-T094 | arrow/parser.py | 246 | CFG | previsto (inalcançável) |
| arrow | ARW-T101 | arrow/parser.py | 433 | MORTO | previsto (inalcançável) |
| arrow | ARW-T115 | arrow/parser.py | 690->-591 | MORTO | previsto (inalcançável) |
| arrow | ARW-T116 | arrow/parser.py | 692->-591 | MORTO | previsto (inalcançável) |
| humanize | HUM-T002 | humanize/i18n.py | 47 | CFG | previsto (inalcançável) |
| humanize | HUM-T003 | humanize/i18n.py | 86-90 | CFG | previsto (inalcançável) |
| humanize | HUM-T038 | humanize/time.py | 468->473 | MORTO | previsto (inalcançável) |
| humanize | HUM-T039 | humanize/time.py | 655->674 | MORTO | previsto (inalcançável) |
| humanize | HUM-T040 | humanize/time.py | 663->665 | MORTO | previsto (inalcançável) |
| humanize | (novo) | humanize/time.py | 206->256 |  | desvio parcial revelado na fase final |

## Análises complementares (definidas após a coleta)

Estas análises não estavam no plano original. Foram definidas depois de ver os dados e devem ser
apresentadas como exploratórias / de sensibilidade.

### Onde sobrevivem os mutantes

Cada mutante foi localizado no comando que altera (`scripts/mutant_lines.py`). Sobreviventes incluem os mutantes sem teste.

| Biblioteca | Fase | Sobreviventes | Em comando executado | Em comando não executado | Valor padrão na assinatura | Não identificado |
|---|---|---:|---:|---:|---:|---:|
| tinydb | inicial | 267 | 196 (73%) | 68 (25%) | 1 | 2 |
| tinydb | final | 224 | 213 (95%) | 9 (4%) | 0 | 2 |
| arrow | inicial | 1299 | 559 (43%) | 716 (55%) | 21 | 3 |
| arrow | final | 974 | 943 (97%) | 9 (1%) | 20 | 2 |
| humanize | inicial | 430 | 187 (43%) | 233 (54%) | 7 | 3 |
| humanize | final | 215 | 197 (92%) | 8 (4%) | 7 | 3 |

Na fase final, praticamente todo mutante que sobrevive está num comando que a suíte executa: o limite passou a ser a força dos oráculos (asserções), não a cobertura.

### Arrow com e sem `locales.py`

| Recorte | Fase | Comandos | Desvios | Escore de mutação | Mutantes |
|---|---|---:|---:|---:|---:|
| com locales.py | inicial | 86.2% | 69.5% | 63.0% | 3510 |
| com locales.py | final | 99.6% | 98.8% | 72.3% | 3510 |
| sem locales.py | inicial | 93.0% | 87.4% | 73.7% | 2824 |
| sem locales.py | final | 99.3% | 98.6% | 80.2% | 2824 |

### Hipótese sob diferentes ponderações

Participação de exceções + validações (EXC+VAL) no código não coberto pela suíte funcional.

| Ponderação | Avaliador A | Avaliador B |
|---|---:|---:|
| Contagem de trechos | 29.4% | 30.5% |
| Ponderado por comandos | 18.5% | 18.5% |
| Ponderado por mutantes | 12.6% | 12.5% |
| Contagem, sem `arrow/locales.py` | 39.6% | 40.3% |
| Por comandos, sem `arrow/locales.py` | 40.5% | 40.0% |

Em nenhuma ponderação EXC+VAL passa de 50%; a hipótese não se sustenta em nenhum recorte.
