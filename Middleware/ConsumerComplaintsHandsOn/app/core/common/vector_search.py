"""Local JSONL vector search for Intellect (D88/D90). Mirrors Airflow hash embeddings."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


DEFAULT_COLLECTION = "complaints"
DEFAULT_DIM = 32


@dataclass
class HashEmbeddingReq:
    text: str
    dim: int = DEFAULT_DIM


@dataclass
class CosineReq:
    a: list[float]
    b: list[float]


@dataclass
class ResolveStorePathReq:
    getenv: Callable[..., str | None] = field(default=os.getenv)


@dataclass
class SearchLocalVectorsReq:
    query: str
    store_path: Path
    limit: int = 5
    collection: str = DEFAULT_COLLECTION


def hash_embedding(req: HashEmbeddingReq) -> list[float]:
    digest = hashlib.sha256((req.text or "").encode("utf-8")).digest()
    out: list[float] = []
    i = 0
    while len(out) < req.dim:
        chunk = digest[i % len(digest)]
        out.append((chunk / 127.5) - 1.0)
        i += 1
        digest = hashlib.sha256(digest + bytes([i])).digest()
    return out[: req.dim]


def cosine(req: CosineReq) -> float:
    a, b = req.a, req.b
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def resolve_store_path(req: ResolveStorePathReq | None = None) -> Path:
    req = req or ResolveStorePathReq()
    value = (req.getenv("CCA_VECTOR_STORE_PATH") or "").strip()
    if not value:
        raise ValueError("CCA_VECTOR_STORE_PATH is required")
    return Path(value)


def search_local_vectors(req: SearchLocalVectorsReq) -> list[dict[str, Any]]:
    if req.limit < 1:
        raise ValueError("limit must be >= 1")
    path = req.store_path / f"{req.collection}.jsonl"
    if not path.is_file():
        return []
    q_emb = hash_embedding(HashEmbeddingReq(text=req.query))
    scored: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        emb = row.get("embedding") or hash_embedding(HashEmbeddingReq(text=str(row.get("text") or "")))
        score = cosine(CosineReq(a=q_emb, b=list(emb)))
        scored.append({"id": str(row.get("id") or ""), "text": str(row.get("text") or ""), "score": score})
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[: req.limit]
