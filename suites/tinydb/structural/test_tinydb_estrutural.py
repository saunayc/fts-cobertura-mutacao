"""Suíte estrutural (caixa-branca) do TinyDB — QP3.

Cada teste mira um trecho não coberto pela suíte funcional, identificado em
``classificacao/trechos_tinydb.csv`` e marcado com ``@pytest.mark.alvo``.
Trechos classificados como inalcançáveis pela API pública não recebem teste.
"""
import pytest

from tinydb import Query, TinyDB, where
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.utils import LRUCache

alvo = pytest.mark.alvo


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    yield d
    d.close()


@alvo("TDB-T001")
def test_drop_table_banco_sem_dados(db):
    db.drop_table("qualquer")
    assert db.tables() == set()


@alvo("TDB-T002")
@alvo("TDB-T003")
def test_drop_table_inexistente(db):
    db.insert({"a": 1})
    db.drop_table("nao_existe")
    assert db.tables() == {"_default"}


@alvo("TDB-T004")
def test_exit_apos_close():
    d = TinyDB(storage=MemoryStorage)
    with d:
        d.close()
    assert d._opened is False


@alvo("TDB-T005")
def test_middleware_delega_atributos(tmp_path):
    d = TinyDB(tmp_path / "x.json", storage=CachingMiddleware(JSONStorage))
    assert d.storage._handle is not None   # atributo do storage interno
    d.close()


class Unhashable:
    __hash__ = None

    def __eq__(self, other):
        return True


@alvo("TDB-T006")
@alvo("TDB-T008")
@alvo("TDB-T009")
def test_query_com_argumento_nao_hashavel(db):
    db.insert({"v": 1})
    q = Query().v.test(lambda v, x: True, Unhashable())
    assert not q.is_cacheable()
    assert len(db.search(q)) == 1
    assert not (q & (Query().v == 1)).is_cacheable()
    assert not (q | (Query().v == 1)).is_cacheable()


@alvo("TDB-T007")
def test_query_eq_outro_tipo():
    assert (Query().a == 1) != "a == 1"


@alvo("TDB-T010")
def test_query_sem_caminho():
    with pytest.raises(ValueError):
        Query().matches("x")


@alvo("TDB-T011")
@alvo("TDB-T012")
def test_regex_sobre_valor_nao_str(db):
    db.insert({"v": 1})
    assert db.search(Query().v.matches("1")) == []
    assert db.search(Query().v.search("1")) == []


@alvo("TDB-T015")
def test_access_mode_inseguro_avisa(tmp_path):
    with pytest.warns(UserWarning):
        JSONStorage(str(tmp_path / "x.json"), access_mode="w").close()


@alvo("TDB-T016")
def test_create_dirs_com_diretorio_existente(tmp_path):
    with TinyDB(tmp_path / "db.json", create_dirs=True) as d:
        d.insert({"a": 1})
    assert (tmp_path / "db.json").exists()


@alvo("TDB-T017")
def test_persist_empty(db):
    db.table("vazia", persist_empty=True)
    assert "vazia" in db.tables()


@alvo("TDB-T018")
@alvo("TDB-T019")
def test_documento_nao_mapping(db):
    with pytest.raises(ValueError):
        db.insert([1, 2])
    with pytest.raises(ValueError):
        db.insert_multiple([[1, 2]])


@alvo("TDB-T020")
@alvo("TDB-T021")
@alvo("TDB-T022")
def test_operacoes_sem_criterio(db):
    with pytest.raises(RuntimeError):
        db.get()
    with pytest.raises(RuntimeError):
        db.contains()
    with pytest.raises(RuntimeError):
        db.remove()


@alvo("TDB-T023")
@alvo("TDB-T024")
@alvo("TDB-T025")
@alvo("TDB-T026")
@alvo("TDB-T027")
@alvo("TDB-T028")
@alvo("TDB-T029")
def test_lru_cache_interface_de_dicionario():
    c = LRUCache(capacity=2)
    c["a"] = 1
    c["b"] = 2
    c["a"] = 10                  # chave existente
    assert c.lru == ["b", "a"]
    assert len(c) == 2 and "a" in c and list(c) == ["b", "a"]
    assert c["a"] == 10
    del c["a"]
    with pytest.raises(KeyError):
        c["a"]
    c["c"] = 3
    c["d"] = 4                   # ultrapassa a capacidade
    assert "b" not in c


@alvo("TDB-T033")
@alvo("TDB-T034")
def test_freeze_tupla_e_set(db):
    db.insert({"v": 1})
    q1 = Query().v.test(lambda v, t: v in t, (1, 2))
    q2 = Query().v.test(lambda v, s: v in s, {1, 2})
    assert q1.is_cacheable() and q2.is_cacheable()
    assert len(db.search(q1)) == 1 and len(db.search(q2)) == 1
    assert len(db.search(where("v").one_of([1]))) == 1
