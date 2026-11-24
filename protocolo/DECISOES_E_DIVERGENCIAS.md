# Decisões de execução, divergências encontradas e ameaças à validade

## Decisões de execução

**Commits fixados.** Cada biblioteca foi congelada na tag de release mais recente disponível em 23/11/2026: TinyDB `v4.9.0`, Arrow `1.4.0` e Humanize `4.17.0`. Os hashes completos e as dependências de execução estão em `subjects.lock.json`, e cada ambiente grava o próprio `pip freeze` em `work/<lib>/requirements.lock.txt`. As ferramentas de medição estão travadas em `requirements-tools.txt` (pytest 9.2.0, coverage 7.17.5, mutmut 3.8.1). O ambiente usado foi Linux com Python 3.13 e 2 núcleos.

**Isolamento.** O script `scripts/prepare.py` copia apenas o pacote de cada biblioteca para `work/<lib>/src/` e descarta a pasta de testes original. Para o Humanize foi preciso reproduzir uma etapa do build oficial, a compilação dos catálogos de tradução (`.po` para `.mo`) com Babel, porque o repositório não versiona os `.mo` e sem eles nenhuma tradução funciona. Também foi criado o arquivo `_version.py`, que no pacote oficial é gerado pelo hatch-vcs.

**Exclusões de medição.** O único arquivo excluído foi `tinydb/mypy_plugin.py`, um plugin do verificador de tipos mypy que não faz parte da biblioteca em execução e só pode ser importado com o mypy instalado. As localidades do Arrow (`locales.py`, mais de 6 mil linhas) foram mantidas na medição, o que pesa bastante nos números do Arrow e deve ser discutido no artigo.

**Definição do escore de mutação.** Escore = (mortos + timeout) / (total − ignorados). Mutantes "sem teste" (nenhum teste executa a linha mutada) contam como sobreviventes, como na definição clássica; nenhum mutante foi descartado como equivalente, então o escore é um limite inferior.

**Blocos `except`.** São contados pela AST de cada módulo; um bloco é considerado coberto quando o primeiro comando do seu corpo foi executado.

**Unidade de análise da QP2.** Um trecho é um bloco máximo de comandos consecutivos não executados no mesmo escopo (tipo L) ou um desvio não exercitado cuja origem e destino foram executados por outros caminhos (tipo D). A definição está em `scripts/extract_uncovered.py` e no livro de códigos.

**Categoria OUTRO.** O livro de códigos acrescenta às cinco categorias pré-definidas uma válvula de escape, `OUTRO`, para trechos que não se encaixam em nenhuma delas. Ela foi usada para API pública auxiliar que os requisitos não exigiam (por exemplo, a interface de dicionário do `LRUCache` do TinyDB). A frequência de `OUTRO` (11 de 197 trechos na classificação A) serve como indicador da adequação do esquema de cinco categorias.

## Divergências entre documentação e comportamento

A suíte funcional foi escrita a partir da documentação; quando um teste derivado dela falhava, a falha foi analisada sem consultar o código-fonte. Falhas que vinham de suposições minhas sem base na documentação (limiares do `humanize` do Arrow, strings de idiomas não documentados, a exceção exata para unidades inválidas) foram removidas ou afrouxadas. As falhas que contradizem a documentação foram mantidas como testes `xfail(strict=True)`. Elas continuam sendo executadas, então contam para a cobertura e para o escore de mutação, e passam a falhar se o comportamento mudar.

| ID | Biblioteca | O que a documentação diz | O que a biblioteca faz |
|---|---|---|---|
| DIVERGENCIA-01 | TinyDB | `matches()` exige casamento do valor inteiro ("Full item has to match the regex") | `matches("John")` casa com `"Johnny"`: ancora só no início |
| DIVERGENCIA-02 | TinyDB | `flags` altera a busca por regex | com o cache de consultas, `matches(r)` seguido de `matches(r, flags=re.I)` devolve o resultado em cache da primeira consulta |
| DIVERGENCIA-03 | Arrow | o README mostra `format()` como `'2013-05-11 13:23:58 -07:00'` | sai `'2013-05-11 13:23:58-07:00'` (sem espaço) |
| DIVERGENCIA-04 | Arrow | o guia mostra 5 intervalos em `span_range('hour', 12:30, 17:15)` | a biblioteca devolve 6 (inclui o das 17h) |
| DIVERGENCIA-05 | Arrow (ambígua) | a tabela de tokens lista `1381685817` como saída de `X` | um timestamp inteiro sai como `'1367741229.0'` |
| DIVERGENCIA-06 | Humanize | `activate(locale, path)` levanta `FileNotFoundError` se não encontrar o locale | se o mesmo locale já foi carregado do caminho padrão, o `path` é ignorado e nada é levantado |

Os testes estruturais registraram mais duas observações de comportamento que não chegam a ser divergências documentadas, mas valem uma nota no artigo: no Arrow, o nome `arrow.factory` resolve para o módulo `factory` e não para a função documentada `arrow.api.factory`; e `Arrow.format("YYY")` devolve string vazia em silêncio, porque o token é aceito pela expressão regular do formatador mas não tem tratamento.

## Ameaças à validade introduzidas pela execução

**Autoria da suíte funcional e conhecimento prévio.** A suíte funcional e a classificação A foram produzidas por um assistente de IA (Claude) a pedido da equipe. A suíte foi escrita a partir do README, dos guias e da referência de API (docstrings públicas extraídas com `pydoc`, sem abrir o corpo das funções), cumprindo o protocolo de não ler o código-fonte nessa etapa. Ainda assim, um modelo de linguagem pode ter visto essas bibliotecas populares durante o treinamento, o que é uma ameaça à validade interna análoga a um testador que já conhece a implementação. A equipe deve declarar isso e, se possível, revisar a suíte.

**Avaliadores da QP2.** O protocolo previa dois integrantes humanos classificando de forma independente. Nesta execução, os dois avaliadores foram instâncias de IA (Claude). O Avaliador A classificou com acesso ao restante do trabalho. O Avaliador B foi uma instância separada, iniciada do zero numa pasta isolada que continha só o livro de códigos, a lista de trechos, as planilhas em branco e o código-fonte das bibliotecas, sem acesso à classificação A. O Kappa de Cohen entre os dois foi 0,871 sobre 197 trechos (concordância observada de 90,4%). Isso precisa ser declarado no artigo como desvio do protocolo. A concordância alta entre dois modelos da mesma família pode refletir vieses compartilhados, e não necessariamente a clareza do livro de códigos. Por isso o número não é comparável a um Kappa entre avaliadores humanos. Se houver tempo, o ideal é que um integrante humano classifique usando `avaliador_B_EM_BRANCO_<lib>.csv` e que se compare humano × IA. As 19 divergências estão em `classificacao/divergencias_todas.csv`, para a resolução de consenso. A maior fonte de discordância foi a fronteira entre VAL e MORTO para guardas defensivas que a API pública raramente aciona (5 casos).

**Classificação A antes da QP3.** A coluna `alcancavel` foi preenchida antes de escrever os testes estruturais. O caso ARW-T024 mostra que esse julgamento pode errar: classificado como alcançável, o trecho se mostrou inalcançável na prática. Esse erro foi mantido de propósito na classificação e reportado no resíduo, em vez de corrigido depois.

**Tamanho do Arrow.** As localidades respondem por 46 dos 123 trechos não cobertos do Arrow e por boa parte dos mutantes. Os resultados do Arrow, e o total agregado, mudam bastante dependendo de `locales.py` ser incluído ou não; vale apresentar os dois recortes no artigo.
