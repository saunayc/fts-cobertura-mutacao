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

> Classificação de um único avaliador (A). O Kappa de Cohen só pode ser calculado depois que o
> Avaliador B preencher `classificacao/avaliador_B_EM_BRANCO_<lib>.csv` (renomeado para
> `avaliador_B_<lib>.csv`) e rodar `python scripts/kappa.py --todas`.

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
