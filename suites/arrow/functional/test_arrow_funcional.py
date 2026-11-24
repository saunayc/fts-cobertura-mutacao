"""Suíte funcional (caixa-preta) do Arrow.

Derivada do README, do guia do usuário (docs/guide.rst) e da referência de API
publicada (docstrings públicas). Rastreabilidade via ``@pytest.mark.req``.
"""
import time
from datetime import date, datetime, timedelta, timezone

import pytest
from dateutil import tz as dtz

import arrow
from arrow import Arrow

req = pytest.mark.req
UTC = dtz.tzutc()


def A(*args, **kw):
    return arrow.get(*args, **kw)


# ------------------------------------------------------------- criação
@req("ARW-R01")
def test_utcnow_e_now():
    antes = datetime.now(timezone.utc)
    u = arrow.utcnow()
    depois = datetime.now(timezone.utc)
    assert antes <= u.datetime <= depois
    assert u.utcoffset() == timedelta(0)
    p = arrow.now("US/Pacific")
    assert p.utcoffset() in (timedelta(hours=-7), timedelta(hours=-8))
    assert abs((arrow.now() - u).total_seconds()) < 5


@req("ARW-R02")
@pytest.mark.parametrize(
    "ts, esperado",
    [
        (0, "1970-01-01T00:00:00+00:00"),
        (1367900664, "2013-05-07T04:24:24+00:00"),
        (1367900664.152325, "2013-05-07T04:24:24.152325+00:00"),
        (-86400, "1969-12-31T00:00:00+00:00"),
    ],
)
def test_get_timestamp(ts, esperado):
    assert A(ts).isoformat() == esperado


@req("ARW-R02")
def test_fromtimestamp_string_e_tz():
    assert Arrow.fromtimestamp("1367900664", tzinfo="UTC").isoformat() == "2013-05-07T04:24:24+00:00"
    assert Arrow.fromtimestamp(0, "+03:00").hour == 3


@req("ARW-R03")
def test_get_datetime():
    assert A(datetime(2013, 5, 5)).isoformat() == "2013-05-05T00:00:00+00:00"
    assert A(datetime(2013, 5, 5), "US/Pacific").isoformat() == "2013-05-05T00:00:00-07:00"
    assert A(datetime(2013, 5, 5), dtz.gettz("US/Pacific")).isoformat() == "2013-05-05T00:00:00-07:00"
    aware = datetime(2013, 5, 5, 12, tzinfo=dtz.gettz("Europe/Paris"))
    assert A(aware).utcoffset() == timedelta(hours=2)


@req("ARW-R04")
def test_get_com_formato():
    assert A("2013-05-05 12:30:45", "YYYY-MM-DD HH:mm:ss").isoformat() == "2013-05-05T12:30:45+00:00"
    assert A("2013-05-05 12:30:45 America/Chicago", "YYYY-MM-DD HH:mm:ss ZZZ").isoformat() == \
        "2013-05-05T12:30:45-05:00"
    assert A("05/05/2013", ["YYYY-MM-DD", "MM/DD/YYYY"]).isoformat() == "2013-05-05T00:00:00+00:00"


@req("ARW-R04")
def test_get_com_formato_e_tzinfo():
    a = A("2013-05-05 12:30", "YYYY-MM-DD HH:mm", tzinfo="Asia/Tokyo")
    assert a.utcoffset() == timedelta(hours=9)


@req("ARW-R05")
def test_busca_data_em_texto():
    assert A("June was born in May 1980", "MMMM YYYY").isoformat() == "1980-05-01T00:00:00+00:00"


@req("ARW-R06")
@pytest.mark.parametrize(
    "s, esperado",
    [
        ("2013-05-11T21:23:58.970460+07:00", "2013-05-11T21:23:58.970460+07:00"),
        ("2013-09-30T15:34:00.000-07:00", "2013-09-30T15:34:00-07:00"),
        ("2013-09-29T01:26:43.830580", "2013-09-29T01:26:43.830580+00:00"),
        ("20160413T133656.456289", "2016-04-13T13:36:56.456289+00:00"),
        ("2013-05-05", "2013-05-05T00:00:00+00:00"),
        ("2013-05-05T12:30Z", "2013-05-05T12:30:00+00:00"),
        ("2013-W18-7", "2013-05-05T00:00:00+00:00"),
        ("2013-125", "2013-05-05T00:00:00+00:00"),
    ],
)
def test_iso8601_sem_formato(s, esperado):
    assert A(s).isoformat() == esperado


@req("ARW-R07")
def test_instanciacao_direta():
    assert A(2013, 5, 5).isoformat() == "2013-05-05T00:00:00+00:00"
    assert Arrow(2013, 5, 5).isoformat() == "2013-05-05T00:00:00+00:00"
    assert Arrow(2013, 5, 5, 1, 2, 3, 4, tzinfo="+01:00").isoformat() == "2013-05-05T01:02:03.000004+01:00"
    assert abs((A() - arrow.utcnow()).total_seconds()) < 5


@req("ARW-R08")
def test_get_outras_entradas():
    a = A(2013, 5, 5, 10)
    copia = A(a)
    assert copia == a and copia is not a
    assert A(date(2013, 5, 5)).isoformat() == "2013-05-05T00:00:00+00:00"
    assert A(date(2013, 5, 5), "US/Pacific").isoformat() == "2013-05-05T00:00:00-07:00"
    assert A(time.gmtime(0)).isoformat() == "1970-01-01T00:00:00+00:00"
    assert A((2013, 18, 7)).isoformat() == "2013-05-05T00:00:00+00:00"
    assert A(dtz.gettz("Asia/Tokyo")).utcoffset() == timedelta(hours=9)
    assert A(tzinfo="Asia/Tokyo").utcoffset() == timedelta(hours=9)


# ------------------------------------------------------------- propriedades
@req("ARW-R09")
def test_propriedades():
    a = A("2013-05-07T04:38:15.447644+00:00")
    assert a.datetime == datetime(2013, 5, 7, 4, 38, 15, 447644, tzinfo=a.tzinfo)
    assert a.naive == datetime(2013, 5, 7, 4, 38, 15, 447644)
    assert a.utcoffset() == timedelta(0)
    assert (a.year, a.month, a.day, a.hour, a.minute, a.second, a.microsecond) == (2013, 5, 7, 4, 38, 15, 447644)
    assert a.date() == date(2013, 5, 7)
    assert a.time().hour == 4
    assert a.timetz().tzinfo is not None
    assert a.int_timestamp == 1367901495
    assert a.float_timestamp == pytest.approx(1367901495.447644)
    assert a.timestamp() == pytest.approx(1367901495.447644)
    assert a.week == 19 and a.quarter == 2


# ------------------------------------------------------------- replace / shift
@req("ARW-R10")
def test_replace():
    a = A("2013-05-12T03:29:35.334214+00:00")
    assert a.replace(hour=4, minute=40).isoformat() == "2013-05-12T04:40:35.334214+00:00"
    assert a.replace(tzinfo="US/Pacific").isoformat() == "2013-05-12T03:29:35.334214-07:00"
    assert a.replace(year=2014, month=6).isoformat().startswith("2014-06-12")


@req("ARW-R10")
def test_replace_com_atributo_plural_e_erro():
    with pytest.raises(ValueError):
        A(2013, 5, 5).replace(hours=1)
    with pytest.raises(ValueError):
        A(2013, 5, 5).replace(week=1)


@req("ARW-R11")
@pytest.mark.parametrize(
    "kw, esperado",
    [
        ({"weeks": 3}, "2013-06-02T03:29:35+00:00"),
        ({"years": 1, "months": -1}, "2014-04-12T03:29:35+00:00"),
        ({"days": -12}, "2013-04-30T03:29:35+00:00"),
        ({"hours": 21}, "2013-05-13T00:29:35+00:00"),
        ({"minutes": -30, "seconds": 25}, "2013-05-12T03:00:00+00:00"),
        ({"microseconds": 1}, "2013-05-12T03:29:35.000001+00:00"),
        ({"quarters": 1}, "2013-08-12T03:29:35+00:00"),
    ],
)
def test_shift(kw, esperado):
    assert A("2013-05-12T03:29:35+00:00").shift(**kw).isoformat() == esperado


@req("ARW-R11")
@pytest.mark.parametrize(
    "inicio, kw, esperado",
    [
        ("2013-01-31", {"months": 1}, "2013-02-28"),   # fim de mês, ano comum
        ("2012-01-31", {"months": 1}, "2012-02-29"),   # ano bissexto
        ("2012-02-29", {"years": 1}, "2013-02-28"),
        ("2012-02-29", {"years": 4}, "2016-02-29"),
        ("2013-12-31", {"days": 1}, "2014-01-01"),
    ],
)
def test_shift_valor_limite(inicio, kw, esperado):
    assert A(inicio).shift(**kw).format("YYYY-MM-DD") == esperado


@req("ARW-R11")
def test_shift_weekday():
    sab = A("2013-05-11T22:27:34+00:00")
    assert sab.shift(weekday=5) == sab
    assert sab.shift(weekday=0).format("YYYY-MM-DD") == "2013-05-13"
    from dateutil.relativedelta import MO
    assert sab.shift(weekday=MO(-1)).format("YYYY-MM-DD") == "2013-05-06"


@req("ARW-R11")
def test_shift_argumento_invalido():
    with pytest.raises(ValueError):
        A(2013, 5, 5).shift(hour=1)
    with pytest.raises((ValueError, IndexError, TypeError)):
        A(2013, 5, 5).shift(weekday=7)


@req("ARW-R12")
def test_horario_ambiguo():
    p = Arrow(2019, 10, 27, 2, tzinfo="Europe/Paris", fold=0)
    assert p.ambiguous is True
    assert p.isoformat() == "2019-10-27T02:00:00+02:00"
    assert p.replace(fold=1).isoformat() == "2019-10-27T02:00:00+01:00"
    assert Arrow(2019, 7, 1, 2, tzinfo="Europe/Paris").ambiguous is False
    assert p.fold == 0


@req("ARW-R12")
def test_horario_inexistente_e_imaginario():
    p = Arrow(2019, 3, 31, 2, 30, tzinfo="Europe/Paris")
    assert p.imaginary is True or p.hour == 3
    assert Arrow(2019, 7, 1, tzinfo="Europe/Paris").imaginary is False


# ------------------------------------------------------------- format
@req("ARW-R13")
@pytest.mark.parametrize(
    "fmt, esperado",
    [
        ("YYYY", "2013"), ("YY", "13"),
        ("MMMM", "May"), ("MMM", "May"), ("MM", "05"), ("M", "5"),
        ("DDDD", "125"), ("DDD", "125"), ("DD", "05"), ("D", "5"), ("Do", "5th"),
        ("dddd", "Sunday"), ("ddd", "Sun"), ("d", "7"),
        ("HH", "08"), ("H", "8"), ("hh", "08"), ("h", "8"),
        ("A", "AM"), ("a", "am"),
        ("mm", "07"), ("m", "7"), ("ss", "09"), ("s", "9"),
        ("S", "1"), ("SS", "12"), ("SSS", "123"), ("SSSSSS", "123456"),
        ("ZZ", "+00:00"), ("Z", "+0000"),
        ("W", "2013-W18-7"),
    ],
)
def test_format_tokens(fmt, esperado):
    a = A("2013-05-05T08:07:09.123456+00:00")
    assert a.format(fmt) == esperado


@req("ARW-R13")
@pytest.mark.parametrize("dia, sufixo", [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
                                         (11, "11th"), (12, "12th"), (13, "13th"),
                                         (21, "21st"), (22, "22nd"), (23, "23rd"), (31, "31st")])
def test_format_ordinal_dia(dia, sufixo):
    assert A(2013, 1, dia).format("Do") == sufixo


@req("ARW-R13")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-03: README mostra format() == "
                   "'2013-05-11 13:23:58 -07:00' (com espaço antes do fuso)")
def test_format_padrao_conforme_readme():
    assert A("2013-05-11T13:23:58-07:00").format() == "2013-05-11 13:23:58 -07:00"


@req("ARW-R13")
def test_format_timestamp_x_fracionario():
    assert A(1381685817.915482).format("X") == "1381685817.915482"


@req("ARW-R13")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-05 (ambígua): a tabela de tokens lista '1381685817' "
                   "como saída de X, mas um timestamp inteiro é formatado como '1367741229.0'")
def test_format_timestamp_x_inteiro():
    assert A(1367741229).format("X") == "1367741229"


@req("ARW-R13")
def test_format_padrao_e_tarde_e_zzz():
    a = A("2013-05-11T13:23:58-07:00")
    assert a.format("YYYY-MM-DD HH:mm:ss ZZ") == "2013-05-11 13:23:58 -07:00"
    assert a.format("h A") == "1 PM"
    assert a.format("hh") == "01"
    assert A(2013, 5, 5, 0).format("h a") == "12 am"
    assert A(2013, 5, 5).to("US/Pacific").format("ZZZ") in ("PDT", "US/Pacific")
    assert A(2013, 5, 5).format("x") == "1367712000000000"


@req("ARW-R14")
def test_formatos_predefinidos():
    a = A("2020-05-27T10:30:35+00:00")
    assert a.format(arrow.FORMAT_ATOM) == "2020-05-27 10:30:35+00:00"
    assert a.format(arrow.FORMAT_COOKIE) == "Wednesday, 27-May-2020 10:30:35 UTC"
    assert a.format(arrow.FORMAT_RSS) == "Wed, 27 May 2020 10:30:35 +0000"
    assert a.format(arrow.FORMAT_RFC822) == "Wed, 27 May 20 10:30:35 +0000"
    assert a.format(arrow.FORMAT_RFC850) == "Wednesday, 27-May-20 10:30:35 UTC"
    assert a.format(arrow.FORMAT_RFC1036) == "Wed, 27 May 20 10:30:35 +0000"
    assert a.format(arrow.FORMAT_RFC1123) == "Wed, 27 May 2020 10:30:35 +0000"
    assert a.format(arrow.FORMAT_RFC2822) == "Wed, 27 May 2020 10:30:35 +0000"
    assert a.format(arrow.FORMAT_RFC3339) == "2020-05-27 10:30:35+00:00"
    assert a.format(arrow.FORMAT_W3C) == "2020-05-27 10:30:35+00:00"


@req("ARW-R15")
@pytest.mark.parametrize("fmt, texto", [
    ("YYYY-MM-DD h [h] m", "2018-03-09 8 h 40"),
    ("YYYY-MM-DD h [hello] m", "2018-03-09 8 hello 40"),
    ("YYYY-MM-DD h [hello world] m", "2018-03-09 8 hello world 40"),
])
def test_escape_tokens(fmt, texto):
    a = A(texto, fmt)
    assert a.isoformat() == "2018-03-09T08:40:00+00:00"
    assert a.format(fmt) == texto


@req("ARW-R15")
@pytest.mark.parametrize("texto", ["Mon Sep 08 16:41:45 2014", "Mon \tSep 08   16:41:45     2014"])
def test_escape_regex(texto):
    fmt = r"ddd[\s+]MMM[\s+]DD[\s+]HH:mm:ss[\s+]YYYY"
    assert A(texto, fmt).isoformat() == "2014-09-08T16:41:45+00:00"


@req("ARW-R16")
def test_pontuacao_valida():
    assert A("Cool date: 2019-10-31T09:12:45.123456+04:30.", "YYYY-MM-DDTHH:mm:ss.SZZ").isoformat() == \
        "2019-10-31T09:12:45.123456+04:30"
    assert A("Tomorrow (2019-10-31) is Halloween!", "YYYY-MM-DD").day == 31
    assert A("Halloween is on 2019.10.31.", "YYYY.MM.DD").day == 31


@req("ARW-R16")
def test_pontuacao_dupla_invalida():
    with pytest.raises(arrow.parser.ParserError):
        A("It's Halloween tomorrow (2019-10-31)!", "YYYY-MM-DD")


@req("ARW-R17")
def test_normalize_whitespace():
    assert A("\t \n  2013-05-05T12:30:45.123456 \t \n", normalize_whitespace=True).isoformat() == \
        "2013-05-05T12:30:45.123456+00:00"
    assert A("2013-05-05  T \n   12:30:45\t123456", "YYYY-MM-DD T HH:mm:ss S",
             normalize_whitespace=True).isoformat() == "2013-05-05T12:30:45.123456+00:00"


@req("ARW-R17")
def test_sem_normalize_whitespace_falha():
    with pytest.raises(arrow.parser.ParserError):
        A("\t \n  2013-05-05T12:30:45.123456 \t \n")


# ------------------------------------------------------------- conversão
@req("ARW-R18")
def test_to():
    u = A("2013-05-07T05:24:11.823627+00:00")
    assert u.to("US/Pacific").isoformat() == "2013-05-06T22:24:11.823627-07:00"
    assert u.to(dtz.gettz("US/Pacific")).isoformat() == "2013-05-06T22:24:11.823627-07:00"
    assert u.to("-07:00").hour == 22
    assert u.to("local").to("utc") == u
    assert u.to("local").to("UTC").utcoffset() == timedelta(0)


# ------------------------------------------------------------- humanize
BASE = A("2013-05-05T12:00:00+00:00")


@req("ARW-R19")
@pytest.mark.parametrize(
    "delta, esperado",
    [
        ({"seconds": 0}, "just now"),
        ({"seconds": -5}, "just now"),
        ({"minutes": -1}, "a minute ago"),
        ({"minutes": -10}, "10 minutes ago"),
        ({"hours": -1}, "an hour ago"),
        ({"hours": -2}, "2 hours ago"),
        ({"hours": -24}, "a day ago"),
        ({"days": -2}, "2 days ago"),
        ({"days": -7}, "a week ago"),
        ({"days": -14}, "2 weeks ago"),
        ({"months": -1}, "a month ago"),
        ({"months": -2}, "2 months ago"),
        ({"years": -1}, "a year ago"),
        ({"years": -3}, "3 years ago"),
        ({"hours": 2}, "in 2 hours"),
        ({"days": 3}, "in 3 days"),
    ],
)
def test_humanize_auto(delta, esperado):
    assert BASE.shift(**delta).humanize(BASE) == esperado


@req("ARW-R19")
def test_humanize_relativo_ao_agora_e_datetime():
    assert arrow.utcnow().shift(hours=-1).humanize() == "an hour ago"
    assert BASE.shift(hours=2).humanize(BASE.datetime) == "in 2 hours"


@req("ARW-R19")
def test_humanize_only_distance_e_granularidade():
    futuro = BASE.shift(minutes=66)
    assert futuro.humanize(BASE, only_distance=True) == "an hour"
    assert futuro.humanize(BASE, granularity="minute") == "in 66 minutes"
    assert futuro.humanize(BASE, granularity=["hour", "minute"]) == "in an hour and 6 minutes"
    assert BASE.humanize(futuro, granularity=["hour", "minute"]) == "an hour and 6 minutes ago"
    assert futuro.humanize(BASE, only_distance=True, granularity=["hour", "minute"]) == "an hour and 6 minutes"


@req("ARW-R19")
@pytest.mark.parametrize("gran, esperado", [
    ("second", "in 93600 seconds"), ("minute", "in 1560 minutes"), ("hour", "in 26 hours"),
    ("day", "in a day"), ("week", "in 0 weeks"), ("month", "in 0 months"),
    ("quarter", "in 0 quarters"), ("year", "in 0 years"),
])
def test_humanize_granularidade_unidades(gran, esperado):
    assert BASE.shift(hours=26).humanize(BASE, granularity=gran) == esperado


@req("ARW-R19")
def test_humanize_granularidade_invalida():
    with pytest.raises(ValueError):
        BASE.humanize(BASE, granularity="decade")
    with pytest.raises(ValueError):
        BASE.humanize(BASE, granularity=["hour", "decade"])


@req("ARW-R19")
def test_humanize_outro_tipo_invalido():
    with pytest.raises(TypeError):
        BASE.humanize("ontem")


@req("ARW-R20")
@pytest.mark.parametrize("locale, trecho", [
    ("ko-kr", "한시간 전"), ("pt-br", "hora"), ("es", "hora"), ("de", "Stunde"), ("fr", "heure"),
])
def test_humanize_localidades(locale, trecho):
    # Só o exemplo ko-kr está na documentação; nas demais verifica-se a palavra-chave da unidade.
    assert trecho in BASE.shift(hours=-1).humanize(BASE, locale=locale)


@req("ARW-R20")
def test_humanize_localidade_inexistente():
    with pytest.raises(ValueError):
        BASE.humanize(BASE, locale="xx-yy")


# ------------------------------------------------------------- dehumanize
@req("ARW-R21")
@pytest.mark.parametrize("texto, delta", [
    ("2 days ago", {"days": -2}),
    ("in a month", {"months": 1}),
    ("an hour ago", {"hours": -1}),
    ("in 3 weeks", {"weeks": 3}),
    ("5 seconds ago", {"seconds": -5}),
    ("in 2 years", {"years": 2}),
    ("just now", {}),
])
def test_dehumanize(texto, delta):
    assert BASE.dehumanize(texto) == BASE.shift(**delta)


@req("ARW-R21")
def test_dehumanize_localidade():
    assert BASE.dehumanize("एक माह बाद", locale="hi") == BASE.shift(months=1)


@req("ARW-R21")
@pytest.mark.parametrize("texto", ["amanhã de manhã", "2 days"])
def test_dehumanize_invalido(texto):
    with pytest.raises(ValueError):
        BASE.dehumanize(texto)


@req("ARW-R21")
def test_dehumanize_localidade_invalida():
    with pytest.raises(ValueError):
        BASE.dehumanize("2 days ago", locale="xx")


# ------------------------------------------------------------- spans / ranges
M = A("2013-05-09T03:32:36.186203+00:00")


@req("ARW-R22")
@pytest.mark.parametrize("frame, ini, fim", [
    ("year", "2013-01-01T00:00:00+00:00", "2013-12-31T23:59:59.999999+00:00"),
    ("quarter", "2013-04-01T00:00:00+00:00", "2013-06-30T23:59:59.999999+00:00"),
    ("month", "2013-05-01T00:00:00+00:00", "2013-05-31T23:59:59.999999+00:00"),
    ("week", "2013-05-06T00:00:00+00:00", "2013-05-12T23:59:59.999999+00:00"),
    ("day", "2013-05-09T00:00:00+00:00", "2013-05-09T23:59:59.999999+00:00"),
    ("hour", "2013-05-09T03:00:00+00:00", "2013-05-09T03:59:59.999999+00:00"),
    ("minute", "2013-05-09T03:32:00+00:00", "2013-05-09T03:32:59.999999+00:00"),
    ("second", "2013-05-09T03:32:36+00:00", "2013-05-09T03:32:36.999999+00:00"),
])
def test_span(frame, ini, fim):
    s, e = M.span(frame)
    assert (s.isoformat(), e.isoformat()) == (ini, fim)
    assert M.floor(frame) == s and M.ceil(frame) == e


@req("ARW-R22")
def test_span_week_start_count_bounds_exact():
    assert M.floor("week", week_start=7).format("YYYY-MM-DD") == "2013-05-05"
    assert M.ceil("week", week_start=7).format("YYYY-MM-DD") == "2013-05-11"
    s, e = M.span("day", count=2)
    assert e.format("YYYY-MM-DD") == "2013-05-10"
    s, e = M.span("hour", bounds="[]")
    assert e.isoformat() == "2013-05-09T04:00:00+00:00"
    s, e = M.span("hour", bounds="()")
    assert s.isoformat() == "2013-05-09T03:00:00.000001+00:00"
    s, e = M.span("hour", exact=True)
    assert s == M and e == M.shift(hours=1, microseconds=-1)


@req("ARW-R22")
@pytest.mark.parametrize("ws", [0, 8])
def test_span_week_start_invalido(ws):
    with pytest.raises(ValueError):
        M.span("week", week_start=ws)


@req("ARW-R22")
def test_span_frame_invalido():
    with pytest.raises(ValueError):
        M.span("decade")


@req("ARW-R23")
def test_span_range_e_range():
    start, end = datetime(2013, 5, 5, 12, 30), datetime(2013, 5, 5, 17, 15)
    spans = list(Arrow.span_range("hour", start, end))
    assert spans[0][0].isoformat() == "2013-05-05T12:00:00+00:00"
    pontos = list(Arrow.range("hour", start, end))
    assert [p.hour for p in pontos] == [12, 13, 14, 15, 16]
    assert pontos[0].minute == 30


@req("ARW-R23")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-04: o guia mostra 5 intervalos (12h..16h) para "
                   "span_range('hour', 12:30, 17:15); a biblioteca inclui também o das 17h")
def test_span_range_conforme_guia():
    spans = list(Arrow.span_range("hour", datetime(2013, 5, 5, 12, 30), datetime(2013, 5, 5, 17, 15)))
    assert len(spans) == 5
    assert spans[-1][1].isoformat() == "2013-05-05T16:59:59.999999+00:00"


@req("ARW-R23")
@pytest.mark.parametrize("limit, n", [(0, 0), (1, 1), (3, 3)])
def test_range_limit(limit, n):
    assert len(list(Arrow.range("day", datetime(2013, 1, 1), limit=limit))) == n


@req("ARW-R23")
def test_range_tz_meses_e_fim_de_mes():
    pts = list(Arrow.range("month", datetime(2013, 1, 31), datetime(2013, 4, 30), tz="US/Pacific"))
    assert [p.format("MM-DD") for p in pts] == ["01-31", "02-28", "03-31", "04-30"]
    assert pts[0].utcoffset() == timedelta(hours=-8)
    semanas = list(Arrow.range("week", datetime(2013, 1, 1), datetime(2013, 1, 22)))
    assert len(semanas) == 4
    q = list(Arrow.range("quarter", datetime(2013, 1, 1), datetime(2013, 12, 31)))
    assert len(q) == 4


@req("ARW-R23")
def test_span_range_limit_tz_bounds_exact():
    s = list(Arrow.span_range("day", datetime(2013, 1, 1), datetime(2013, 1, 10), limit=2, tz="Asia/Tokyo"))
    assert len(s) == 2 and s[0][0].utcoffset() == timedelta(hours=9)
    s = list(Arrow.span_range("hour", datetime(2013, 1, 1, 0, 30), datetime(2013, 1, 1, 2, 15), exact=True))
    assert s[0][0].minute == 30 and s[-1][1].minute == 14
    s = list(Arrow.span_range("hour", datetime(2013, 1, 1), datetime(2013, 1, 1, 1), bounds="[]"))
    assert s[0][1].minute == 0


@req("ARW-R23")
def test_range_sem_fim_e_sem_limite():
    with pytest.raises(ValueError):
        list(Arrow.range("day", datetime(2013, 1, 1)))


@req("ARW-R24")
def test_interval():
    iv = list(Arrow.interval("hour", datetime(2013, 5, 5, 12, 30), datetime(2013, 5, 5, 17, 15), 2))
    assert len(iv) == 3
    assert iv[0][0].hour == 12 and iv[0][1].hour == 13
    iv = list(Arrow.interval("hour", datetime(2013, 5, 5, 12, 30), datetime(2013, 5, 5, 17, 15), 2, exact=True))
    assert iv[0][0].minute == 30
    iv = list(Arrow.interval("day", datetime(2013, 5, 5), datetime(2013, 5, 6), bounds="[]"))
    assert iv[0][1].hour == 0


@req("ARW-R24")
def test_interval_invalido():
    with pytest.raises(ValueError):
        list(Arrow.interval("hour", datetime(2013, 5, 5), datetime(2013, 5, 6), 0))


@req("ARW-R25")
@pytest.mark.parametrize("instante, bounds, esperado", [
    (datetime(2013, 5, 5, 12, 30, 27), "()", True),
    (datetime(2013, 5, 5, 12, 30, 10), "()", False),
    (datetime(2013, 5, 5, 12, 30, 10), "[)", True),
    (datetime(2013, 5, 5, 12, 30, 36), "[)", False),
    (datetime(2013, 5, 5, 12, 30, 36), "(]", True),
    (datetime(2013, 5, 5, 12, 30, 10), "(]", False),
    (datetime(2013, 5, 5, 12, 30, 36), "[]", True),
    (datetime(2013, 5, 5, 12, 30, 9), "[]", False),
    (datetime(2013, 5, 5, 12, 30, 37), "[]", False),
])
def test_is_between(instante, bounds, esperado):
    start = A(datetime(2013, 5, 5, 12, 30, 10))
    end = A(datetime(2013, 5, 5, 12, 30, 36))
    assert A(instante).is_between(start, end, bounds) is esperado


@req("ARW-R25")
def test_is_between_entradas_invalidas():
    s, e = A(2013, 1, 1), A(2013, 1, 2)
    with pytest.raises(ValueError):
        A(2013, 1, 1, 12).is_between(s, e, "[[")
    with pytest.raises(TypeError):
        A(2013, 1, 1, 12).is_between(datetime(2013, 1, 1), e)


@req("ARW-R26")
def test_factory_tipo_derivado():
    class CustomArrow(Arrow):
        def days_till_xmas(self):
            xmas = Arrow(self.year, 12, 25)
            if self > xmas:
                xmas = xmas.shift(years=1)
            return (xmas - self).days

    factory = arrow.ArrowFactory(CustomArrow)
    c = factory.get(2013, 12, 20)
    assert isinstance(c, CustomArrow)
    assert c.days_till_xmas() == 5
    assert isinstance(factory.utcnow(), CustomArrow)
    assert isinstance(factory.now("Asia/Tokyo"), CustomArrow)
    assert "CustomArrow" in repr(c)


@req("ARW-R27")
def test_construtores_alternativos():
    assert Arrow.fromdatetime(datetime(2013, 5, 5, 1), "US/Pacific").utcoffset() == timedelta(hours=-7)
    assert Arrow.fromdatetime(datetime(2013, 5, 5, 1)).utcoffset() == timedelta(0)
    assert Arrow.fromdate(date(2013, 5, 5)).isoformat() == "2013-05-05T00:00:00+00:00"
    assert Arrow.fromordinal(737741).isoformat() == "2020-11-12T00:00:00+00:00"
    assert Arrow.strptime("20-01-2019 15:49:10", "%d-%m-%Y %H:%M:%S").isoformat() == "2019-01-20T15:49:10+00:00"
    assert Arrow.strptime("2019 +0300", "%Y %z").utcoffset() == timedelta(hours=3)
    assert Arrow.utcfromtimestamp(0).isoformat() == "1970-01-01T00:00:00+00:00"
    assert Arrow.utcnow().utcoffset() == timedelta(0)
    assert Arrow.now(dtz.gettz("Asia/Tokyo")).utcoffset() == timedelta(hours=9)


@req("ARW-R27")
def test_fromordinal_invalido():
    with pytest.raises((TypeError, ValueError)):
        Arrow.fromordinal(1.5)


@req("ARW-R28")
def test_aritmetica_e_comparacao():
    a, b = A(2013, 5, 5), A(2013, 5, 6)
    assert a + timedelta(days=1) == b
    assert timedelta(days=1) + a == b
    assert b - timedelta(days=1) == a
    assert b - a == timedelta(days=1)
    assert b - datetime(2013, 5, 5, tzinfo=UTC) == timedelta(days=1)
    assert datetime(2013, 5, 6, tzinfo=UTC) - a == timedelta(days=1)
    assert a < b and b > a and a <= a and b >= b and a != b
    assert a == datetime(2013, 5, 5, tzinfo=UTC)
    assert (a == "x") is False and (a != "x") is True
    with pytest.raises(TypeError):
        a < "x"
    with pytest.raises(TypeError):
        a + 1
    with pytest.raises(TypeError):
        a - "x"
    assert hash(a) == hash(A(2013, 5, 5))


@req("ARW-R29")
def test_interoperabilidade_datetime():
    a = A("2019-01-19T18:25:36.760079+00:00")
    assert a.for_json() == "2019-01-19T18:25:36.760079+00:00"
    assert a.isoformat(sep=" ", timespec="seconds") == "2019-01-19 18:25:36+00:00"
    assert a.weekday() == 5 and a.isoweekday() == 6
    assert tuple(a.isocalendar())[:2] == (2019, 3)
    assert a.ctime() == "Sat Jan 19 18:25:36 2019"
    assert a.strftime("%Y/%m/%d") == "2019/01/19"
    assert a.toordinal() == date(2019, 1, 19).toordinal()
    assert a.utcoffset() == timedelta(0)
    assert a.timetuple().tm_year == 2019 and a.utctimetuple().tm_hour == 18
    assert a.astimezone(dtz.gettz("Asia/Tokyo")).hour == 3
    assert str(a) == a.isoformat()
    assert repr(a) == "<Arrow [2019-01-19T18:25:36.760079+00:00]>"
    assert format(a, "YYYY") == "2019" and format(a, "") == str(a)
    assert a.clone() == a and a.clone() is not a
    assert Arrow.min < a < Arrow.max and a.resolution == timedelta(microseconds=1)


@req("ARW-R30")
@pytest.mark.parametrize("args", [
    ("2013-13-01", "YYYY-MM-DD"),
    ("2013-02-30", "YYYY-MM-DD"),
    ("abc", "YYYY"),
    ("2013-05-05 25:00", "YYYY-MM-DD HH:mm"),
    ("not a date",),
    ("2013-05-05T12:30:45+99:99",),
])
def test_entradas_invalidas_parser(args):
    with pytest.raises((arrow.parser.ParserError, ValueError)):
        A(*args)


@req("ARW-R30")
def test_tipos_e_fusos_invalidos():
    with pytest.raises(TypeError):
        A(object())
    with pytest.raises(TypeError):
        A([2013, 5, 5])
    with pytest.raises((arrow.parser.ParserError, ValueError)):
        A(2013, 5, 5).to("Mars/Olympus")
    with pytest.raises(TypeError):
        A("2013-05-05", 123)
    with pytest.raises(TypeError):
        A(datetime(2013, 5, 5), 123)
    with pytest.raises(ValueError):
        Arrow.fromtimestamp("abc")


@req("ARW-R31")
@pytest.mark.parametrize("texto, fmt, esperado", [
    ("1381685817", "X", "2013-10-13T17:36:57+00:00"),
    ("1381685817.915482", "X", "2013-10-13T17:36:57.915482+00:00"),
    ("1569980330813", "x", "2019-10-02T01:38:50.813000+00:00"),
    ("1569980330813221", "x", "2019-10-02T01:38:50.813221+00:00"),
    ("2011-W05-4", "W", "2011-02-03T00:00:00+00:00"),
    ("2019-W17", "W", "2019-04-22T00:00:00+00:00"),
    ("2013-125", "YYYY-DDDD", "2013-05-05T00:00:00+00:00"),
    ("2013-1", "YYYY-DDD", "2013-01-01T00:00:00+00:00"),
    ("2013-05-05 Europe/Warsaw", "YYYY-MM-DD ZZZ", "2013-05-05T00:00:00+02:00"),
    ("2013-05-05 +0530", "YYYY-MM-DD Z", "2013-05-05T00:00:00+05:30"),
    ("2013-05-05 Z", "YYYY-MM-DD ZZ", "2013-05-05T00:00:00+00:00"),
    ("12:30:45.1234565", "HH:mm:ss.S", "0001-01-01T12:30:45.123456+00:00"),
    ("12:30:45.1234575", "HH:mm:ss.S", "0001-01-01T12:30:45.123458+00:00"),
    ("12:30:45.9999995", "HH:mm:ss.S", "0001-01-01T12:30:46+00:00"),
    ("5 May 13", "D MMM YY", "2013-05-05T00:00:00+00:00"),
    ("5 May 69", "D MMM YY", "1969-05-05T00:00:00+00:00"),
    ("1 PM", "h A", "0001-01-01T13:00:00+00:00"),
    ("12 am", "h a", "0001-01-01T00:00:00+00:00"),
    ("24:00", "HH:mm", "0001-01-02T00:00:00+00:00"),
])
def test_tokens_interpretacao(texto, fmt, esperado):
    assert A(texto, fmt).isoformat() == esperado


@req("ARW-R31")
def test_x_em_texto_natural_nao_suportado():
    with pytest.raises(arrow.parser.ParserError):
        A("time 1381685817 here", "X")


@req("ARW-R32")
def test_localizacao_interpretacao_e_formatacao():
    a = A("5 mayo 2013", "D MMMM YYYY", locale="es")
    assert a.month == 5
    assert A(2013, 5, 5).format("dddd D MMMM", locale="pt-br").lower() == "domingo 5 maio"
    assert A(2013, 5, 5).format("MMMM", locale="de") == "Mai"
    assert A(2013, 5, 5, 15).format("A", locale="en") == "PM"
    assert A("15 de janeiro de 2020", "D [de] MMMM [de] YYYY", locale="pt").month == 1
