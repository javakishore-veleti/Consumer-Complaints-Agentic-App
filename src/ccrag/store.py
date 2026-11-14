"""Storage and search: pgvector for vectors, an in-memory BM25 index per filter, and the catalog of values.

A *filter* is `None` (search everything) or a tuple of `(column, value)` pairs, e.g.
`(("product", "Mortgage"), ("year", 2025))`. All pairs must match. The same filter drives the SQL `WHERE`
for vector search and the Python predicate for BM25, so both retrievers always see the same subset.
"""
import re
from collections import Counter
from dataclasses import dataclass
from functools import cache

import psycopg
from rank_bm25 import BM25Okapi

from .chunking import FILTER_COLUMNS, Chunk
from .config import DATABASE_URL, EMBED_DIM, TABLE
from . import llm

Filter = tuple[tuple[str, object], ...] | None


def as_filter(pairs) -> Filter:
    """Normalise a filter that came back from JSON (lists) or from a planner (dict) into a hashable tuple."""
    if not pairs:
        return None
    items = pairs.items() if isinstance(pairs, dict) else pairs
    return tuple(sorted((k, v) for k, v in items)) or None


def passes(chunk: Chunk, filter: Filter) -> bool:
    return filter is None or all(chunk.meta.get(k) == v for k, v in filter)


def _where(filter: Filter) -> tuple[str, list]:
    if not filter:
        return "", []
    for column, _ in filter:
        if column not in FILTER_COLUMNS:
            raise ValueError(f"cannot filter on {column!r}")
    return "WHERE " + " AND ".join(f"{c} = %s" for c, _ in filter), [v for _, v in filter]


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, autocommit=True)


def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"


# ---------------------------------------------------------------- building the table

DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE {TABLE} (
    chunk_id text PRIMARY KEY, kind text, doc_id text, chunk_index int, n_tokens int, content text,
    embedding vector({EMBED_DIM}),
    complaint_id text, date_received date, year int, product text, sub_product text, issue text, sub_issue text,
    company text, state text, company_response text, submitted_via text, timely boolean,
    older_american boolean, servicemember boolean
)"""
COLUMNS = ["chunk_id", "kind", "doc_id", "chunk_index", "n_tokens", "content", "embedding", "complaint_id",
           "date_received", "year", "product", "sub_product", "issue", "sub_issue", "company", "state",
           "company_response", "submitted_via", "timely", "older_american", "servicemember"]


def table_exists(conn) -> bool:
    return conn.execute("SELECT to_regclass(%s)", (TABLE,)).fetchone()[0] is not None


def build_table(conn, chunks: list[Chunk], vectors: list[list[float]]) -> None:
    conn.execute(DDL)
    placeholders = ", ".join("%s::vector" if c == "embedding" else "%s" for c in COLUMNS)
    rows = []
    for c, v in zip(chunks, vectors):
        m = c.meta
        rows.append([c.id, m["kind"], m["doc_id"], m["chunk_index"], m["n_tokens"], c.text, _vec(v),
                     m.get("complaint_id"), m.get("date_received"), m.get("year"), m.get("product"),
                     m.get("sub_product"), m.get("issue"), m.get("sub_issue"), m.get("company"), m.get("state"),
                     m.get("company_response"), m.get("submitted_via"), m.get("timely"), m.get("older_american"),
                     m.get("servicemember")])
    with conn.cursor() as cur:
        cur.executemany(f"INSERT INTO {TABLE} ({', '.join(COLUMNS)}) VALUES ({placeholders})", rows)


def index(chunks: list[Chunk], rebuild: bool = False) -> int:
    """Embed the chunks and write them to Postgres. Does nothing if the table already exists."""
    with connect() as conn:
        if table_exists(conn):
            if not rebuild:
                return conn.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
            conn.execute(f"DROP TABLE {TABLE}")
        build_table(conn, chunks, llm.embed([c.text for c in chunks]))
        return conn.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]


# ---------------------------------------------------------------- vector search

def vector_ids(query_vector: list[float], k: int, filter: Filter) -> list[str]:
    where, params = _where(filter)
    with connect() as conn:
        rows = conn.execute(f"SELECT chunk_id FROM {TABLE} {where} ORDER BY embedding <=> %s::vector LIMIT %s",
                            [*params, _vec(query_vector), k]).fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------- BM25

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        self.ids = [c.id for c in chunks]
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks]) if chunks else None

    def search(self, query: str, k: int) -> list[str]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)[:k]
        return [self.ids[i] for i in ranked if scores[i] > 0]


# ---------------------------------------------------------------- catalog

@dataclass
class Catalog:
    """What is in the index. The self-query planner reads it, and `to_filter` validates against it."""
    products: list[str]
    companies: dict[str, int]       # every company in the index -> number of complaints
    states: list[str]
    years: list[int]
    responses: list[str]
    channels: list[str]

    def top_companies(self, n: int = 120) -> list[str]:
        return [c for c, _ in sorted(self.companies.items(), key=lambda kv: -kv[1])[:n]]


def catalog_from_chunks(chunks: list[Chunk]) -> Catalog:
    cs = [c.meta for c in chunks if c.meta["kind"] == "complaint"]
    count = lambda key: Counter(m[key] for m in cs if m.get(key) is not None)
    return Catalog(
        products=[p for p, _ in count("product").most_common()],
        companies=dict(count("company")),
        states=sorted(count("state")),
        years=sorted(count("year")),
        responses=[p for p, _ in count("company_response").most_common()],
        channels=[p for p, _ in count("submitted_via").most_common()])
