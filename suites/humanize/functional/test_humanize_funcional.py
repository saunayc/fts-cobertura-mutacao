"""Suíte funcional (caixa-preta) do Humanize.

Derivada do README e da referência de API publicada (docstrings públicas
renderizadas em humanize.readthedocs.io). Rastreabilidade via ``@pytest.mark.req``.
"""
import datetime as dt
import shutil
from pathlib import Path

import pytest

import humanize
from humanize import i18n

req = pytest.mark.req


@pytest.fixture(autouse=True)
def _sem_locale():
    humanize.i18n.deactivate()
    yield
    humanize.i18n.deactivate()


# ---------------------------------------------------------------- inteiros
@req("HUM-R01")
@pytest.mark.parametrize("valor, esperado", [
    (100, "100"), (999, "999"), (1000, "1,000"), ("1000", "1,000"), (12345, "12,345"),
    (1_000_000, "1,000,000"), (1_234_567.25, "1,234,567.25"), (-1234, "-1,234"),
    (None, "None"),
])
def test_intcomma(valor, esperado):
    assert humanize.intcomma(valor) == esperado


@req("HUM-R01")
def test_intcomma_ndigits():
    assert humanize.intcomma(1234.5454545, 2) == "1,234.55"
    assert humanize.intcomma(14308.40, 1) == "14,308.4"
    assert humanize.intcomma("14308.40", 1) == "14,308.4"


@req("HUM-R02")
@pytest.mark.parametrize("valor, esperado", [
    ("100", "100"), (999, "999"), ("12400", "12.4 thousand"), ("1000000", "1.0 million"),
    (123455913, "123.5 million"), (12345591313, "12.3 billion"), (1_200_000_000, "1.2 billion"),
    (8100000000000000000000000000000000, "8.1 decillion"), (10**100, "1.0 googol"),
    (None, "None"),
])
def test_intword(valor, esperado):
    assert humanize.intword(valor) == esperado


@req("HUM-R02")
def test_intword_format_e_negativo():
    assert humanize.intword("1234000", "%0.3f") == "1.234 million"
    assert humanize.intword(-1_200_000) == "-1.2 million"


@req("HUM-R03")
@pytest.mark.parametrize("valor, esperado", [
    (0, "zero"), (4, "four"), (5, "five"), (9, "nine"), (10, "10"), (41, "41"),
    ("7", "seven"), ("foo", "foo"), (None, "None"),
])
def test_apnumber(valor, esperado):
    assert humanize.apnumber(valor) == esperado


@req("HUM-R04")
@pytest.mark.parametrize("valor, esperado", [
    (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (11, "11th"), (12, "12th"), (13, "13th"),
    (101, "101st"), (103, "103rd"), (111, "111th"), (1002, "1002nd"), (0, "0th"),
    ("something else", "something else"),
])
def test_ordinal(valor, esperado):
    assert humanize.ordinal(valor) == esperado


@req("HUM-R04")
def test_ordinal_lista_e_gender():
    assert humanize.ordinal([1, 2, 3]) == "[1, 2, 3]"
    assert humanize.ordinal(1, gender="female") == "1st"


@req("HUM-R05")
@pytest.mark.parametrize("valor, esperado", [
    (1 / 3, "1/3"), (1.5, "1 1/2"), (0.3, "3/10"), (0.333, "333/1000"), (1, "1"),
    (1.3, "1 3/10"), ("ten", "ten"), (None, "None"),
])
def test_fractional(valor, esperado):
    assert humanize.fractional(valor) == esperado


@req("HUM-R06")
@pytest.mark.parametrize("args, esperado", [
    ((0.3,), "3.00 x 10⁻¹"), ((500,), "5.00 x 10²"), (("20000",), "2.00 x 10⁴"),
    ((1**10,), "1.00 x 10⁰"), ((1**10, 1), "1.0 x 10⁰"), ((1**10, 0), "1 x 10⁰"),
    ((-1000,), "-1.00 x 10³"), ((1000, 3), "1.000 x 10³"), (("99",), "9.90 x 10¹"),
    (("foo",), "foo"), ((None,), "None"),
])
def test_scientific(args, esperado):
    assert humanize.scientific(*args) == esperado


@req("HUM-R07")
def test_clamp():
    assert humanize.clamp(123.456) == "123.456"
    assert humanize.clamp(0.0001, floor=0.01) == "<0.01"
    assert humanize.clamp(0.99, format="{:.0%}", ceil=0.99) == "99%"
    assert humanize.clamp(0.999, format="{:.0%}", ceil=0.99) == ">99%"
    assert humanize.clamp(1, format=humanize.intword, floor=1e6, floor_token="under ") == "under 1.0 million"
    assert humanize.clamp(None) is None
    assert humanize.clamp(0.01, floor=0.01) == "0.01"           # valor no limite inferior
    assert humanize.clamp(5, ceil=3, ceil_token="mais de ") == "mais de 3"


@req("HUM-R08")
@pytest.mark.parametrize("args, esperado", [
    ((1500, "V"), "1.50 kV"), ((2e8, "W"), "200 MW"), ((220e-6, "F"), "220 μF"),
    ((123_000,), "123 k"),
    ((1_230_000,), "1.23 M"), ((1e40,), "1.00 x 10⁴⁰"),
])
def test_metric(args, esperado):
    assert humanize.metric(*args) == esperado


@req("HUM-R08")
def test_metric_precision():
    assert humanize.metric(1e-14, precision=4) == "10.00 f"


# ---------------------------------------------------------------- tamanhos
@req("HUM-R09")
@pytest.mark.parametrize("args, esperado", [
    ((1_000_000,), "1.0 MB"), ((1_000_000, True), "976.6 KiB"), ((3000000,), "3.0 MB"),
    ((300, False, True), "300B"), ((3000, False, True), "2.9K"),
    ((3000, False, True, "%.3f"), "2.930K"), ((3000, True), "2.9 KiB"),
    ((10**28,), "10.0 RB"), ((10**34 * 3,), "30000.0 QB"), ((-4096, True), "-4.0 KiB"),
    ((1,), "1 Byte"), ((0,), "0 Bytes"), ((1000,), "1.0 kB"), ((1024, True), "1.0 KiB"),
    (("2000",), "2.0 kB"),
])
def test_naturalsize(args, esperado):
    assert humanize.naturalsize(*args) == esperado


@req("HUM-R09")
def test_naturalsize_gnu():
    assert humanize.naturalsize(1_000_000, gnu=True) == "976.6K"


# ---------------------------------------------------------------- datas
@req("HUM-R10")
def test_naturalday():
    hoje = dt.date.today()
    assert humanize.naturalday(dt.datetime.now()) == "today"
    assert humanize.naturalday(hoje - dt.timedelta(days=1)) == "yesterday"
    assert humanize.naturalday(hoje + dt.timedelta(days=1)) == "tomorrow"
    assert humanize.naturalday(dt.date(2007, 6, 5)) == "Jun 05"
    assert humanize.naturalday(dt.date(2007, 6, 5), "%d/%m/%Y") == "05/06/2007"


@req("HUM-R10")
def test_naturalday_entrada_nao_data():
    assert humanize.naturalday("x") == "x"


@req("HUM-R11")
def test_naturaldate():
    assert humanize.naturaldate(dt.date(2007, 6, 5)) == "Jun 05 2007"
    hoje = dt.date.today()
    assert humanize.naturaldate(hoje) == "today"
    perto = hoje + dt.timedelta(days=30)
    assert str(perto.year) not in humanize.naturaldate(perto)
    longe = hoje + dt.timedelta(days=365)
    assert str(longe.year) in humanize.naturaldate(longe)


@req("HUM-R12")
@pytest.mark.parametrize("valor, esperado", [
    (dt.timedelta(seconds=2), "2 seconds"),
    (dt.timedelta(seconds=1), "a second"),
    (dt.timedelta(minutes=30), "30 minutes"),
    (dt.timedelta(hours=1), "an hour"),
    (dt.timedelta(days=1), "a day"),
    (dt.timedelta(days=3), "3 days"),
    (dt.timedelta(days=365), "a year"),
    (dt.timedelta(milliseconds=4), "a moment"),
    (0, "a moment"),
    (60, "a minute"),
])
def test_naturaldelta(valor, esperado):
    assert humanize.naturaldelta(valor) == esperado


@req("HUM-R12")
def test_naturaldelta_readme_1001_segundos():
    assert humanize.naturaldelta(dt.timedelta(seconds=1001)) == "17 minutes"


@req("HUM-R12")
def test_naturaldelta_minimum_unit_e_months():
    d = dt.timedelta(milliseconds=4)
    assert humanize.naturaldelta(d, minimum_unit="milliseconds") == "4 milliseconds"
    assert humanize.naturaldelta(d, minimum_unit="microseconds") == "4 milliseconds"
    assert humanize.naturaldelta(dt.timedelta(microseconds=7), minimum_unit="microseconds") == "7 microseconds"
    com = humanize.naturaldelta(dt.timedelta(days=400))
    sem = humanize.naturaldelta(dt.timedelta(days=400), months=False)
    assert "month" in com and "35 days" in sem


@req("HUM-R12")
def test_naturaldelta_entradas_invalidas():
    assert humanize.naturaldelta("abc") == "abc"
    assert humanize.naturaldelta(float("inf")) == "inf"
    with pytest.raises(ValueError):
        humanize.naturaldelta(dt.timedelta(seconds=1), minimum_unit="hours")
    with pytest.raises(OverflowError):
        humanize.naturaldelta(10**20)


@req("HUM-R13")
def test_naturaltime():
    agora = dt.datetime.now()
    assert humanize.naturaltime(agora - dt.timedelta(seconds=1)) == "a second ago"
    assert humanize.naturaltime(agora - dt.timedelta(seconds=3600)) == "an hour ago"
    assert humanize.naturaltime(dt.timedelta(seconds=3)) == "3 seconds ago"
    assert humanize.naturaltime(3) == "3 seconds ago"
    assert humanize.naturaltime(3, future=True) == "3 seconds from now"
    assert humanize.naturaltime(dt.timedelta(milliseconds=4)) == "now"
    assert humanize.naturaltime(dt.timedelta(milliseconds=4), minimum_unit="milliseconds") == "4 milliseconds ago"
    assert humanize.naturaltime(dt.timedelta(milliseconds=4), minimum_unit="microseconds") == "4 milliseconds ago"


@req("HUM-R13")
def test_naturaltime_futuro_e_when():
    when = dt.datetime(2020, 1, 1, 12)
    assert humanize.naturaltime(dt.datetime(2020, 1, 1, 14), when=when) == "2 hours from now"
    assert humanize.naturaltime(dt.datetime(2020, 1, 1, 10), when=when) == "2 hours ago"
    assert humanize.naturaltime(dt.datetime(2020, 1, 1, 12), when=when) == "now"
    assert humanize.naturaltime("abc") == "abc"


@req("HUM-R13")
def test_naturaltime_com_fuso():
    tz = dt.timezone(dt.timedelta(hours=-3))
    when = dt.datetime(2020, 1, 1, 12, tzinfo=tz)
    assert humanize.naturaltime(dt.datetime(2020, 1, 1, 11, tzinfo=tz), when=when) == "an hour ago"


@req("HUM-R14")
def test_precisedelta():
    delta = dt.timedelta(seconds=3633, days=2, microseconds=123000)
    assert humanize.precisedelta(delta) == "2 days, 1 hour and 33.12 seconds"
    assert humanize.precisedelta(delta, minimum_unit="microseconds") == \
        "2 days, 1 hour, 33 seconds and 123 milliseconds"
    assert humanize.precisedelta(delta, suppress=["days"], format="%0.4f") == "49 hours and 33.1230 seconds"
    assert humanize.precisedelta(delta, format="%0.4f") == "2 days, 1 hour and 33.1230 seconds"
    assert humanize.precisedelta(delta, suppress=["days"]) == "49 hours and 33.12 seconds"


@req("HUM-R14")
def test_precisedelta_limites():
    d = dt.timedelta(seconds=90, microseconds=100)
    assert humanize.precisedelta(d, suppress=["seconds", "milliseconds", "microseconds"]) == "1.50 minutes"
    assert humanize.precisedelta(dt.timedelta(seconds=1), minimum_unit="minutes") == "0.02 minutes"
    assert humanize.precisedelta(dt.timedelta(seconds=0.1), minimum_unit="minutes") == "0 minutes"
    assert humanize.precisedelta(3600) == "1 hour"
    assert humanize.precisedelta(dt.timedelta(days=800)).startswith("2 years")


@req("HUM-R14")
def test_precisedelta_invalidos():
    assert humanize.precisedelta(None) == "None"
    assert humanize.precisedelta("abc") == "abc"
    # A documentação não especifica a exceção para unidades inválidas: exige-se apenas rejeição.
    with pytest.raises(Exception):
        humanize.precisedelta(1, minimum_unit="decades")
    with pytest.raises(Exception):
        humanize.precisedelta(1, suppress=["decades"])


@req("HUM-R15")
@pytest.mark.parametrize("itens, esperado", [
    ([], ""), (["one"], "one"), (["one", "two"], "one and two"),
    (["one", "two", "three"], "one, two and three"), ([1, 2], "1 and 2"),
])
def test_natural_list(itens, esperado):
    assert humanize.natural_list(itens) == esperado


# ---------------------------------------------------------------- i18n
@req("HUM-R16")
def test_activate_deactivate_ru():
    assert humanize.naturaltime(dt.timedelta(seconds=3)) == "3 seconds ago"
    humanize.i18n.activate("ru_RU")
    assert humanize.naturaltime(dt.timedelta(seconds=3)) == "3 секунды назад"
    humanize.i18n.deactivate()
    assert humanize.naturaltime(dt.timedelta(seconds=3)) == "3 seconds ago"


@req("HUM-R16")
def test_separadores_do_locale():
    assert i18n.thousands_separator() == "," and i18n.decimal_separator() == "."
    humanize.i18n.activate("tr_TR")
    assert humanize.intcomma(1_234_567.89) == "1.234.567,89"
    assert humanize.intword(1_200_000) == "1,2 milyon"
    assert i18n.thousands_separator() == "." and i18n.decimal_separator() == ","


@req("HUM-R16")
@pytest.mark.parametrize("loc", ["pt_BR", "fr_FR", "de_DE", "es_ES", "ja_JP"])
def test_traducoes_diferem_do_ingles(loc):
    humanize.i18n.activate(loc)
    assert humanize.naturaltime(dt.timedelta(hours=2)) != "2 hours ago"
    assert humanize.ordinal(1) != "" and humanize.naturaldelta(dt.timedelta(days=3)) != "3 days"


@req("HUM-R16")
def test_locale_inexistente_e_none():
    with pytest.raises(FileNotFoundError):
        humanize.i18n.activate("xx_XX")
    humanize.i18n.activate("ru_RU")
    humanize.i18n.activate(None)
    assert humanize.naturaltime(dt.timedelta(seconds=3)) == "3 seconds ago"


@req("HUM-R17")
def test_activate_com_path(tmp_path):
    origem = Path(humanize.__file__).parent / "locale" / "pt_BR"
    shutil.copytree(origem, tmp_path / "pt_BR")
    humanize.i18n.activate("pt_BR", path=str(tmp_path))
    assert humanize.naturaltime(dt.timedelta(hours=2)) != "2 hours ago"
    with pytest.raises(FileNotFoundError):
        humanize.i18n.activate("sk_SK", path=str(tmp_path))   # idioma ainda não carregado


@req("HUM-R17")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-06: activate(locale, path) ignora o path e não levanta "
                   "FileNotFoundError quando o mesmo locale já foi carregado do caminho padrão")
def test_activate_com_path_apos_carregar_locale(tmp_path):
    humanize.i18n.activate("it_IT")
    humanize.i18n.deactivate()
    with pytest.raises(FileNotFoundError):
        humanize.i18n.activate("it_IT", path=str(tmp_path))
