"""Query Chroma cfpb_semantic_signatures (or local JSONL mirror) for Intellect (M52-0003 / #354)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NamedTuple

from app.core.common.vector_search import HashEmbeddingReq, hash_embedding

SIGNATURE_COLLECTION = "cfpb_semantic_signatures"
DEFAULT_DIM = 32


class ResolveChromaUrlReq(NamedTuple):
    getenv: Any = os.getenv


class LoadSignaturesJsonlReq(NamedTuple):
    store_path: Path
    collection: str = SIGNATURE_COLLECTION


class ChromaQueryReq(NamedTuple):
    base_url: str
    query: str
    limit: int = 5
    collection: str = SIGNATURE_COLLECTION
    client: Any | None = None


def resolve_chroma_url(req: ResolveChromaUrlReq | None = None) -> str:
    req = req or ResolveChromaUrlReq()
    return (req.getenv("CCA_CHROMA_URL") or "").strip()


def load_signatures_jsonl(req: LoadSignaturesJsonlReq) -> list[dict[str, Any]]:
    path = req.store_path / f"{req.collection}.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("id"):
            rows.append(row)
    return rows


class _CollectionIdReq(NamedTuple):
    client: Any
    root: str
    name: str


def _collection_id(req: _CollectionIdReq) -> str:
    client, root, name = req.client, req.root, req.name
    if client is not None and hasattr(client, "ensure_collection"):
        return str(client.ensure_collection(name))
    http_req = urllib.request.Request(
        f"{root}/api/v1/collections",
        data=json.dumps({"name": name, "get_or_create": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        payload = json.loads(urllib.request.urlopen(http_req, timeout=30).read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
        get_req = urllib.request.Request(f"{root}/api/v1/collections/{name}", method="GET")
        payload = json.loads(urllib.request.urlopen(get_req, timeout=30).read().decode("utf-8") or "{}")
    cid = str((payload or {}).get("id") or "").strip()
    if not cid:
        raise ValueError("Chroma collection id missing")
    return cid


def query_chroma_signatures(req: ChromaQueryReq) -> list[dict[str, Any]]:
    """Return hits [{id,text,score}] or [] if Chroma unreachable / empty."""
    root = (req.base_url or "").rstrip("/")
    if not root or not (req.query or "").strip():
        return []
    try:
        cid = _collection_id(_CollectionIdReq(req.client, root, req.collection))
        emb = hash_embedding(HashEmbeddingReq(text=req.query, dim=DEFAULT_DIM))
        body = {
            "query_embeddings": [emb],
            "n_results": max(1, req.limit),
            "include": ["documents", "metadatas", "distances"],
        }
        if req.client is not None and hasattr(req.client, "query"):
            payload = req.client.query(cid, query_embeddings=[emb], n_results=max(1, req.limit))
        else:
            http_req = urllib.request.Request(
                f"{root}/api/v1/collections/{cid}/query",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            payload = json.loads(urllib.request.urlopen(http_req, timeout=60).read().decode("utf-8") or "{}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return []

    ids = (payload.get("ids") or [[]])[0] if payload else []
    docs = (payload.get("documents") or [[]])[0] if payload else []
    dists = (payload.get("distances") or [[]])[0] if payload else []
    hits: list[dict[str, Any]] = []
    for i, doc_id in enumerate(ids or []):
        dist = float(dists[i]) if i < len(dists or []) else 0.0
        score = 1.0 / (1.0 + max(dist, 0.0))
        text = str(docs[i]) if i < len(docs or []) else ""
        hits.append({"id": str(doc_id), "text": text, "score": score})
    return hits
