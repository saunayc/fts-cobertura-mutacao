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
| `resultados/RESUMO.md` e `resultados/qp*.csv` | tabelas consolidadas para o artigo |
| `scripts/` | todo o pipeline (preparação, medição, extração, Kappa, análise) |

## O que ainda depende da equipe

A classificação A foi produzida por um assistente de IA, e o protocolo pede dois integrantes humanos classificando de forma independente. Para fechar a QP2, cada avaliador copia `classificacao/avaliador_B_EM_BRANCO_<lib>.csv` para `avaliador_B_<lib>.csv` (ou para outro nome, comparando os dois com `scripts/kappa.py <arquivo1> <arquivo2>`), preenche as colunas `categoria`, `alcancavel` e `justificativa` seguindo o livro de códigos e sem olhar a outra planilha, e roda o script do Kappa. O script também gera `divergencias_*.csv` para a reunião de consenso. A regra de parada adotada é uma proposta padrão que ainda precisa ser validada com a professora.
