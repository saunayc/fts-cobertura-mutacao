"""Suíte estrutural (caixa-branca) do Arrow — QP3.

Cada teste mira trechos não cobertos pela suíte funcional
(``classificacao/trechos_arrow.csv``), marcados com ``@pytest.mark.alvo``.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from dateutil import tz as dtz

import arrow
from arrow import Arrow, locales, parser, util

alvo = pytest.mark.alvo
BASE = arrow.get("2013-05-05T12:00:00+00:00")


@alvo("ARW-T001")
def test_factory_funcao():
    class C(Arrow):
        pass
    # Observação: o nome ``arrow.factory`` resolve para o *módulo* factory, não para a
    # função documentada; a função só é alcançável como ``arrow.api.factory``.
    assert isinstance(arrow.api.factory(C).get(2013, 1, 1), C)


@alvo("ARW-T002")
def test_tzinfo_estilo_pytz():
    class PytzLike(timezone.__base__):   # datetime.tzinfo
        zone = "Asia/Tokyo"

        def localize(self, dt):
            return dt

        def utcoffset(self, dt):
            return timedelta(0)

    assert Arrow(2013, 5, 5, tzinfo=PytzLike()).utcoffset() == timedelta(hours=9)


@alvo("ARW-T003")
@alvo("ARW-T036")
def test_now_fuso_local_e_objeto():
    assert Arrow.now().tzinfo is not None
    assert arrow.ArrowFactory().now(dtz.gettz("Asia/Tokyo")).utcoffset() == timedelta(hours=9)


@alvo("ARW-T004")
def test_utcfromtimestamp_invalido():
    with pytest.raises(ValueError):
        Arrow.utcfromtimestamp("abc")


@alvo("ARW-T005")
@alvo("ARW-T006")
@alvo("ARW-T027")
def test_span_range_limites_de_fim():
    s = list(Arrow.span_range("hour", Arrow(2013, 1, 1), Arrow(2013, 1, 1, 3)))
    assert len(s) == 4   # o intervalo das 3h é incluído mesmo com fim exatamente às 3h
    s = list(Arrow.span_range("hour", Arrow(2013, 1, 1), Arrow(2013, 1, 1, 2, 59, 59, 999999)))
    assert len(s) == 3
    s = list(Arrow.span_range("hour", datetime(2013, 1, 1), datetime(2013, 1, 1, 1, 30), bounds="[]", exact=True))
    assert s[-1][1] == Arrow(2013, 1, 1, 1, 30)


@alvo("ARW-T005")
@alvo("ARW-T006")
def test_span_range_exato_com_fim_no_inicio_de_intervalo():
    assert len(list(Arrow.span_range("hour", Arrow(2013, 1, 1, 0, 30), Arrow(2013, 1, 1, 2, 30), exact=True))) == 2
    assert len(list(Arrow.span_range("hour", Arrow(2013, 1, 1, 0, 30), Arrow(2013, 1, 1, 2, 30),
                                     exact=True, bounds="()"))) == 2


@alvo("ARW-T007")
def test_shift_para_horario_inexistente():
    a = Arrow(2019, 3, 31, 1, 30, tzinfo="Europe/Paris").shift(hours=1)
    assert a.hour == 3


@alvo("ARW-T008")
@alvo("ARW-T009")
@alvo("ARW-T010")
@alvo("ARW-T011")
@alvo("ARW-T012")
def test_humanize_caminhos_internos():
    assert BASE.humanize(datetime(2013, 5, 5, 11)) == "in an hour"
    assert BASE.shift(hours=2).humanize(BASE, granularity=["hour"]) == "in 2 hours"
    assert BASE.shift(seconds=-30).humanize(BASE) == "30 seconds ago"
    assert BASE.shift(days=-50).humanize(BASE) == "2 months ago"
    assert BASE.shift(seconds=1).humanize(BASE, granularity="second") == "just now"


@alvo("ARW-T013")
def test_humanize_lista_vazia():
    with pytest.raises(ValueError):
        BASE.humanize(BASE, granularity=[])


@alvo("ARW-T014")
def test_humanize_granularidade_sem_traducao():
    with pytest.raises(ValueError):
        BASE.shift(weeks=2).humanize(BASE, granularity="week", locale="af")


@alvo("ARW-T015")
def test_dehumanize_locale_nao_suportado():
    from arrow import constants
    loc = next(n for n in sorted(locales._locale_map) if n not in constants.DEHUMANIZE_LOCALES)
    with pytest.raises(ValueError):
        BASE.dehumanize("2 days ago", locale=loc)


@alvo("ARW-T016")
def test_dehumanize_locale_com_formas():
    assert BASE.dehumanize("через 2 дня", locale="ru") == BASE.shift(days=2)


@alvo("ARW-T017")
def test_is_between_fim_invalido():
    with pytest.raises(TypeError):
        BASE.is_between(BASE, datetime(2014, 1, 1))


@alvo("ARW-T018")
def test_dst():
    assert Arrow(2013, 7, 1, tzinfo="Europe/Paris").dst() == timedelta(hours=1)


@alvo("ARW-T019")
@alvo("ARW-T020")
@alvo("ARW-T021")
@alvo("ARW-T022")
def test_operadores_com_tipo_invalido():
    assert BASE.__rsub__("x") is NotImplemented
    for op in ("__gt__", "__ge__", "__le__"):
        assert getattr(BASE, op)("x") is NotImplemented


@alvo("ARW-T023")
def test_fuso_invalido_em_range():
    with pytest.raises(ValueError):
        list(Arrow.range("day", datetime(2013, 1, 1), limit=1, tz="Marte/Base"))


@alvo("ARW-T024")
def test_get_datetime_tentativa():
    # Tentativa de QP3: os chamadores de _get_datetime (range/span_range e comparações)
    # rejeitam timestamps e tipos inválidos antes (AttributeError / NotImplemented).
    # O ramo foi registrado como resíduo "inalcançável na prática" (ver resultados/qp3).
    with pytest.raises(AttributeError):
        list(Arrow.range("day", 0, limit=1))
    with pytest.raises(TypeError):
        BASE < 0


@alvo("ARW-T025")
def test_frames_no_plural():
    assert BASE.span("hours")[0].minute == 0


@alvo("ARW-T026")
def test_strptime_com_tzinfo():
    assert Arrow.strptime("2019", "%Y", tzinfo="Asia/Tokyo").utcoffset() == timedelta(hours=9)


@alvo("ARW-T028")
def test_atributo_inexistente():
    with pytest.raises(AttributeError):
        BASE.nao_existe


@alvo("ARW-T029")
@alvo("ARW-T030")
@alvo("ARW-T031")
@alvo("ARW-T032")
@alvo("ARW-T035")
def test_get_variacoes_de_argumentos():
    assert arrow.get(2013, 5, 5, tzinfo="Asia/Tokyo", fold=0).utcoffset() == timedelta(hours=9)
    assert arrow.get(2013, 5, 5, fold=0).year == 2013
    assert arrow.get(tzinfo=dtz.gettz("Asia/Tokyo")).utcoffset() == timedelta(hours=9)
    assert arrow.get(Decimal("0")).year == 1970
    assert arrow.get(0, tzinfo="Asia/Tokyo").hour == 9


@alvo("ARW-T033")
@alvo("ARW-T034")
def test_get_argumentos_invalidos():
    with pytest.raises(TypeError):
        arrow.get(None)
    with pytest.raises(TypeError):
        arrow.get(date(2013, 1, 1), 5)


@alvo("ARW-T037")
@alvo("ARW-T038")
def test_tokens_subsegundos():
    a = arrow.get("2013-05-05T08:07:09.123456+00:00")
    assert a.format("SSSSS") == "12345" and a.format("SSSS") == "1234"


@alvo("ARW-T039")
def test_token_sem_tratamento():
    # 'YYY' é casado pela regex do formatador mas não tem tratamento: some da saída.
    assert BASE.format("YYY") == ""


@alvo("ARW-T040")
def test_get_locale_by_class_name():
    assert isinstance(locales.get_locale_by_class_name("EnglishLocale"), locales.EnglishLocale)
    with pytest.raises(ValueError):
        locales.get_locale_by_class_name("NaoExiste")


@alvo("ARW-T041")
def test_locale_duplicado():
    with pytest.raises(LookupError):
        class Dup(locales.Locale):
            names = ["en"]


# ---------------------------------------------------------------- localidades
ORDINAIS = ["ka", "it", "es", "fr", "fi", "ko", "de", "nb", "nn", "tl", "da", "eo",
            "bn", "or", "lb", "ta", "am"]


@alvo("ARW-T043")
@pytest.mark.parametrize("loc", ORDINAIS)
@pytest.mark.parametrize("n", [-1, 0, 1, 2, 3, 4, 5, 6, 11, 22])
def test_ordinais_por_localidade(loc, n):
    txt = locales.get_locale(loc).ordinal_number(n)
    assert isinstance(txt, str)


TIMEFRAME_LOCS = ["fi", "ko", "ru", "de", "ar", "is", "cs", "sk", "he", "hu", "th", "lo",
                  "et", "hr", "mt", "sr", "lb", "zu", "si", "am", "ka"]
DELTAS = [dict(seconds=-1), dict(seconds=30), dict(minutes=-1), dict(minutes=3), dict(hours=-2),
          dict(hours=5), dict(days=1), dict(days=-2), dict(days=-3), dict(days=11), dict(weeks=1),
          dict(weeks=-2), dict(weeks=3), dict(months=-1), dict(months=2), dict(months=5),
          dict(years=1), dict(years=-2), dict(years=11), dict(years=21), dict(years=-22)]


@alvo("ARW-T065")
def test_hebraico_multi_com_palavra():
    assert BASE.shift(hours=1, minutes=1).humanize(BASE, granularity=["hour", "minute"], locale="he")


@alvo("ARW-T048")
@pytest.mark.parametrize("loc", TIMEFRAME_LOCS)
def test_humanize_por_localidade(loc):
    for d in DELTAS:
        for dist in (False, True):
            try:
                txt = BASE.shift(**d).humanize(BASE, locale=loc, only_distance=dist)
            except ValueError:
                continue   # granularidade sem tradução nessa localidade
            assert isinstance(txt, str)
    for gran in (["hour", "minute"], ["day", "hour", "minute"], ["year", "month"]):
        try:
            BASE.shift(days=1, hours=2, minutes=3).humanize(BASE, granularity=gran, locale=loc)
            BASE.shift(days=-1, hours=-2).humanize(BASE, granularity=gran, locale=loc, only_distance=True)
        except ValueError:
            pass


@alvo("ARW-T068")
@pytest.mark.parametrize("loc", ["th", "lo"])
def test_ano_budista(loc):
    assert BASE.format("YYYY", locale=loc) == "2556"
    assert BASE.format("YY", locale=loc) == "56"


@alvo("ARW-T044")
def test_ingles_instantly():
    assert BASE.humanize(BASE, only_distance=True) == "instantly"


@alvo("ARW-T089")
@alvo("ARW-T090")
@alvo("ARW-T091")
def test_describe_multi():
    loc = locales.get_locale("en")
    assert loc.describe_multi([("hours", 0), ("minutes", 0)]) == "in 0 hours and 0 minutes"
    assert "ago" in loc.describe_multi([("hours", 0), ("minutes", -5)])
    ko = locales.get_locale("ko")
    assert ko.describe_multi([("hours", 1), ("minutes", 2)])


@alvo("ARW-T092")
def test_month_number_cache():
    loc = locales.get_locale("en")
    assert loc.month_number("may") == 5 and loc.month_number("jun") == 6


# ---------------------------------------------------------------- parser
@alvo("ARW-T095")
@alvo("ARW-T097")
@alvo("ARW-T098")
def test_iso_com_espaco_e_so_hora():
    assert arrow.get("2013-05-05 12:30:45").minute == 30
    assert arrow.get("2013-05-05T12").hour == 12


@alvo("ARW-T096")
def test_iso_hora_invalida():
    with pytest.raises(parser.ParserError):
        arrow.get("2013-05-05T1x:30")


@alvo("ARW-T099")
def test_regex_invalida_no_formato():
    with pytest.raises(parser.ParserError):
        arrow.get("2013", r"YYYY[(]")


@alvo("ARW-T100")
@alvo("ARW-T103")
@alvo("ARW-T104")
@alvo("ARW-T110")
def test_tokens_do_e_dddd():
    assert arrow.get("May 5th 2013", "MMMM Do YYYY").day == 5
    a = arrow.get("Monday 2013", "dddd YYYY")
    assert a.weekday() == 0 and a.year == 2013


@alvo("ARW-T102")
def test_token_desconhecido():
    with pytest.raises(parser.ParserError):
        arrow.get("2013", "YYY")


@alvo("ARW-T105")
def test_subsegundo_arredonda_para_cima():
    assert arrow.get("12:30:45.1234567", "HH:mm:ss.S").microsecond == 123457


@alvo("ARW-T106")
def test_am_com_hora_maior_que_12():
    with pytest.raises(parser.ParserError):
        arrow.get("13 am", "H a")


@alvo("ARW-T107")
@alvo("ARW-T108")
@alvo("ARW-T109")
def test_dia_do_ano_invalido():
    with pytest.raises(parser.ParserError):
        arrow.get("125", "DDDD")
    with pytest.raises(parser.ParserError):
        arrow.get("2013-05-125", "YYYY-MM-DDDD")
    with pytest.raises(parser.ParserError):
        arrow.get("2013-400", "YYYY-DDDD")


@alvo("ARW-T111")
@alvo("ARW-T112")
@alvo("ARW-T113")
def test_meia_noite_24h_invalida():
    for s, f in [("24:01", "HH:mm"), ("24:00:01", "HH:mm:ss"), ("24:00:00.1", "HH:mm:ss.S")]:
        with pytest.raises(parser.ParserError):
            arrow.get(s, f)


@alvo("ARW-T114")
@alvo("ARW-T117")
def test_multiformato_sem_casamento():
    with pytest.raises(parser.ParserError):
        arrow.get("abc", ["YYYY", "MM/DD"])


@alvo("ARW-T118")
def test_next_weekday_invalido():
    with pytest.raises(ValueError):
        util.next_weekday(datetime(2013, 1, 1), 7)


@alvo("ARW-T119")
@alvo("ARW-T120")
@alvo("ARW-T121")
@alvo("ARW-T122")
@alvo("ARW-T123")
def test_utilitarios_de_validacao():
    assert util.is_timestamp([1]) is False
    assert util.is_timestamp(True) is False
    assert util.is_timestamp("abc") is False
    with pytest.raises(ValueError):
        Arrow.fromordinal(10**9)
    with pytest.raises(ValueError):
        arrow.get(10**30)
    with pytest.raises(ValueError):
        arrow.get((2013, 60, 1))
    with pytest.raises(ValueError):
        arrow.get((2013, 10, 9))
