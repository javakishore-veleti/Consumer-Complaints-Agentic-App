"""Local vector index adapters for complaint docs (D88 / D92). No app.* imports."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol


DEFAULT_COLLECTION = "complaints"
DEFAULT_DIM = 32
COMPLAINT_ID_FIELD = "Complaint ID"
DEFAULT_PG_TABLE = "complaint_vectors"
BACKEND_JSONL = "jsonl"
BACKEND_PGVECTOR = "pgvector"


class SupportsVectorUpsert(Protocol):
    def upsert(self, docs: list[dict[str, Any]]) -> int: ...


@dataclass(frozen=True)
class IndexResult:
    rows_loaded: int
    batch_count: int


def _first_nonblank(*values: str | None) -> str | None:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_vector_store_path(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> Path:
    value = _first_nonblank(getenv("CCA_VECTOR_STORE_PATH"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_VECTOR_STORE_PATH"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_VECTOR_STORE_PATH is required (env or Airflow Variable)")
    return Path(value)


def resolve_pgvector_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_PGVECTOR_URL"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_PGVECTOR_URL"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_PGVECTOR_URL is required (env or Airflow Variable)")
    return value


def hash_embedding(text: str, *, dim: int = DEFAULT_DIM) -> list[float]:
    """Deterministic pseudo-embedding for local MVP / CI (no ML model)."""
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    out: list[float] = []
    i = 0
    while len(out) < dim:
        chunk = digest[i % len(digest)]
        out.append((chunk / 127.5) - 1.0)
        i += 1
        digest = hashlib.sha256(digest + bytes([i])).digest()
    return out[:dim]


def _embedding_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in values) + "]"


class JsonlVectorStore:
    """Simple local store: one JSONL file per collection under root."""

    def __init__(self, root: Path, collection: str = DEFAULT_COLLECTION) -> None:
        self.root = root
        self.collection = collection
        self.path = root / f"{collection}.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    def upsert(self, docs: list[dict[str, Any]]) -> int:
        existing: dict[str, dict] = {}
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                existing[str(row["id"])] = row
        for doc in docs:
            existing[str(doc["id"])] = doc
        tmp = self.path.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for row in existing.values():
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp.replace(self.path)
        return len(docs)


class PgvectorStore:
    """Postgres + pgvector upsert store (D92). Uses stdlib-friendly SQL literals."""

    def __init__(
        self,
        dsn: str,
        *,
        table: str = DEFAULT_PG_TABLE,
        dim: int = DEFAULT_DIM,
        connect: Callable[[], Any] | None = None,
    ) -> None:
        if not (dsn or "").strip():
            raise ValueError("dsn is required")
        self.dsn = dsn.strip()
        self.table = table
        self.dim = dim
        self._connect = connect
        self.ensure_schema()

    def _conn(self):
        if self._connect is not None:
            return self._connect()
        import psycopg

        return psycopg.connect(self.dsn)

    def ensure_schema(self) -> None:
        ddl_ext = "CREATE EXTENSION IF NOT EXISTS vector"
        ddl_table = (
            f"CREATE TABLE IF NOT EXISTS {self.table} ("
            "id TEXT PRIMARY KEY, "
            "text TEXT NOT NULL, "
            f"embedding vector({self.dim})"
            ")"
        )
        with self._conn() as conn:
            conn.execute(ddl_ext)
            conn.execute(ddl_table)
            conn.commit()

    def upsert(self, docs: list[dict[str, Any]]) -> int:
        if not docs:
            return 0
        sql = (
            f"INSERT INTO {self.table} (id, text, embedding) VALUES (%s, %s, %s::vector) "
            "ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, embedding = EXCLUDED.embedding"
        )
        with self._conn() as conn:
            for doc in docs:
                emb = doc.get("embedding") or []
                if len(emb) != self.dim:
                    raise ValueError(f"embedding dim must be {self.dim}, got {len(emb)}")
                conn.execute(
                    sql,
                    (str(doc["id"]), str(doc.get("text") or ""), _embedding_literal(list(emb))),
                )
            conn.commit()
        return len(docs)


def open_vector_store(
    *,
    backend: str,
    path: Path | None = None,
    dsn: str | None = None,
    connect: Callable[[], Any] | None = None,
) -> SupportsVectorUpsert:
    """Factory for index DAGs — backend agnostic to SoT (D92)."""
    kind = (backend or "").strip().lower()
    if kind == BACKEND_JSONL:
        if path is None:
            raise ValueError("path is required for jsonl backend")
        return JsonlVectorStore(path)
    if kind == BACKEND_PGVECTOR:
        if not dsn:
            raise ValueError("dsn is required for pgvector backend")
        return PgvectorStore(dsn, connect=connect)
    raise ValueError(f"unknown vector backend: {backend!r} (expected jsonl|pgvector)")


def complaint_text(doc: dict[str, Any]) -> str:
    parts = [
        str(doc.get("Product") or ""),
        str(doc.get("Issue") or ""),
        str(doc.get("Consumer complaint narrative") or ""),
        str(doc.get("Company") or ""),
    ]
    return " | ".join(p for p in parts if p)


def index_complaint_docs(
    docs: Iterable[dict[str, Any]],
    store: SupportsVectorUpsert,
    *,
    batch_size: int = 500,
) -> IndexResult:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    batch: list[dict[str, Any]] = []
    rows = 0
    batches = 0

    def flush() -> None:
        nonlocal batch, batches
        if not batch:
            return
        store.upsert(batch)
        batches += 1
        batch = []

    for doc in docs:
        cid = str(doc.get(COMPLAINT_ID_FIELD) or doc.get("_id") or "").strip()
        if not cid:
            continue
        text = complaint_text(doc)
        batch.append(
            {
                "id": cid,
                "text": text,
                "embedding": hash_embedding(text),
            }
        )
        rows += 1
        if len(batch) >= batch_size:
            flush()
    flush()
    return IndexResult(rows_loaded=rows, batch_count=batches)


def iter_mongo_complaints(mongo_url: str, *, collection_name: str = DEFAULT_COLLECTION):
    from urllib.parse import urlparse
    from pymongo import MongoClient

    client = MongoClient(mongo_url)
    parsed = urlparse(mongo_url)
    db_name = (parsed.path or "").lstrip("/").split("?")[0] or "consumer_comp_db"
    for doc in client[db_name][collection_name].find({}):
        yield doc
