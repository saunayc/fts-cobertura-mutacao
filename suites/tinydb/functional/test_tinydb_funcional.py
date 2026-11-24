"""Suíte funcional (caixa-preta) do TinyDB.

Derivada exclusivamente da documentação pública (README, getting-started,
usage, extend e referência de API). Cada teste é rastreado a um requisito de
``requisitos/tinydb.csv`` pelo marcador ``@pytest.mark.req``.
Técnicas: partição de equivalência (PE) e análise de valor-limite (AVL).
"""
import json
import re

import pytest

from tinydb import Query, TinyDB, where
from tinydb.middlewares import CachingMiddleware, Middleware
from tinydb.operations import add, decrement, delete, increment, set as op_set, subtract
from tinydb.storages import JSONStorage, MemoryStorage, Storage
from tinydb.table import Document

req = pytest.mark.req


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    yield d
    d.close()


@pytest.fixture
def fruits(db):
    db.insert({"type": "apple", "count": 7})
    db.insert({"type": "peach", "count": 3})
    return db


# ---------------------------------------------------------------- básico
@req("TDB-R01")
def test_insert_retorna_id(db):
    first = db.insert({"type": "apple", "count": 7})
    second = db.insert({"type": "peach", "count": 3})
    assert isinstance(first, int) and isinstance(second, int)
    assert first != second
    assert db.get(doc_id=first) == {"type": "apple", "count": 7}


@req("TDB-R02")
def test_all_e_iter_tabela_vazia(db):
    assert db.all() == []
    assert list(iter(db)) == []


@req("TDB-R02")
def test_all_e_iter_tabela_com_dados(fruits):
    docs = fruits.all()
    assert docs == [{"type": "apple", "count": 7}, {"type": "peach", "count": 3}]
    assert list(fruits) == docs


@req("TDB-R03")
@pytest.mark.parametrize(
    "query, esperados",
    [
        (Query().count == 7, ["apple"]),
        (Query().count != 7, ["peach"]),
        (Query().count > 3, ["apple"]),       # limite: 3 não entra
        (Query().count >= 3, ["apple", "peach"]),
        (Query().count < 7, ["peach"]),       # limite: 7 não entra
        (Query().count <= 7, ["apple", "peach"]),
        (Query().count > 7, []),
        (Query().count < 3, []),
        (Query().count > 6, ["apple"]),       # limite - 1
        (Query().count < 4, ["peach"]),       # limite + 1
    ],
)
def test_search_operadores_comparacao(fruits, query, esperados):
    assert [d["type"] for d in fruits.search(query)] == esperados


@req("TDB-R03")
def test_search_campo_ausente_nao_casa(fruits):
    assert fruits.search(Query().inexistente == 1) == []


@req("TDB-R04")
def test_update_com_query(fruits):
    Fruit = Query()
    ids = fruits.update({"count": 10}, Fruit.type == "apple")
    assert len(ids) == 1
    assert fruits.all() == [{"type": "apple", "count": 10}, {"type": "peach", "count": 3}]


@req("TDB-R05")
def test_remove_com_query(fruits):
    removidos = fruits.remove(Query().count < 5)
    assert len(removidos) == 1
    assert fruits.all() == [{"type": "apple", "count": 7}]


@req("TDB-R06")
def test_truncate(fruits):
    fruits.truncate()
    assert fruits.all() == []
    assert len(fruits) == 0


# ---------------------------------------------------------------- queries
@req("TDB-R07")
def test_campos_aninhados(db):
    db.insert({"name": "a", "birthday": {"year": 1990}})
    db.insert({"name": "b", "birthday": {"year": 1900}})
    User = Query()
    assert [d["name"] for d in db.search(User.birthday.year == 1990)] == ["a"]
    assert [d["name"] for d in db.search(User["birthday"]["year"] == 1900)] == ["b"]


@req("TDB-R07")
def test_campo_com_nome_invalido_por_indice(db):
    db.insert({"country-code": "foo"})
    assert len(db.search(Query()["country-code"] == "foo")) == 1


@req("TDB-R08")
def test_where_equivale_a_query(db):
    db.insert({"field": "value", "birthday": {"year": 1900}})
    db.insert({"field": "other"})
    assert db.search(where("field") == "value") == db.search(Query()["field"] == "value")
    assert len(db.search(where("birthday").year == 1900)) == 1
    assert len(db.search(where("birthday")["year"] == 1900)) == 1


@req("TDB-R09")
def test_map_transforma_valor(db):
    db.insert({"name": "JOSE"})
    db.insert({"name": "maria"})
    assert len(db.search(Query().name.map(str.lower) == "jose")) == 1


@req("TDB-R10")
def test_exists(db):
    db.insert({"name": "John"})
    db.insert({"age": 3})
    assert db.search(Query().name.exists()) == [{"name": "John"}]


@req("TDB-R11")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-01: docs dizem 'Full item has to match', "
                   "mas 'John' casa com 'Johnny' (ancora so no inicio)")
def test_matches_valor_inteiro(db):
    db.insert({"name": "John"})
    db.insert({"name": "Johnny"})
    assert db.search(Query().name.matches("John")) == [{"name": "John"}]


@req("TDB-R11")
def test_matches_flags_e_inicio(db):
    db.insert({"name": "John"})
    db.insert({"name": "john"})
    db.insert({"name": "xJohn"})
    assert db.search(Query().name.matches("John")) == [{"name": "John"}]


@req("TDB-R11")
def test_matches_com_flag(db):
    db.insert({"name": "John"})
    db.insert({"name": "john"})
    assert len(db.search(Query().name.matches("John", flags=re.IGNORECASE))) == 2


@req("TDB-R11")
@pytest.mark.xfail(strict=True, reason="DIVERGENCIA-02: a mesma regex com flags diferentes "
                   "reaproveita o resultado do cache de consultas")
def test_matches_flag_apos_consulta_sem_flag(db):
    db.insert({"name": "John"})
    db.insert({"name": "john"})
    assert len(db.search(Query().name.matches("John"))) == 1
    assert len(db.search(Query().name.matches("John", flags=re.IGNORECASE))) == 2


@req("TDB-R12")
def test_search_substring(db):
    db.insert({"name": "abbc"})
    db.insert({"name": "acd"})
    assert db.search(Query().name.search("b+")) == [{"name": "abbc"}]
    assert len(db.search(Query().name.search("B+", flags=re.IGNORECASE))) == 1


@req("TDB-R13")
@pytest.mark.parametrize("idade, casa", [(-1, False), (0, True), (21, True), (22, False)])
def test_test_com_parametros_valor_limite(db, idade, casa):
    db.insert({"age": idade})

    def entre(val, m, n):
        return m <= val <= n

    assert bool(db.search(Query().age.test(entre, 0, 21))) is casa


@req("TDB-R13")
def test_test_simples(db):
    db.insert({"name": "John"})
    assert len(db.search(Query().name.test(lambda s: s == "John"))) == 1


@req("TDB-R14")
def test_fragment(db):
    db.insert({"foo": True, "bar": False, "foobar": "yes!"})
    db.insert({"foo": True, "bar": True})
    db.insert({"field": {"foo": True, "bar": False, "x": 1}})
    assert db.search(Query().fragment({"foo": True, "bar": False})) == [
        {"foo": True, "bar": False, "foobar": "yes!"}
    ]
    assert len(db.search(Query().field.fragment({"foo": True, "bar": False}))) == 1


@pytest.fixture
def users(db):
    db.insert({"name": "user1", "groups": ["user"]})
    db.insert({"name": "user2", "groups": ["admin", "user"]})
    db.insert({"name": "user3", "groups": ["sudo", "user"]})
    return db


@pytest.fixture
def groups(db):
    t = db.table("groups")
    t.insert({"name": "user", "permissions": [{"type": "read"}]})
    t.insert({"name": "sudo", "permissions": [{"type": "read"}, {"type": "sudo"}]})
    t.insert({"name": "admin", "permissions": [{"type": "read"}, {"type": "write"}, {"type": "sudo"}]})
    return t


@req("TDB-R15")
def test_any_com_lista(users):
    nomes = [d["name"] for d in users.search(Query().groups.any(["admin", "sudo"]))]
    assert nomes == ["user2", "user3"]


@req("TDB-R15")
def test_any_com_query(groups):
    assert len(groups.search(Query().permissions.any(Query().type == "read"))) == 3
    assert len(groups.search(Query().permissions.any(Query().type == "write"))) == 1


@req("TDB-R16")
def test_all_com_lista(users):
    assert [d["name"] for d in users.search(Query().groups.all(["admin", "user"]))] == ["user2"]


@req("TDB-R16")
def test_all_com_query(groups):
    assert [d["name"] for d in groups.search(Query().permissions.all(Query().type == "read"))] == ["user"]


@req("TDB-R17")
def test_one_of(db):
    for n in ("jane", "john", "bob"):
        db.insert({"name": n})
    assert sorted(d["name"] for d in db.search(Query().name.one_of(["jane", "john"]))) == ["jane", "john"]


@req("TDB-R18")
def test_modificadores_logicos(db):
    db.insert({"name": "John", "age": 30})
    db.insert({"name": "John", "age": 31})
    db.insert({"name": "Bob", "age": 20})
    User = Query()
    assert len(db.search(~(User.name == "John"))) == 1
    assert len(db.search((User.name == "John") & (User.age <= 30))) == 1
    assert len(db.search((User.name == "John") | (User.name == "Bob"))) == 3
    assert len(db.search(Query().noop())) == 3


@req("TDB-R19")
def test_predicado_callable_em_search(db):
    db.insert({"a": 1, "b": 1})
    db.insert({"a": 1, "b": 2})
    assert db.search(lambda doc: doc.get("a") == doc.get("b")) == [{"a": 1, "b": 1}]


@req("TDB-R19")
def test_query_sem_condicao_nao_pode_ser_usada(db):
    db.insert({"a": 1})
    with pytest.raises(Exception):
        db.search(Query())


# ---------------------------------------------------------------- dados
@req("TDB-R20")
def test_insert_multiple_lista_e_gerador(db):
    ids = db.insert_multiple([{"name": "John", "age": 22}, {"name": "John", "age": 37}])
    assert len(ids) == 2
    ids2 = db.insert_multiple({"int": 1, "value": i} for i in range(2))
    assert len(ids2) == 2
    assert len(db) == 4


@req("TDB-R20")
def test_insert_multiple_vazio(db):
    assert db.insert_multiple([]) == []
    assert len(db) == 0


@req("TDB-R21")
def test_document_com_doc_id(db):
    assert db.insert(Document({"name": "John", "age": 22}, doc_id=12)) == 12
    assert db.insert_multiple(
        [Document({"name": "A"}, doc_id=20), Document({"name": "B"}, doc_id=21)]
    ) == [20, 21]
    assert db.get(doc_id=12)["name"] == "John"


@req("TDB-R21")
def test_document_com_doc_id_duplicado(db):
    db.insert(Document({"name": "John"}, doc_id=12))
    with pytest.raises(ValueError):
        db.insert(Document({"name": "Jane"}, doc_id=12))
    with pytest.raises(ValueError):
        db.insert_multiple([Document({"name": "Jane"}, doc_id=12)])


@req("TDB-R22")
def test_update_sem_query(fruits):
    fruits.update({"foo": "bar"})
    assert all(d["foo"] == "bar" for d in fruits.all())


@req("TDB-R23")
def test_operacoes_de_update(db):
    db.insert({"name": "John", "key1": 1, "n": 10, "s": "ab"})
    q = Query().name == "John"
    db.update(delete("key1"), q)
    db.update(increment("n"), q)
    db.update(decrement("n"), q)
    db.update(decrement("n"), q)
    db.update(add("n", 5), q)
    db.update(subtract("n", 2), q)
    db.update(add("s", "cd"), q)
    db.update(op_set("novo", True), q)
    assert db.get(q) == {"name": "John", "n": 12, "s": "abcd", "novo": True}


@req("TDB-R24")
def test_update_funcao_personalizada(db):
    db.insert({"name": "John", "tags": []})

    def append_tag(tag):
        def transform(doc):
            doc["tags"].append(tag)
        return transform

    db.update(append_tag("x"), Query().name == "John")
    assert db.all()[0]["tags"] == ["x"]


@req("TDB-R25")
def test_update_multiple(db):
    db.insert({"char": "a", "int": 1})
    db.insert({"char": "b", "int": 1})
    db.insert({"char": "c", "int": 1})
    db.update_multiple([
        ({"int": 2}, where("char") == "a"),
        (delete("int"), where("char") == "b"),
    ])
    assert db.all() == [{"char": "a", "int": 2}, {"char": "b"}, {"char": "c", "int": 1}]


@req("TDB-R26")
def test_upsert_atualiza_quando_existe(db):
    db.insert({"name": "John", "logged-in": False})
    db.insert({"name": "John", "logged-in": False})
    ids = db.upsert({"name": "John", "logged-in": True}, Query().name == "John")
    assert len(ids) == 2
    assert all(d["logged-in"] for d in db.all())


@req("TDB-R26")
def test_upsert_insere_quando_nao_existe(db):
    db.upsert({"name": "John", "logged-in": True}, Query().name == "John")
    assert db.all() == [{"name": "John", "logged-in": True}]


@req("TDB-R26")
def test_upsert_por_doc_id(db):
    db.upsert(Document({"name": "John"}, doc_id=12))
    assert db.get(doc_id=12) == {"name": "John"}
    db.upsert(Document({"name": "Jane"}, doc_id=12))
    assert db.get(doc_id=12) == {"name": "Jane"}
    assert len(db) == 1


@req("TDB-R26")
def test_upsert_sem_query_nem_doc_id_e_erro(db):
    with pytest.raises(ValueError):
        db.upsert({"name": "John"})


@req("TDB-R27")
@pytest.mark.parametrize("n", [0, 1, 3])
def test_len_count_contains_get_por_quantidade(db, n):
    for i in range(n):
        db.insert({"name": "John", "age": 20 + i})
    q = Query().name == "John"
    assert len(db) == n
    assert db.count(q) == n
    assert db.contains(q) is (n > 0)
    if n == 0:
        assert db.get(q) is None
    else:
        assert db.get(q)["name"] == "John"


@req("TDB-R28")
def test_doc_ids(db):
    ids = db.insert_multiple([{"v": 1}, {"v": 2}, {"v": 3}])
    el = db.get(Query().v == 2)
    assert el.doc_id == ids[1]
    assert db.all()[0].doc_id == ids[0]
    assert db.update({"v": 9}, doc_ids=ids[:2]) == ids[:2]
    assert db.contains(doc_id=ids[0]) is True
    assert db.contains(doc_id=999) is False
    assert [d["v"] for d in db.get(doc_ids=ids[:2])] == [9, 9]
    assert db.remove(doc_ids=ids[:2]) == ids[:2]
    assert db.get(doc_id=ids[2]) == {"v": 3}
    assert db.get(doc_id=ids[0]) is None


@req("TDB-R28")
def test_doc_ids_inexistentes_sao_ignorados(db):
    ids = db.insert_multiple([{"v": 1}])
    assert db.update({"v": 2}, doc_ids=[ids[0], 999]) == [ids[0]]
    assert db.remove(doc_ids=[999]) == []
    assert db.remove(doc_ids=[ids[0], 998]) == [ids[0]]


# ---------------------------------------------------------------- tabelas
@req("TDB-R29")
def test_tabelas(db):
    table = db.table("table_name")
    table.insert({"value": True})
    assert table.all() == [{"value": True}]
    assert list(table) == [{"value": True}]
    db.insert({"x": 1})
    assert db.tables() == {"_default", "table_name"}
    db.drop_table("table_name")
    assert db.tables() == {"_default"}
    db.drop_tables()
    assert db.tables() == set()


@req("TDB-R29")
def test_tabela_vazia_nao_aparece_em_tables(db):
    db.table("nada")
    assert "nada" not in db.tables()


@req("TDB-R30")
def test_default_table_name_por_instancia(db):
    db.default_table_name = "my-default"
    db.insert({"a": 1})
    assert "my-default" in db.tables()


@req("TDB-R31")
@pytest.mark.parametrize("cache_size", [0, 1, 30, None])
def test_cache_size_nao_altera_resultado(db, cache_size):
    t = db.table("t", cache_size=cache_size)
    t.insert_multiple([{"v": i} for i in range(5)])
    q = Query().v >= 2
    assert len(t.search(q)) == 3
    assert len(t.search(q)) == 3       # segunda leitura (potencialmente do cache)
    t.insert({"v": 10})
    assert len(t.search(q)) == 4       # escrita invalida o cache
    t.clear_cache()
    assert len(t.search(q)) == 4


@req("TDB-R31")
def test_mesma_tabela_reaproveitada(db):
    assert db.table("t", cache_size=5) is db.table("t", cache_size=50)


@req("TDB-R31")
def test_clear_cache_relê_storage_externo(tmp_path):
    path = tmp_path / "db.json"
    a = TinyDB(path)
    b = TinyDB(path)
    a.insert({"v": 1})
    q = Query().v == 1
    assert len(b.search(q)) == 1
    a.insert({"v": 1})
    b.clear_cache()
    assert len(b.search(q)) == 2
    a.close()
    b.close()


# ---------------------------------------------------------------- storages
@req("TDB-R32")
def test_json_storage_persiste(tmp_path):
    path = tmp_path / "db.json"
    with TinyDB(path) as db:
        db.insert({"a": 1})
    with TinyDB(path) as db:
        assert db.all() == [{"a": 1}]
    assert json.loads(path.read_text())["_default"]


@req("TDB-R32")
def test_json_storage_kwargs_indent(tmp_path):
    path = tmp_path / "db.json"
    with TinyDB(path, indent=4, sort_keys=True) as db:
        db.insert({"b": 1, "a": 2})
    assert "\n    " in path.read_text()


@req("TDB-R32")
def test_json_storage_create_dirs(tmp_path):
    path = tmp_path / "x" / "y" / "db.json"
    with TinyDB(path, create_dirs=True) as db:
        db.insert({"a": 1})
    assert path.exists()


@req("TDB-R32")
def test_json_storage_sem_create_dirs_falha(tmp_path):
    with pytest.raises(OSError):
        TinyDB(tmp_path / "nao" / "existe" / "db.json")


@req("TDB-R32")
def test_memory_storage_nao_cria_arquivo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = TinyDB(storage=MemoryStorage)
    db.insert({"a": 1})
    assert list(tmp_path.iterdir()) == []


@req("TDB-R33")
def test_access_mode_somente_leitura(tmp_path):
    path = tmp_path / "db.json"
    with TinyDB(path) as db:
        db.insert({"a": 1})
    with TinyDB(path, access_mode="r") as db:
        assert db.all() == [{"a": 1}]
        with pytest.raises(Exception):
            db.insert({"b": 2})


# ---------------------------------------------------------------- middleware
@req("TDB-R34")
def test_caching_middleware_flush_e_close(tmp_path):
    path = tmp_path / "db.json"
    db = TinyDB(path, storage=CachingMiddleware(JSONStorage))
    db.insert({"a": 1})
    assert db.all() == [{"a": 1}]
    db.storage.flush()
    assert json.loads(path.read_text())["_default"]
    db.insert({"b": 2})
    db.close()
    with TinyDB(path) as db2:
        assert len(db2) == 2


@req("TDB-R34")
def test_caching_middleware_write_cache_size_limite(tmp_path, monkeypatch):
    monkeypatch.setattr(CachingMiddleware, "WRITE_CACHE_SIZE", 3)
    path = tmp_path / "db.json"
    db = TinyDB(path, storage=CachingMiddleware(JSONStorage))

    def no_disco():
        txt = path.read_text()
        return len(json.loads(txt).get("_default", {})) if txt.strip() else 0

    db.insert({"n": 1})
    db.insert({"n": 2})
    assert no_disco() == 0          # WRITE_CACHE_SIZE - 1 escritas: ainda em memória
    db.insert({"n": 3})
    assert no_disco() == 3          # WRITE_CACHE_SIZE escritas: gravado
    db.close()


@req("TDB-R34")
def test_caching_middleware_memoria(db):
    m = TinyDB(storage=CachingMiddleware(MemoryStorage))
    m.insert({"a": 1})
    m.storage.flush()
    assert m.all() == [{"a": 1}]
    m.close()


@req("TDB-R35")
def test_context_manager_fecha_storage():
    closed = []

    class S(MemoryStorage):
        def close(self):
            closed.append(True)

    with TinyDB(storage=S) as db:
        db.insert({"a": 1})
    assert closed == [True]


# ---------------------------------------------------------------- extensão
@req("TDB-R36")
def test_storage_personalizado_recebe_argumentos_e_inicializa():
    class DictStorage(Storage):
        def __init__(self, name):
            self.name = name
            self.data = None

        def read(self):
            return self.data

        def write(self, data):
            self.data = data

    db = TinyDB("algo", storage=DictStorage)
    assert db.storage.name == "algo"
    assert db.all() == []
    db.insert({"a": 1})
    assert "_default" in db.storage.data


@req("TDB-R36")
def test_middleware_personalizado(db):
    class RemoveEmpty(Middleware):
        def read(self):
            data = self.storage.read()
            for table in (data or {}).values():
                for k in [k for k, v in table.items() if v == {}]:
                    del table[k]
            return data

        def write(self, data):
            self.storage.write(data)

        def close(self):
            self.storage.close()

    d = TinyDB(storage=RemoveEmpty(MemoryStorage))
    d.insert({})
    d.insert({"a": 1})
    assert d.all() == [{"a": 1}]
    d.close()


@req("TDB-R37")
def test_propriedades_e_repr(db):
    t = db.table("abc")
    assert t.name == "abc"
    assert t.storage is db.storage
    assert "abc" in repr(t)
    assert "TinyDB" in repr(db)
