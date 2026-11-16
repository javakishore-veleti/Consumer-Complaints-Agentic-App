"""Local filesystem vector index for complaint docs (D88). No app.* imports."""

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


def hash_embedding(text: str, *, dim: int = DEFAULT_DIM) -> list[float]:
    """Deterministic pseudo-embedding for local MVP / CI (no ML model)."""
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    # Expand digest to dim floats in [-1, 1]
    out: list[float] = []
    i = 0
    while len(out) < dim:
        chunk = digest[i % len(digest)]
        out.append((chunk / 127.5) - 1.0)
        i += 1
        digest = hashlib.sha256(digest + bytes([i])).digest()
    return out[:dim]


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
