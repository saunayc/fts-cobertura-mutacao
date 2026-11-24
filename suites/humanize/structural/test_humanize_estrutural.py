"""Suíte estrutural (caixa-branca) do Humanize — QP3.

Cada teste mira trechos não cobertos pela suíte funcional
(``classificacao/trechos_humanize.csv``), marcados com ``@pytest.mark.alvo``.
"""
import datetime as dt
import math

import pytest

import humanize

alvo = pytest.mark.alvo


@pytest.fixture(autouse=True)
def _sem_locale():
    humanize.i18n.deactivate()
    yield
    humanize.i18n.deactivate()


@alvo("HUM-T001")
def test_naturalsize_arredondamento_sobe_sufixo():
    assert humanize.naturalsize(999_999) == "1.0 MB"


@alvo("HUM-T004")
@alvo("HUM-T005")
@alvo("HUM-T006")
@alvo("HUM-T007")
@alvo("HUM-T008")
@alvo("HUM-T010")
@alvo("HUM-T011")
@alvo("HUM-T012")
@alvo("HUM-T013")
@alvo("HUM-T015")
@pytest.mark.parametrize("v, esperado", [(math.nan, "NaN"), (math.inf, "+Inf"), (-math.inf, "-Inf")])
def test_valores_nao_finitos(v, esperado):
    for f in (humanize.ordinal, humanize.intcomma, humanize.intword, humanize.apnumber,
              humanize.fractional, humanize.scientific, humanize.clamp, humanize.metric):
        assert f(v) == esperado
    assert humanize.intcomma(str(v)) == esperado


@alvo("HUM-T004")
def test_format_not_finite_valor_finito():
    from humanize.number import _format_not_finite
    assert _format_not_finite(1.0) == ""


@alvo("HUM-T009")
def test_intword_arredondamento_sobe_potencia():
    assert humanize.intword(999_999_999) == "1.0 billion"


@alvo("HUM-T014")
def test_clamp_format_invalido():
    with pytest.raises(ValueError):
        humanize.clamp(1, format=123)


@alvo("HUM-T016")
@alvo("HUM-T017")
@alvo("HUM-T018")
def test_metric_caminhos():
    assert humanize.metric(999.9, "V", precision=3) == "1.00 kV"
    assert humanize.metric(42) == "42.0"
    assert humanize.metric(42, "°") == "42.0°"


@alvo("HUM-T019")
def test_unit_comparacao_com_outro_tipo():
    from humanize.time import Unit
    assert Unit.DAYS.__lt__(3) is NotImplemented


@alvo("HUM-T020")
@alvo("HUM-T021")
@alvo("HUM-T022")
@alvo("HUM-T023")
@alvo("HUM-T024")
@alvo("HUM-T025")
@alvo("HUM-T026")
@pytest.mark.parametrize("delta, kw, esperado", [
    (dt.timedelta(minutes=59, seconds=50), {}, "an hour"),
    (dt.timedelta(hours=23, minutes=50), {}, "a day"),
    (dt.timedelta(days=20), {"months": False}, "20 days"),
    (dt.timedelta(days=31), {}, "a month"),
    (dt.timedelta(days=364), {}, "a year"),
    (dt.timedelta(days=120), {}, "4 months"),
    (dt.timedelta(days=367), {}, "1 year, 2 days"),
    (dt.timedelta(days=396), {}, "1 year, 1 month"),
    (dt.timedelta(days=729), {}, "2 years"),
    (dt.timedelta(days=500), {}, "1 year, 4 months"),
    (dt.timedelta(days=500), {"months": False}, "1 year, 135 days"),
    (dt.timedelta(days=3650), {}, "10 years"),
    (dt.timedelta(days=365 * 2000), {}, "2,000 years"),
])
def test_naturaldelta_faixas(delta, kw, esperado):
    assert humanize.naturaldelta(delta, **kw) == esperado


@alvo("HUM-T027")
@alvo("HUM-T029")
def test_datas_com_fuso():
    agora = dt.datetime.now(dt.timezone.utc)
    assert humanize.naturalday(agora) == "today"
    assert humanize.naturaldate(agora) == "today"


@alvo("HUM-T028")
@alvo("HUM-T030")
def test_datas_fora_da_faixa_e_nao_data():
    class Fora:
        year, month, day = 10**6, 1, 1

        def __str__(self):
            return "fora"

    assert humanize.naturalday(Fora()) == "fora"
    assert humanize.naturaldate(Fora()) == "fora"
    assert humanize.naturaldate("x") == "x"


@alvo("HUM-T031")
def test_minimum_unit_suprimido_sem_substituto():
    with pytest.raises(ValueError):
        humanize.precisedelta(1, minimum_unit="years", suppress=["years"])


@alvo("HUM-T032")
@alvo("HUM-T033")
@alvo("HUM-T034")
@alvo("HUM-T035")
@alvo("HUM-T036")
@alvo("HUM-T037")
@pytest.mark.parametrize("delta, kw, esperado", [
    (dt.timedelta(seconds=1, microseconds=999_999), {"minimum_unit": "milliseconds"}, "2 seconds"),
    (dt.timedelta(seconds=59.999), {"minimum_unit": "seconds", "format": "%0.0f"}, "1 minute"),
    (dt.timedelta(minutes=59, seconds=59.9), {"minimum_unit": "minutes", "format": "%0.0f"}, "1 hour"),
    (dt.timedelta(hours=23, minutes=59.9), {"minimum_unit": "hours", "format": "%0.0f"}, "1 day"),
])
def test_precisedelta_promocao_por_arredondamento(delta, kw, esperado):
    assert humanize.precisedelta(delta, **kw) == esperado


@alvo("HUM-T036")
@alvo("HUM-T037")
def test_precisedelta_promocao_dias_meses():
    txt = humanize.precisedelta(dt.timedelta(days=30, hours=23, minutes=59.99), minimum_unit="days",
                                format="%0.0f")
    assert "month" in txt
    txt = humanize.precisedelta(dt.timedelta(days=364.9), minimum_unit="months", format="%0.0f")
    assert "year" in txt
