"""Unit tests for Middleware/Airflow-dags/ccaa/vector_index.py (D88)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import vector_index as vi  # noqa: E402


def test_resolve_vector_store_path_prefers_env(tmp_path: Path):
    assert (
        vi.resolve_vector_store_path(
            getenv=lambda k, default=None: str(tmp_path) if k == "CCA_VECTOR_STORE_PATH" else default,
            get_variable=lambda k: "/from/var",
        )
        == tmp_path
    )


def test_resolve_vector_store_path_requires_value():
    with pytest.raises(ValueError, match="CCA_VECTOR_STORE_PATH"):
        vi.resolve_vector_store_path(
            getenv=lambda k, default=None: default,
            get_variable=lambda k: (_ for _ in ()).throw(KeyError(k)),
        )


def test_hash_embedding_is_deterministic_and_fixed_dim():
    a = vi.hash_embedding("hello", dim=16)
    b = vi.hash_embedding("hello", dim=16)
    c = vi.hash_embedding("other", dim=16)
    assert a == b
    assert len(a) == 16
    assert a != c


def test_index_complaint_docs_upserts_jsonl(tmp_path: Path):
    store = vi.JsonlVectorStore(tmp_path)
    result = vi.index_complaint_docs(
        [
            {
                "Complaint ID": "c1",
                "Product": "Credit",
                "Issue": "Billing",
                "Consumer complaint narrative": "overcharged",
                "Company": "Acme",
            },
            {"Complaint ID": "c2", "Product": "Mortgage"},
        ],
        store,
        batch_size=1,
    )
    assert result.rows_loaded == 2
    assert result.batch_count == 2
    lines = store.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["id"] in {"c1", "c2"}
    assert "embedding" in row and len(row["embedding"]) == vi.DEFAULT_DIM

    # upsert replaces same id
    result2 = vi.index_complaint_docs(
        [{"Complaint ID": "c1", "Product": "Updated"}],
        store,
        batch_size=10,
    )
    assert result2.rows_loaded == 1
    lines2 = store.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines2) == 2
    by_id = {json.loads(ln)["id"]: json.loads(ln) for ln in lines2}
    assert "Updated" in by_id["c1"]["text"]


def test_index_skips_docs_without_complaint_id(tmp_path: Path):
    store = vi.JsonlVectorStore(tmp_path)
    result = vi.index_complaint_docs([{"Product": "x"}], store)
    assert result.rows_loaded == 0
    assert not store.path.is_file() or store.path.read_text() == ""


class _FakePgConn:
    def __init__(self) -> None:
        self.statements: list[tuple] = []

    def execute(self, sql, params=None):
        self.statements.append((sql, params))

    def commit(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_open_vector_store_jsonl_and_pgvector(tmp_path: Path):
    jsonl = vi.open_vector_store(backend="jsonl", path=tmp_path)
    assert isinstance(jsonl, vi.JsonlVectorStore)
    fake = _FakePgConn()
    pg = vi.open_vector_store(
        backend="pgvector",
        dsn="postgresql://postgres:postgres@127.0.0.1:5432/cca",
        connect=lambda: fake,
    )
    assert isinstance(pg, vi.PgvectorStore)
    # ensure_schema ran CREATE EXTENSION + CREATE TABLE
    assert any("CREATE EXTENSION" in s[0] for s in fake.statements)
    assert any("CREATE TABLE" in s[0] for s in fake.statements)
    with pytest.raises(ValueError, match="unknown vector backend"):
        vi.open_vector_store(backend="pinecone", path=tmp_path)


class _FakeChromaClient:
    def __init__(self) -> None:
        self.collections: list[str] = []
        self.upserts: list[tuple] = []

    def ensure_collection(self, name: str) -> None:
        self.collections.append(name)

    def upsert(self, name: str, ids: list[str], embeddings: list[list[float]], documents: list[str]) -> None:
        self.upserts.append((name, ids, embeddings, documents))


class _FakeRedisClient:
    def __init__(self) -> None:
        self.indexes: list[tuple] = []
        self.docs: list[tuple] = []

    def ensure_index(self, index: str, dim: int) -> None:
        self.indexes.append((index, dim))

    def hset_doc(self, key: str, text: str, embedding: list[float]) -> None:
        self.docs.append((key, text, embedding))


def test_open_vector_store_chroma_and_redis():
    chroma_client = _FakeChromaClient()
    chroma = vi.open_vector_store(
        backend="chroma",
        dsn="http://127.0.0.1:8000",
        client=chroma_client,
    )
    assert isinstance(chroma, vi.ChromaStore)
    assert chroma_client.collections == [vi.DEFAULT_COLLECTION]
    emb = vi.hash_embedding("hi")
    assert chroma.upsert([{"id": "c1", "text": "hi", "embedding": emb}]) == 1
    assert chroma_client.upserts[0][0] == vi.DEFAULT_COLLECTION
    assert chroma_client.upserts[0][1] == ["c1"]

    redis_client = _FakeRedisClient()
    redis_store = vi.open_vector_store(
        backend="redis",
        dsn="redis://127.0.0.1:6379",
        client=redis_client,
    )
    assert isinstance(redis_store, vi.RedisVectorStore)
    assert redis_client.indexes == [(vi.DEFAULT_REDIS_INDEX, vi.DEFAULT_DIM)]
    assert redis_store.upsert([{"id": "c2", "text": "bye", "embedding": emb}]) == 1
    assert redis_client.docs[0][0] == f"{vi.DEFAULT_REDIS_INDEX}:c2"


def test_resolve_chroma_and_redis_url_prefer_env():
    assert (
        vi.resolve_chroma_url(
            getenv=lambda k, default=None: "http://env-chroma" if k == "CCA_CHROMA_URL" else default,
            get_variable=lambda k: "http://var",
        )
        == "http://env-chroma"
    )
    assert (
        vi.resolve_redis_url(
            getenv=lambda k, default=None: "redis://env" if k == "CCA_REDIS_URL" else default,
            get_variable=lambda k: "redis://var",
        )
        == "redis://env"
    )


def test_pgvector_store_upsert_uses_conflict(tmp_path: Path):
    fake = _FakePgConn()
    store = vi.PgvectorStore(
        "postgresql://x",
        connect=lambda: fake,
        dim=vi.DEFAULT_DIM,
    )
    emb = vi.hash_embedding("hello")
    n = store.upsert([{"id": "c1", "text": "hello", "embedding": emb}])
    assert n == 1
    upserts = [s for s in fake.statements if s[1] is not None]
    assert upserts
    sql, params = upserts[-1]
    assert "ON CONFLICT" in sql
    assert params[0] == "c1"
    assert params[1] == "hello"


def test_resolve_pgvector_url_prefers_env():
    assert (
        vi.resolve_pgvector_url(
            getenv=lambda k, default=None: "postgresql://env" if k == "CCA_PGVECTOR_URL" else default,
            get_variable=lambda k: "postgresql://var",
        )
        == "postgresql://env"
    )
