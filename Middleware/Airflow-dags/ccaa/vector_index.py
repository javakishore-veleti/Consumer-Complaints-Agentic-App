"""Local vector index adapters for complaint docs (D88 / D92). No app.* imports."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol


DEFAULT_COLLECTION = "complaints"
SIGNATURE_COLLECTION = "cfpb_semantic_signatures"
DEFAULT_DIM = 32
COMPLAINT_ID_FIELD = "Complaint ID"
DEFAULT_PG_TABLE = "complaint_vectors"
BACKEND_JSONL = "jsonl"
BACKEND_PGVECTOR = "pgvector"
BACKEND_CHROMA = "chroma"
BACKEND_REDIS = "redis"
DEFAULT_REDIS_INDEX = "complaint_vectors"


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


def _resolve_named_url(
    name: str,
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv(name), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable(name))
        except Exception:
            value = None
    if not value:
        raise ValueError(f"{name} is required (env or Airflow Variable)")
    return value


def resolve_pgvector_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    return _resolve_named_url("CCA_PGVECTOR_URL", getenv=getenv, get_variable=get_variable)


def resolve_chroma_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    return _resolve_named_url("CCA_CHROMA_URL", getenv=getenv, get_variable=get_variable)


def resolve_redis_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    return _resolve_named_url("CCA_REDIS_URL", getenv=getenv, get_variable=get_variable)


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


class ChromaStore:
    """HTTP Chroma upsert store (D94). Uses injectable client for tests.

    Chroma 0.5.x requires the collection UUID in upsert/add paths; using the
    collection name returns HTTP 400 InvalidUUID.
    """

    def __init__(
        self,
        base_url: str,
        *,
        collection: str = DEFAULT_COLLECTION,
        client: Any | None = None,
    ) -> None:
        if not (base_url or "").strip():
            raise ValueError("base_url is required")
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.collection_id: str = ""
        self._client = client
        self.ensure_schema()

    def _http(self):
        if self._client is not None:
            return self._client
        import urllib.error
        import urllib.request

        class _UrllibClient:
            def __init__(self, root: str) -> None:
                self.root = root

            def _collection_id_from_payload(self, raw: bytes) -> str:
                payload = json.loads(raw.decode("utf-8") or "{}")
                cid = str((payload or {}).get("id") or "").strip()
                if not cid:
                    raise ValueError("Chroma create/get response missing collection id")
                return cid

            def _get_collection_id_by_name(self, name: str) -> str:
                req = urllib.request.Request(
                    f"{self.root}/api/v1/collections/{name}",
                    method="GET",
                )
                return self._collection_id_from_payload(urllib.request.urlopen(req, timeout=30).read())

            def ensure_collection(self, name: str) -> str:
                req = urllib.request.Request(
                    f"{self.root}/api/v1/collections",
                    data=json.dumps({"name": name, "get_or_create": True}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    return self._collection_id_from_payload(urllib.request.urlopen(req, timeout=30).read())
                except urllib.error.HTTPError as exc:
                    if exc.code == 409:
                        return self._get_collection_id_by_name(name)
                    raise

            def upsert(
                self,
                collection_id: str,
                ids: list[str],
                embeddings: list[list[float]],
                documents: list[str],
                metadatas: list[dict[str, Any]] | None = None,
            ) -> None:
                body: dict[str, Any] = {
                    "ids": ids,
                    "embeddings": embeddings,
                    "documents": documents,
                }
                if metadatas is not None:
                    body["metadatas"] = metadatas
                req = urllib.request.Request(
                    f"{self.root}/api/v1/collections/{collection_id}/upsert",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=60).read()

            def count(self, collection_id: str) -> int:
                req = urllib.request.Request(
                    f"{self.root}/api/v1/collections/{collection_id}/count",
                    method="GET",
                )
                raw = urllib.request.urlopen(req, timeout=30).read()
                payload = json.loads(raw.decode("utf-8") or "0")
                if isinstance(payload, dict):
                    return int(payload.get("count") or payload.get("value") or 0)
                return int(payload)

            def query(
                self,
                collection_id: str,
                *,
                query_embeddings: list[list[float]],
                n_results: int = 3,
                include: list[str] | None = None,
            ) -> dict[str, Any]:
                body = {
                    "query_embeddings": query_embeddings,
                    "n_results": n_results,
                    "include": include
                    or ["documents", "metadatas", "distances"],
                }
                req = urllib.request.Request(
                    f"{self.root}/api/v1/collections/{collection_id}/query",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                raw = urllib.request.urlopen(req, timeout=60).read()
                return json.loads(raw.decode("utf-8") or "{}")

        return _UrllibClient(self.base_url)

    def ensure_schema(self) -> None:
        self.collection_id = self._http().ensure_collection(self.collection)

    def upsert(self, docs: list[dict[str, Any]]) -> int:
        if not docs:
            return 0
        if not self.collection_id:
            self.ensure_schema()
        ids = [str(d["id"]) for d in docs]
        embeddings = [list(d.get("embedding") or []) for d in docs]
        documents = [str(d.get("text") or "") for d in docs]
        metadatas = [dict(d["metadata"]) for d in docs if d.get("metadata") is not None]
        meta_arg = metadatas if len(metadatas) == len(docs) else None
        self._http().upsert(
            self.collection_id, ids, embeddings, documents, metadatas=meta_arg
        )
        return len(docs)

    def count(self) -> int:
        if not self.collection_id:
            self.ensure_schema()
        return int(self._http().count(self.collection_id))

    def query_text(self, text: str, *, n_results: int = 3) -> dict[str, Any]:
        if not self.collection_id:
            self.ensure_schema()
        emb = hash_embedding(text, dim=DEFAULT_DIM)
        return self._http().query(
            self.collection_id,
            query_embeddings=[emb],
            n_results=n_results,
        )


class RedisVectorStore:
    """Redis Stack vector+doc store (D94). Injectable client for tests."""

    def __init__(
        self,
        url: str,
        *,
        index: str = DEFAULT_REDIS_INDEX,
        dim: int = DEFAULT_DIM,
        client: Any | None = None,
    ) -> None:
        if not (url or "").strip():
            raise ValueError("url is required")
        self.url = url.strip()
        self.index = index
        self.dim = dim
        self._client = client
        self.ensure_schema()

    def _redis(self):
        if self._client is not None:
            return self._client
        import redis

        return redis.from_url(self.url, decode_responses=True)

    def ensure_schema(self) -> None:
        r = self._redis()
        if hasattr(r, "ensure_index"):
            r.ensure_index(self.index, self.dim)
            return
        # Best-effort FT.CREATE; ignore "index already exists"
        try:
            r.execute_command(
                "FT.CREATE",
                self.index,
                "ON",
                "HASH",
                "PREFIX",
                "1",
                f"{self.index}:",
                "SCHEMA",
                "text",
                "TEXT",
                "embedding",
                "VECTOR",
                "FLAT",
                "6",
                "TYPE",
                "FLOAT32",
                "DIM",
                str(self.dim),
                "DISTANCE_METRIC",
                "COSINE",
            )
        except Exception as exc:  # noqa: BLE001 — redis raises ResponseError variants
            if "Index already exists" not in str(exc) and "exists" not in str(exc).lower():
                # Hash-only fallback still usable for upsert/cache
                pass

    def upsert(self, docs: list[dict[str, Any]]) -> int:
        if not docs:
            return 0
        r = self._redis()
        for doc in docs:
            key = f"{self.index}:{doc['id']}"
            emb = doc.get("embedding") or []
            if hasattr(r, "hset_doc"):
                r.hset_doc(key, str(doc.get("text") or ""), list(emb))
            else:
                # Store embedding as comma-separated floats for MVP portability
                r.hset(
                    key,
                    mapping={
                        "text": str(doc.get("text") or ""),
                        "embedding": ",".join(f"{float(x):.8f}" for x in emb),
                        "id": str(doc["id"]),
                    },
                )
        return len(docs)


def open_vector_store(
    *,
    backend: str,
    path: Path | None = None,
    dsn: str | None = None,
    connect: Callable[[], Any] | None = None,
    client: Any | None = None,
) -> SupportsVectorUpsert:
    """Factory for index DAGs — backend agnostic to SoT (D92 / D94)."""
    kind = (backend or "").strip().lower()
    if kind == BACKEND_JSONL:
        if path is None:
            raise ValueError("path is required for jsonl backend")
        return JsonlVectorStore(path)
    if kind == BACKEND_PGVECTOR:
        if not dsn:
            raise ValueError("dsn is required for pgvector backend")
        return PgvectorStore(dsn, connect=connect)
    if kind == BACKEND_CHROMA:
        if not dsn:
            raise ValueError("dsn (CCA_CHROMA_URL) is required for chroma backend")
        return ChromaStore(dsn, client=client)
    if kind == BACKEND_REDIS:
        if not dsn:
            raise ValueError("dsn (CCA_REDIS_URL) is required for redis backend")
        return RedisVectorStore(dsn, client=client)
    raise ValueError(
        f"unknown vector backend: {backend!r} (expected jsonl|pgvector|chroma|redis)"
    )


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
