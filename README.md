# O que os requisitos não alcançam: cobertura estrutural e escore de mutação em projetos Python

Repositório de artefatos do estudo da **Equipe 12** da disciplina Fundamentos de Testes de Software (2026.2): Ana Luisa Feitosa, Luan Romancini, Lucas dos Santos e Saunay Coutinho.

O estudo compara o que uma suíte de testes funcionais (caixa-preta), derivada só da documentação pública, alcança em cobertura estrutural e em escore de mutação, e depois investiga o código que ela deixa de fora. A amostra são três bibliotecas Python puras: [TinyDB](https://github.com/msiemens/tinydb), [Arrow](https://github.com/arrow-py/arrow) e [Humanize](https://github.com/python-humanize/humanize). O trabalho responde a três questões: quanto a suíte funcional cobre (QP1); de que tipo é o código que ela não cobre, numa classificação em cinco categorias com concordância medida pelo Kappa de Cohen (QP2); e quanto testes estruturais direcionados acrescentam em cobertura e em escore de mutação, e o que continua sem cobertura (QP3).

Os números consolidados estão em [`resultados/RESUMO.md`](resultados/RESUMO.md). As decisões tomadas na execução, as divergências entre documentação e comportamento e as ameaças à validade estão em [`protocolo/DECISOES_E_DIVERGENCIAS.md`](protocolo/DECISOES_E_DIVERGENCIAS.md), e a regra de parada da QP3 em [`protocolo/REGRA_DE_PARADA.md`](protocolo/REGRA_DE_PARADA.md).

## Como reproduzir

É preciso Python 3.10 ou mais recente, git e acesso à internet (para clonar as bibliotecas e instalar pacotes). Cada biblioteca ganha um ambiente virtual próprio dentro de `work/`, que não é versionado.

```bash
python3 scripts/prepare.py                 # clona nos commits fixados, monta work/<lib> e os venvs

for lib in tinydb arrow humanize; do
  python3 scripts/measure.py $lib inicial  # QP1: só a suíte funcional (Coverage --branch + mutmut)
done

python3 scripts/extract_uncovered.py       # QP2: lista os trechos não cobertos
python3 scripts/classificacao_avaliador_A.py   # grava a classificação A e as planilhas em branco
python3 scripts/kappa.py --todas           # depois que o(s) avaliador(es) humano(s) preencherem

for lib in tinydb arrow humanize; do
  python3 scripts/measure.py $lib final    # QP3: suíte funcional + estrutural
done

python3 scripts/mutant_lines.py            # localiza a linha de cada mutante e cruza com a cobertura
python3 scripts/analyze.py                 # consolida tudo em resultados/
```

A medição com mutação leva poucos minutos para TinyDB e Humanize e algo em torno de 10 a 15 minutos para o Arrow numa máquina com dois núcleos. Para rodar só a cobertura, acrescente `--sem-mutacao` ao `measure.py`.

## Organização

| Caminho | Conteúdo |
|---|---|
| `subjects.lock.json` | repositório, tag, commit e dependências travadas de cada biblioteca |
| `requisitos/<lib>.csv` | tabela de requisitos extraídos da documentação, com a fonte e a técnica (partição de equivalência / valor-limite) |
| `requisitos/rastreabilidade.csv` | requisito → testes funcionais que o verificam (gerada a partir do marcador `@pytest.mark.req`) |
| `suites/<lib>/functional/` | suíte funcional caixa-preta (QP1) |
| `suites/<lib>/structural/` | testes estruturais direcionados (QP3), cada um marcado com `@pytest.mark.alvo("<trecho>")` |
| `classificacao/LIVRO_DE_CODIGOS.md` | definições operacionais das categorias e regra de desempate, para os avaliadores |
| `classificacao/trechos_<lib>.csv` | trechos não cobertos pela suíte funcional, com o código |
| `classificacao/avaliador_A_<lib>.csv` | classificação do avaliador A |
| `classificacao/avaliador_B_EM_BRANCO_<lib>.csv` | planilha em branco para o segundo avaliador |
| `resultados/inicial/<lib>/`, `resultados/final/<lib>/` | relatórios brutos: `coverage.json`, `modulos.csv`, `projeto.json`, `mutantes.csv`, saída do pytest |
| `resultados/RESUMO.md` e `resultados/qp*.csv` | tabelas consolidadas para o artigo, incluindo as análises complementares (onde sobrevivem os mutantes, Arrow com e sem localidades, hipótese sob diferentes ponderações) |
| `resultados/<fase>/<lib>/mutantes_linhas.csv` | cada mutante com a linha que altera e se o comando foi executado naquela fase |
| `scripts/` | todo o pipeline (preparação, medição, extração, Kappa, análise) |

## Sobre os avaliadores da QP2

As duas classificações (`avaliador_A_<lib>.csv` e `avaliador_B_IA_<lib>.csv`) foram feitas por instâncias independentes de IA (Claude). O Avaliador B trabalhou isolado, sem acesso à classificação A. O Kappa de Cohen entre elas é 0,871. Esse é um desvio declarado do protocolo, que previa avaliadores humanos (ver `protocolo/DECISOES_E_DIVERGENCIAS.md`). Para acrescentar um avaliador humano, copie `classificacao/avaliador_B_EM_BRANCO_<lib>.csv` para `avaliador_B_<lib>.csv`, preencha seguindo o livro de códigos sem consultar as outras planilhas e rode `python3 scripts/kappa.py --todas`. Quando esse arquivo existe, o script passa a usá-lo no lugar da classificação de IA. As divergências para a reunião de consenso ficam em `classificacao/divergencias_todas.csv`. A regra de parada adotada na QP3 é uma proposta padrão que ainda precisa ser validada com a professora.
