"""Ingest CFPB CSV/zip rows into local Mongo (D10 / D20 / D86). No app.* imports."""

from __future__ import annotations

import csv
import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol


COMPLAINT_ID_FIELD = "Complaint ID"
DEFAULT_COLLECTION = "complaints"
DEFAULT_DB_NAME = "consumer_comp_db"
DEFAULT_BATCH_SIZE = 500


class SupportsBulkWrite(Protocol):
    def create_index(self, keys: Any, **kwargs: Any) -> Any: ...

    def bulk_write(self, ops: list[Any], ordered: bool = False) -> Any: ...


@dataclass(frozen=True)
class IngestResult:
    rows_loaded: int
    batch_count: int


def _first_nonblank(*values: str | None) -> str | None:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_complaints_mongo_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_MONGO_COMPLAINTS_URL"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_MONGO_COMPLAINTS_URL"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_MONGO_COMPLAINTS_URL is required (env or Airflow Variable)")
    return value


def open_complaints_collection(
    mongo_url: str,
    *,
    collection_name: str = DEFAULT_COLLECTION,
):
    """Lazy pymongo client; database from URI path or consumer_comp_db."""
    from pymongo import MongoClient
    from urllib.parse import urlparse

    client = MongoClient(mongo_url)
    parsed = urlparse(mongo_url)
    db_name = (parsed.path or "").lstrip("/").split("?")[0] or DEFAULT_DB_NAME
    return client[db_name][collection_name]


def _first_csv_member(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if not n.endswith("/") and n.lower().endswith(".csv")]
    if not names:
        raise ValueError("zip has no CSV member")
    return names[0]


def _make_replace_one(filter_doc: dict, replacement: dict):
    try:
        from pymongo import ReplaceOne

        return ReplaceOne(filter_doc, replacement, upsert=True)
    except ImportError:
        # Test doubles: store a simple namespace-like object
        class Op:
            def __init__(self) -> None:
                self._filter = filter_doc
                self.doc = replacement

        return Op()


def ingest_complaints_zip(
    source_zip: Path,
    collection: SupportsBulkWrite,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    ensure_index: bool = True,
) -> IngestResult:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    if not source_zip.is_file():
        raise FileNotFoundError(f"source zip not found: {source_zip}")

    if ensure_index:
        # Same name as CICD/Local/mongodb docker-entrypoint-initdb.d/01-init-complaints.js
        # so a fresh volume (uniq_complaint_id already present) does not IndexOptionsConflict.
        collection.create_index(
            COMPLAINT_ID_FIELD, unique=True, name="uniq_complaint_id"
        )

    rows_loaded = 0
    batch_count = 0
    batch: list[Any] = []

    def flush() -> None:
        nonlocal batch_count, batch
        if not batch:
            return
        collection.bulk_write(batch, ordered=False)
        batch_count += 1
        batch = []

    with zipfile.ZipFile(source_zip, "r") as zf:
        member = _first_csv_member(zf)
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            if not reader.fieldnames or COMPLAINT_ID_FIELD not in reader.fieldnames:
                raise ValueError(f"CSV must include {COMPLAINT_ID_FIELD!r} column")
            for row in reader:
                cid = (row.get(COMPLAINT_ID_FIELD) or "").strip()
                if not cid:
                    continue
                doc = {k: (v if v != "" else None) for k, v in row.items()}
                doc["_id"] = cid
                doc[COMPLAINT_ID_FIELD] = cid
                batch.append(_make_replace_one({COMPLAINT_ID_FIELD: cid}, doc))
                rows_loaded += 1
                if len(batch) >= batch_size:
                    flush()
            flush()

    return IngestResult(rows_loaded=rows_loaded, batch_count=batch_count)


def ingest_complaints_parts(
    sources: Iterable[Path],
    collection: SupportsBulkWrite,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    ensure_index: bool = True,
) -> IngestResult:
    """Ingest multiple zip parts; first part may create the unique index."""
    paths = [Path(p) for p in sources]
    if not paths:
        raise ValueError("sources must not be empty")
    rows = 0
    batches = 0
    for i, path in enumerate(paths):
        result = ingest_complaints_zip(
            path,
            collection,
            batch_size=batch_size,
            ensure_index=(ensure_index and i == 0),
        )
        rows += result.rows_loaded
        batches += result.batch_count
    return IngestResult(rows_loaded=rows, batch_count=batches)
