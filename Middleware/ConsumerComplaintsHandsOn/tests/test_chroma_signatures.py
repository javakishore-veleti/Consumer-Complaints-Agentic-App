"""Chroma / JSONL signature catalog helpers (M52-0003 / #354)."""

import json
from pathlib import Path

from app.core.common.chroma_signatures import (
    ChromaQueryReq,
    LoadSignaturesJsonlReq,
    load_signatures_jsonl,
    query_chroma_signatures,
)
from app.core.common.vector_search import HashEmbeddingReq, hash_embedding


def test_load_signatures_jsonl_empty_when_missing(tmp_path: Path):
    assert load_signatures_jsonl(LoadSignaturesJsonlReq(store_path=tmp_path)) == []


def test_load_signatures_jsonl_reads_rows(tmp_path: Path):
    store = tmp_path
    row = {
        "id": "sig-1",
        "text": "Credit card | Billing | Credit Cards",
        "embedding": hash_embedding(HashEmbeddingReq(text="Credit card Billing")),
    }
    (store / "cfpb_semantic_signatures.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    rows = load_signatures_jsonl(LoadSignaturesJsonlReq(store_path=store))
    assert len(rows) == 1
    assert rows[0]["id"] == "sig-1"


def test_query_chroma_signatures_uses_injectable_client():
    class _Client:
        def ensure_collection(self, name: str) -> str:
            assert name == "cfpb_semantic_signatures"
            return "cid-1"

        def query(self, collection_id: str, *, query_embeddings, n_results: int = 3, include=None):
            assert collection_id == "cid-1"
            assert n_results == 2
            return {
                "ids": [["sig-a", "sig-b"]],
                "documents": [["Credit Cards topic", "Mortgages topic"]],
                "distances": [[0.1, 0.5]],
            }

    hits = query_chroma_signatures(
        ChromaQueryReq(base_url="http://chroma.test", query="credit cards", limit=2, client=_Client())
    )
    assert [h["id"] for h in hits] == ["sig-a", "sig-b"]
    assert hits[0]["score"] > hits[1]["score"]


def test_query_chroma_unreachable_returns_empty():
    hits = query_chroma_signatures(
        ChromaQueryReq(base_url="http://127.0.0.1:1", query="x", limit=3)
    )
    assert hits == []
