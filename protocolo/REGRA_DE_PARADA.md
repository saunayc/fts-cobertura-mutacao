# Regra de parada dos testes estruturais (QP3)

**Situação:** proposta padrão adotada na execução. Ela ainda precisa ser validada
com a professora, como previsto no status report; se ela pedir outra regra, basta
ajustar a suíte em `suites/<lib>/structural/` e rodar de novo `scripts/measure.py <lib> final`.

A escrita de testes estruturais para cada biblioteca termina quando todo trecho
que a classificação da QP2 marcou como alcançável pela API pública (coluna
`alcancavel = sim` em `classificacao/avaliador_A_<lib>.csv`) já tem pelo menos um
teste direcionado (marcador `@pytest.mark.alvo("<id>")`). Se um trecho alcançável
não é coberto depois de até duas tentativas de teste, ele é registrado como resíduo
com a situação "tentativa sem sucesso" e a justificativa técnica, e a equipe segue
adiante. Trechos classificados como inalcançáveis (`alcancavel = nao`, em geral
código morto e ramos de ambiente que dependem de outra versão do Python ou de
empacotamento) não recebem teste e entram no resíduo como "previsto".

A regra tem três consequências que valem ser explicitadas no artigo. A primeira é
que o esforço é limitado pela classificação, e não por uma meta de porcentagem,
de modo que o resultado final mede quanto do não coberto era de fato alcançável.
A segunda é que os testes estruturais não usam mocks do ambiente (versão do Python,
ausência de `__spec__`), porque isso mediria o mock e não a biblioteca. A terceira
é que só se miram os trechos da lista da fase inicial. Desvios parciais que só
aparecem na fase final, quando uma linha antes totalmente não executada passa a
rodar, são reportados à parte ("desvio parcial revelado na fase final") e não
reabrem a escrita de testes.

Na execução, todos os trechos alcançáveis segundo o Avaliador A foram cobertos, com
uma única exceção: o ARW-T024, que se mostrou inalcançável na prática (ver `resultados/qp3_residuo.csv`).
