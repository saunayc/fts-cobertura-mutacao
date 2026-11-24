# Livro de códigos — classificação do código não coberto (QP2)

Este documento é a referência única para **os dois avaliadores**. Cada avaliador
classifica todos os trechos de `trechos_<lib>.csv` **sem consultar a classificação
do outro**. Só depois de calculado o Kappa de Cohen (`scripts/kappa.py`) as
divergências são discutidas e resolvidas.

## Unidade de análise

Um **trecho** é (L) um bloco de comandos consecutivos não executados dentro do
mesmo escopo, ou (D) um desvio não exercitado cuja origem e destino foram
executados por outros caminhos. O código é mostrado na coluna `codigo`; o
avaliador pode (e deve) abrir o arquivo em `work/<lib>/src/` para ver o contexto.

## Categorias

| Código | Categoria | Definição operacional | Exemplos típicos |
|---|---|---|---|
| `EXC` | Tratamento de exceções | O trecho está dentro de um `except`/`finally`, ou existe para capturar, traduzir, recuperar ou relançar uma falha vinda de outra operação (I/O, conversão, biblioteca de terceiros). | `except ValueError: return value`; `except KeyError: raise ParserError(...)` |
| `VAL` | Validação defensiva de entradas | O trecho verifica tipo, faixa ou formato de um argumento recebido pela API e rejeita (lança erro) ou normaliza a entrada inválida. | `if not isinstance(x, int): raise TypeError`; `if bounds not in ('()', '[]'...): raise ValueError` |
| `CFG` | Ramos de configuração ou ambiente | O caminho depende de versão do Python, sistema operacional, variáveis de ambiente, dependências opcionais, `TYPE_CHECKING`, ou de um **parâmetro de configuração** (localidade/idioma, modo de acesso a arquivo, classe de storage, flags de customização). | `if sys.version_info < (3, 9)`; métodos de uma localidade específica não exercitada; `if self._mode == 'r'` |
| `LIM` | Casos-limite internos | Lógica normal de funcionamento acionada apenas por combinações particulares de valores ou estados internos (bordas numéricas, coleções vazias, cache cheio, ajustes de calendário, arredondamentos) que a documentação não explicita. | ajuste quando o dia excede o fim do mês; remoção do item mais antigo quando o cache enche |
| `MORTO` | Código morto | O trecho não pode ser executado por nenhuma entrada válida pela API pública sem violar o contrato da biblioteca (invariantes garantem que a condição nunca ocorre, corpo de método abstrato, ramo redundante). | `raise NotImplementedError` em classe abstrata; `else` após condições exaustivas |
| `OUTRO` | Não se encaixa | Use apenas quando nenhuma categoria se aplica; descreva na justificativa. A frequência de `OUTRO` é reportada como indicador da adequação do esquema. | funcionalidade pública não documentada |

## Regra de desempate (aplicar na ordem)

1. Está em `except`/`finally` ou existe para tratar falha de outra operação → `EXC`.
2. Rejeita/normaliza argumento inválido recebido pela API → `VAL`.
3. Depende de ambiente ou de parâmetro de configuração → `CFG`.
4. É inalcançável pela API pública → `MORTO`.
5. Caso contrário, se é lógica normal sob valores particulares → `LIM`.
6. Nenhuma das anteriores → `OUTRO`.

## Como preencher

* Coluna `categoria`: um dos códigos acima.
* Coluna `alcancavel`: `sim` / `nao` — se é possível escrever um teste que execute o
  trecho usando apenas a API pública (usado pela regra de parada da QP3).
* Coluna `justificativa`: uma frase curta.
