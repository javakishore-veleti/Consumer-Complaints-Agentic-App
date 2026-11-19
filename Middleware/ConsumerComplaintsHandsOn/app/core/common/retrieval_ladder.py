"""Intellect retrieval ladder: baseline → hybrid → stubs → rerank (D93). No paid APIs."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.common.vector_search import (
    CosineReq,
    HashEmbeddingReq,
    DEFAULT_COLLECTION,
    cosine,
    hash_embedding,
)

CONFIG_BASELINE = "baseline"
CONFIG_HYBRID = "hybrid"
CONFIG_SELF_QUERY = "self_query"
CONFIG_DECOMPOSE = "decompose"
CONFIG_RERANKER = "reranker"
CONFIG_EVERYTHING = "everything"
CONFIG_SIGNATURES = "signatures"

LADDER_CONFIGS: tuple[str, ...] = (
    CONFIG_BASELINE,
    CONFIG_HYBRID,
    CONFIG_SELF_QUERY,
    CONFIG_DECOMPOSE,
    CONFIG_RERANKER,
    CONFIG_EVERYTHING,
    CONFIG_SIGNATURES,
)

RRF_K = 60
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are", "was", "with"}


@dataclass
class TokenizeReq:
    text: str


@dataclass
class NormalizeConfigReq:
    value: str | None = None


@dataclass
class LoadJsonlCorpusReq:
    store_path: Path
    collection: str = DEFAULT_COLLECTION


@dataclass
class Bm25ScoresReq:
    query_tokens: list[str]
    docs_tokens: list[list[str]]
    k1: float = 1.5
    b: float = 0.75


@dataclass
class RrfFuseReq:
    rank_lists: list[list[str]]
    k: int = RRF_K


@dataclass
class RankCorpusReq:
    query: str
    corpus: list[dict[str, Any]]


@dataclass
class CorpusIndexReq:
    corpus: list[dict[str, Any]]


@dataclass
class HitsFromScoresReq:
    scored: list[tuple[str, float]]
    by_id: dict[str, dict[str, Any]]
    limit: int


@dataclass
class SelfQueryFilterReq:
    query: str
    corpus: list[dict[str, Any]]


@dataclass
class DecomposeQueryReq:
    query: str


@dataclass
class LexicalRerankReq:
    query: str
    candidates: list[dict[str, Any]]


@dataclass
class RetrievalReq:
    query: str
    corpus: list[dict[str, Any]]
    limit: int = 5
    config: str = CONFIG_BASELINE


def tokenize(req: TokenizeReq) -> list[str]:
    return _TOKEN_RE.findall((req.text or "").lower())


def normalize_config(req: NormalizeConfigReq) -> str:
    kind = (req.value or CONFIG_BASELINE).strip().lower()
    if kind not in LADDER_CONFIGS:
        raise ValueError(f"unknown retrieval config: {req.value!r} (expected {'|'.join(LADDER_CONFIGS)})")
    return kind


def load_jsonl_corpus(req: LoadJsonlCorpusReq) -> list[dict[str, Any]]:
    path = req.store_path / f"{req.collection}.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(
            {
                "id": str(row.get("id") or ""),
                "text": str(row.get("text") or ""),
                "embedding": row.get("embedding"),
            }
        )
    return rows


def bm25_scores(req: Bm25ScoresReq) -> list[float]:
    """Okapi BM25 over an in-memory tokenized corpus."""
    docs_tokens = req.docs_tokens
    n = len(docs_tokens)
    if n == 0:
        return []
    avgdl = sum(len(d) for d in docs_tokens) / n
    df: dict[str, int] = {}
    for toks in docs_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    scores = [0.0] * n
    for qi in req.query_tokens:
        ni = df.get(qi, 0)
        if ni == 0:
            continue
        idf = math.log(1.0 + (n - ni + 0.5) / (ni + 0.5))
        for i, toks in enumerate(docs_tokens):
            tf = toks.count(qi)
            if tf == 0:
                continue
            dl = len(toks) or 1
            denom = tf + req.k1 * (1.0 - req.b + req.b * dl / avgdl)
            scores[i] += idf * (tf * (req.k1 + 1.0)) / denom
    return scores


def rrf_fuse(req: RrfFuseReq) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion over ordered id lists (best-first)."""
    scores: dict[str, float] = {}
    for ranks in req.rank_lists:
        for rank, doc_id in enumerate(ranks, start=1):
            if not doc_id:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (req.k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _vector_ranked(req: RankCorpusReq) -> list[tuple[str, float]]:
    q_emb = hash_embedding(HashEmbeddingReq(text=req.query))
    scored: list[tuple[str, float]] = []
    for row in req.corpus:
        emb = row.get("embedding") or hash_embedding(HashEmbeddingReq(text=row["text"]))
        score = cosine(CosineReq(a=q_emb, b=list(emb)))
        scored.append((row["id"], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _bm25_ranked(req: RankCorpusReq) -> list[tuple[str, float]]:
    q_toks = tokenize(TokenizeReq(text=req.query))
    docs_toks = [tokenize(TokenizeReq(text=r["text"])) for r in req.corpus]
    scores = bm25_scores(Bm25ScoresReq(query_tokens=q_toks, docs_tokens=docs_toks))
    ranked = [(req.corpus[i]["id"], scores[i]) for i in range(len(req.corpus))]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def _by_id(req: CorpusIndexReq) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in req.corpus if r.get("id")}


def _hits_from_scores(req: HitsFromScoresReq) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for doc_id, score in req.scored[: req.limit]:
        row = req.by_id.get(doc_id)
        if not row:
            continue
        out.append({"id": doc_id, "text": row["text"], "score": float(score)})
    return out


def self_query_filter(req: SelfQueryFilterReq) -> list[dict[str, Any]]:
    """Heuristic stub (no LLM): keep docs that share ≥1 non-stop token with the query."""
    q_toks = {t for t in tokenize(TokenizeReq(text=req.query)) if t not in _STOP}
    if not q_toks:
        return list(req.corpus)
    filtered = [r for r in req.corpus if q_toks.intersection(tokenize(TokenizeReq(text=r["text"])))]
    return filtered or list(req.corpus)


def decompose_query(req: DecomposeQueryReq) -> list[str]:
    """Heuristic stub (no LLM): split on ' and ' / '?' / ';', else whole query."""
    parts = re.split(r"\s+and\s+|[?;]", req.query, flags=re.IGNORECASE)
    cleaned = [p.strip() for p in parts if p and p.strip()]
    return cleaned or [req.query.strip()]


def lexical_rerank(req: LexicalRerankReq) -> list[dict[str, Any]]:
    """Local rerank: boost by overlapping token count / query length."""
    q_toks = tokenize(TokenizeReq(text=req.query))
    if not q_toks:
        return req.candidates
    rescored: list[dict[str, Any]] = []
    for hit in req.candidates:
        overlap = sum(1 for t in q_toks if t in tokenize(TokenizeReq(text=hit["text"])))
        boost = overlap / len(q_toks)
        rescored.append({**hit, "score": float(hit["score"]) + boost})
    rescored.sort(key=lambda h: h["score"], reverse=True)
    return rescored


def _hybrid_scored(req: RankCorpusReq) -> list[tuple[str, float]]:
    # Double-weight BM25 in RRF: hash embeddings are non-semantic (D88/D93 MVP),
    # so lexical ranks must dominate noise from vector ranks.
    vec = [doc_id for doc_id, _ in _vector_ranked(req)]
    bm = [doc_id for doc_id, _ in _bm25_ranked(req)]
    return rrf_fuse(RrfFuseReq(rank_lists=[bm, bm, vec]))


def retrieve(req: RetrievalReq) -> list[dict[str, Any]]:
    if req.limit < 1:
        raise ValueError("limit must be >= 1")
    config = normalize_config(NormalizeConfigReq(value=req.config))
    corpus = list(req.corpus)
    query = (req.query or "").strip()
    if not query:
        return []
    by_id = _by_id(CorpusIndexReq(corpus=corpus))
    if not by_id:
        return []
    rank_req = RankCorpusReq(query=query, corpus=corpus)

    if config in (CONFIG_BASELINE, CONFIG_SIGNATURES):
        return _hits_from_scores(
            HitsFromScoresReq(scored=_vector_ranked(rank_req), by_id=by_id, limit=req.limit)
        )

    if config == CONFIG_HYBRID:
        return _hits_from_scores(
            HitsFromScoresReq(scored=_hybrid_scored(rank_req), by_id=by_id, limit=req.limit)
        )

    if config == CONFIG_SELF_QUERY:
        filtered = self_query_filter(SelfQueryFilterReq(query=query, corpus=corpus))
        f_req = RankCorpusReq(query=query, corpus=filtered)
        return _hits_from_scores(
            HitsFromScoresReq(
                scored=_hybrid_scored(f_req),
                by_id=_by_id(CorpusIndexReq(corpus=filtered)),
                limit=req.limit,
            )
        )

    if config == CONFIG_DECOMPOSE:
        subqs = decompose_query(DecomposeQueryReq(query=query))
        rank_lists: list[list[str]] = []
        for sub in subqs:
            rank_lists.append(
                [doc_id for doc_id, _ in _hybrid_scored(RankCorpusReq(query=sub, corpus=corpus))]
            )
        fused = rrf_fuse(RrfFuseReq(rank_lists=rank_lists))
        return _hits_from_scores(HitsFromScoresReq(scored=fused, by_id=by_id, limit=req.limit))

    if config == CONFIG_RERANKER:
        pool = _hits_from_scores(
            HitsFromScoresReq(scored=_hybrid_scored(rank_req), by_id=by_id, limit=max(req.limit * 3, 15))
        )
        return lexical_rerank(LexicalRerankReq(query=query, candidates=pool))[: req.limit]

    filtered = self_query_filter(SelfQueryFilterReq(query=query, corpus=corpus))
    f_by = _by_id(CorpusIndexReq(corpus=filtered))
    subqs = decompose_query(DecomposeQueryReq(query=query))
    rank_lists = []
    for sub in subqs:
        rank_lists.append(
            [doc_id for doc_id, _ in _hybrid_scored(RankCorpusReq(query=sub, corpus=filtered))]
        )
    fused = rrf_fuse(RrfFuseReq(rank_lists=rank_lists))
    pool = _hits_from_scores(HitsFromScoresReq(scored=fused, by_id=f_by, limit=max(req.limit * 3, 15)))
    return lexical_rerank(LexicalRerankReq(query=query, candidates=pool))[: req.limit]
