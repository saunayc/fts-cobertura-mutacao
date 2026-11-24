#!/usr/bin/env python3
"""Classificação do Avaliador A (Claude, assistente de IA) — QP2.

Gera classificacao/avaliador_A_<lib>.csv a partir de trechos_<lib>.csv.
Cada entrada: id -> (categoria, alcançável pela API pública, justificativa).
Feita com o código-fonte aberto no contexto de cada trecho, seguindo o
LIVRO_DE_CODIGOS.md e a regra de desempate.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, N = "sim", "nao"

A = {
    # ------------------------------------------------------------ TinyDB
    "TDB-T001": ("LIM", S, "drop_table em banco ainda sem dados gravados (storage vazio)"),
    "TDB-T002": ("LIM", S, "drop_table de tabela inexistente no storage"),
    "TDB-T003": ("LIM", S, "drop_table de tabela nunca aberta nesta instância"),
    "TDB-T004": ("LIM", S, "__exit__ após o banco já ter sido fechado"),
    "TDB-T005": ("OUTRO", S, "delegação de atributos do Middleware ao storage; API auxiliar não especificada nos requisitos"),
    "TDB-T006": ("EXC", S, "except TypeError ao calcular hash de query com argumento não-hashável"),
    "TDB-T007": ("VAL", S, "__eq__ comparando QueryInstance com objeto de outro tipo"),
    "TDB-T008": ("LIM", S, "combinação & com query não cacheável"),
    "TDB-T009": ("LIM", S, "combinação | com query não cacheável"),
    "TDB-T010": ("VAL", S, "rejeita query sem caminho (Query().matches(...) sem campo)"),
    "TDB-T011": ("VAL", S, "matches sobre valor que não é str"),
    "TDB-T012": ("VAL", S, "search sobre valor que não é str"),
    "TDB-T013": ("MORTO", N, "corpo de método abstrato Storage.read"),
    "TDB-T014": ("MORTO", N, "corpo de método abstrato Storage.write"),
    "TDB-T015": ("VAL", S, "aviso para access_mode fora dos valores seguros"),
    "TDB-T016": ("LIM", S, "create_dirs=True com diretório já existente"),
    "TDB-T017": ("CFG", S, "flag persist_empty da tabela"),
    "TDB-T018": ("VAL", S, "insert de documento que não é Mapping"),
    "TDB-T019": ("VAL", S, "insert_multiple com item que não é Mapping"),
    "TDB-T020": ("VAL", S, "get sem cond, doc_id nem doc_ids"),
    "TDB-T021": ("VAL", S, "contains sem cond nem doc_id"),
    "TDB-T022": ("VAL", S, "remove sem cond nem doc_ids"),
    "TDB-T023": ("OUTRO", S, "interface de dicionário do LRUCache (classe utilitária pública) não usada pelo núcleo"),
    "TDB-T024": ("OUTRO", S, "LRUCache.__len__ não usado pelo núcleo"),
    "TDB-T025": ("OUTRO", S, "LRUCache.__contains__ não usado pelo núcleo"),
    "TDB-T026": ("OUTRO", S, "LRUCache.__delitem__ não usado pelo núcleo"),
    "TDB-T027": ("OUTRO", S, "LRUCache.__getitem__ não usado pelo núcleo"),
    "TDB-T028": ("OUTRO", S, "LRUCache.__iter__ não usado pelo núcleo"),
    "TDB-T029": ("OUTRO", S, "LRUCache.set com chave existente; via Table só ocorre após miss"),
    "TDB-T030": ("MORTO", N, "FrozenDict é interno; a biblioteca nunca tenta mutá-lo"),
    "TDB-T031": ("MORTO", N, "FrozenDict.update nunca chamado pela biblioteca"),
    "TDB-T032": ("MORTO", N, "FrozenDict.pop nunca chamado pela biblioteca"),
    "TDB-T033": ("LIM", S, "freeze de tupla (ex.: argumento tupla em Query.test)"),
    "TDB-T034": ("LIM", S, "freeze de set (ex.: argumento set em Query.test)"),
    # ------------------------------------------------------------ Arrow
    "ARW-T001": ("OUTRO", S, "função pública arrow.factory não citada nos requisitos"),
    "ARW-T002": ("CFG", S, "detecção de tzinfo do pytz (dependência opcional)"),
    "ARW-T003": ("CFG", S, "Arrow.now() sem fuso usa o fuso local do sistema"),
    "ARW-T004": ("VAL", S, "utcfromtimestamp com timestamp inválido"),
    "ARW-T005": ("LIM", S, "span_range com fim exatamente no início de um intervalo"),
    "ARW-T006": ("LIM", S, "span_range com fim 1 µs antes do início de um intervalo"),
    "ARW-T007": ("LIM", S, "shift que cai em horário inexistente (transição de horário de verão)"),
    "ARW-T008": ("LIM", S, "humanize com datetime ingênuo como referência"),
    "ARW-T009": ("LIM", S, "granularidade em lista com um único elemento"),
    "ARW-T010": ("LIM", S, "faixa de 10 a 44 segundos no humanize automático"),
    "ARW-T011": ("LIM", S, "arredondamento de mês quando sobram mais de 14 dias"),
    "ARW-T012": ("LIM", S, "granularidade 'second' com diferença menor que 2 s"),
    "ARW-T013": ("VAL", S, "lista de granularidade vazia"),
    "ARW-T014": ("EXC", S, "KeyError de locale sem tradução convertido em ValueError"),
    "ARW-T015": ("VAL", S, "dehumanize com locale válido do Arrow mas não suportado"),
    "ARW-T016": ("CFG", S, "dehumanize em locale cujos timeframes são dicionários"),
    "ARW-T017": ("VAL", S, "is_between com fim que não é Arrow"),
    "ARW-T018": ("OUTRO", S, "Arrow.dst() — delegação a datetime não coberta pelos requisitos"),
    "ARW-T019": ("VAL", S, "__rsub__ com operando de tipo não suportado"),
    "ARW-T020": ("VAL", S, "__gt__ com operando de tipo não suportado"),
    "ARW-T021": ("VAL", S, "__ge__ com operando de tipo não suportado"),
    "ARW-T022": ("VAL", S, "__le__ com operando de tipo não suportado"),
    "ARW-T023": ("EXC", S, "ParserError de fuso traduzido em ValueError"),
    "ARW-T024": ("VAL", S, "start/end de range como timestamp ou tipo inválido"),
    "ARW-T025": ("LIM", S, "nome de unidade no plural em span/range"),
    "ARW-T026": ("LIM", S, "strptime recebendo tzinfo explícito"),
    "ARW-T027": ("LIM", S, "span_range com limite fechado no fim e fim no meio do intervalo"),
    "ARW-T028": ("VAL", S, "acesso a atributo inexistente em Arrow"),
    "ARW-T029": ("LIM", S, "get com vários kwargs repassados ao construtor"),
    "ARW-T030": ("LIM", S, "get com um único kwarg que não é tzinfo"),
    "ARW-T031": ("LIM", S, "get() sem argumentos com tzinfo objeto"),
    "ARW-T032": ("LIM", S, "get com Decimal"),
    "ARW-T033": ("VAL", S, "get(None)"),
    "ARW-T034": ("VAL", S, "get(date, <tipo inválido>)"),
    "ARW-T035": ("LIM", S, "get(timestamp, tzinfo=...)"),
    "ARW-T036": ("LIM", S, "ArrowFactory.now com tzinfo objeto"),
    "ARW-T037": ("LIM", S, "token de formatação SSSSS"),
    "ARW-T038": ("LIM", S, "token de formatação SSSS"),
    "ARW-T039": ("LIM", S, "token casado pela regex mas sem tratamento (ex.: 'YYY')"),
    "ARW-T040": ("OUTRO", S, "função pública get_locale_by_class_name não citada nos requisitos"),
    "ARW-T041": ("VAL", S, "subclasse de Locale com nome duplicado"),
    "ARW-T042": ("MORTO", N, "meridian só é chamado com tokens a/A"),
}
LOCALE_CFG = {f"ARW-T{i:03d}" for i in range(43, 89)} - {"ARW-T044"}
for i in sorted(LOCALE_CFG):
    A[i] = ("CFG", S, "código específico de localidade não exercitada (parâmetro locale)")
A.update({
    "ARW-T044": ("LIM", S, "only_distance com timeframe 'now' no inglês"),
    "ARW-T089": ("CFG", S, "locale sem and_word"),
    "ARW-T090": ("LIM", S, "describe_multi com todos os valores zerados"),
    "ARW-T091": ("LIM", S, "describe_multi com primeiro valor zerado"),
    "ARW-T092": ("LIM", S, "segunda chamada a month_number reaproveita o mapa"),
    "ARW-T093": ("CFG", N, "fallback para backports.zoneinfo em Python < 3.9"),
    "ARW-T094": ("CFG", N, "DateTimeParser com cache_size > 0 (não usado por arrow.get)"),
    "ARW-T095": ("LIM", S, "ISO 8601 com espaço no lugar de 'T'"),
    "ARW-T096": ("VAL", S, "componente de hora inválido em string ISO"),
    "ARW-T097": ("LIM", S, "ISO 8601 só com hora (sem minutos)"),
    "ARW-T098": ("LIM", S, "formatos com separador espaço na interpretação ISO"),
    "ARW-T099": ("EXC", S, "re.error ao gerar padrão convertido em ParserMatchError"),
    "ARW-T100": ("LIM", S, "token Do na interpretação"),
    "ARW-T101": ("MORTO", N, "grupo da regex ausente após casamento bem-sucedido"),
    "ARW-T102": ("EXC", S, "token desconhecido (KeyError) convertido em ParserError"),
    "ARW-T103": ("LIM", S, "token Do define o dia"),
    "ARW-T104": ("LIM", S, "token dddd na interpretação"),
    "ARW-T105": ("LIM", S, "arredondamento de subsegundos com 7º dígito > 5"),
    "ARW-T106": ("VAL", S, "AM com hora maior que 12"),
    "ARW-T107": ("VAL", S, "DDDD sem ano"),
    "ARW-T108": ("VAL", S, "DDDD junto com mês"),
    "ARW-T109": ("EXC", S, "dia do ano inválido (ValueError -> ParserError)"),
    "ARW-T110": ("LIM", S, "dia da semana sem dia do mês"),
    "ARW-T111": ("VAL", S, "24h com minutos"),
    "ARW-T112": ("VAL", S, "24h com segundos"),
    "ARW-T113": ("VAL", S, "24h com microssegundos"),
    "ARW-T114": ("VAL", S, "nenhum formato da lista casa"),
    "ARW-T115": ("MORTO", N, "valor de meridiano sempre é am/pm pela regex"),
    "ARW-T116": ("MORTO", N, "token sempre é um dos tratados"),
    "ARW-T117": ("VAL", S, "lista de formatos esgotada sem casamento"),
    "ARW-T118": ("VAL", S, "next_weekday (inclui validação de 0..6); só usado pelo token dddd"),
    "ARW-T119": ("VAL", S, "is_timestamp com tipo não numérico/str"),
    "ARW-T120": ("VAL", S, "ordinal fora da faixa"),
    "ARW-T121": ("VAL", S, "timestamp grande demais"),
    "ARW-T122": ("VAL", S, "semana ISO fora de 1..53"),
    "ARW-T123": ("VAL", S, "dia ISO fora de 1..7"),
    # ------------------------------------------------------------ Humanize
    "HUM-T001": ("LIM", S, "arredondamento leva ao próximo sufixo (999999 B)"),
    "HUM-T002": ("CFG", N, "módulo carregado sem __spec__ (empacotamento)"),
    "HUM-T003": ("CFG", N, "pasta de locale padrão indeterminável"),
    "HUM-T004": ("VAL", S, "tratamento de NaN e infinitos"),
    "HUM-T005": ("VAL", S, "ordinal de valor não finito"),
    "HUM-T006": ("VAL", S, "intcomma de string não finita"),
    "HUM-T007": ("VAL", S, "intcomma de float não finito"),
    "HUM-T008": ("VAL", S, "intword de valor não finito"),
    "HUM-T009": ("LIM", S, "arredondamento leva à próxima potência no intword"),
    "HUM-T010": ("VAL", S, "apnumber de valor não finito"),
    "HUM-T011": ("VAL", S, "fractional de valor não finito"),
    "HUM-T012": ("VAL", S, "scientific de valor não finito"),
    "HUM-T013": ("VAL", S, "clamp de valor não finito"),
    "HUM-T014": ("VAL", S, "clamp com format que não é str nem função"),
    "HUM-T015": ("VAL", S, "metric de valor não finito"),
    "HUM-T016": ("LIM", S, "arredondamento leva ao próximo prefixo no metric"),
    "HUM-T017": ("LIM", S, "metric com expoente 0..2 (sem prefixo)"),
    "HUM-T018": ("LIM", S, "metric sem unidade e sem prefixo, ou unidade de ângulo"),
    "HUM-T019": ("MORTO", N, "Unit é interno; nunca comparado com outro tipo"),
    "HUM-T020": ("LIM", S, "arredondamento de 59,5+ minutos para 'an hour'"),
    "HUM-T021": ("LIM", S, "arredondamento de 23,5+ horas para 'a day'"),
    "HUM-T022": ("CFG", S, "months=False com menos de um ano"),
    "HUM-T023": ("LIM", S, "um mês, 12 meses ou vários meses"),
    "HUM-T024": ("LIM", S, "1 ano e alguns dias sem mês completo"),
    "HUM-T025": ("LIM", S, "1 ano e 12 meses / 1 ano e vários meses"),
    "HUM-T026": ("LIM", S, "deltas de 2 anos ou mais"),
    "HUM-T027": ("LIM", S, "naturalday com datetime com fuso"),
    "HUM-T028": ("EXC", S, "naturalday com data fora da faixa"),
    "HUM-T029": ("LIM", S, "naturaldate com datetime com fuso"),
    "HUM-T030": ("EXC", S, "naturaldate com valor não-data ou fora da faixa"),
    "HUM-T031": ("VAL", S, "minimum_unit suprimido sem substituto"),
    "HUM-T032": ("LIM", S, "promoção de 1000 ms para 1 s"),
    "HUM-T033": ("LIM", S, "promoção de 60 s para 1 min"),
    "HUM-T034": ("LIM", S, "promoção de 60 min para 1 h"),
    "HUM-T035": ("LIM", S, "promoção de 24 h para 1 dia"),
    "HUM-T036": ("LIM", S, "promoção de 31 dias para 1 mês"),
    "HUM-T037": ("LIM", S, "promoção de 12 meses para 1 ano"),
    "HUM-T038": ("MORTO", N, "laço sempre encontra min_unit e sai por break"),
    "HUM-T039": ("MORTO", N, "laço sempre encontra min_unit e sai por break"),
    "HUM-T040": ("MORTO", N, "anos fracionários só ocorrem quando YEARS é min_unit (ramo anterior)"),
})

if __name__ == "__main__":
    for lib in ("tinydb", "arrow", "humanize"):
        trechos = list(csv.DictReader(open(ROOT / "classificacao" / f"trechos_{lib}.csv")))
        faltando = [t["id"] for t in trechos if t["id"] not in A]
        assert not faltando, faltando
        for nome, preenche in (("avaliador_A", True), ("avaliador_B_EM_BRANCO", False)):
            with open(ROOT / "classificacao" / f"{nome}_{lib}.csv", "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["id", "modulo", "escopo", "linhas", "categoria", "alcancavel", "justificativa"])
                for t in trechos:
                    cat, alc, jus = A[t["id"]] if preenche else ("", "", "")
                    w.writerow([t["id"], t["modulo"], t["escopo"], t["linhas"], cat, alc, jus])
        print(lib, len(trechos), "trechos classificados")
