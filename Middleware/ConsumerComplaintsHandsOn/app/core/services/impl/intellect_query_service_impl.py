"""Rank local JSONL vectors for Intellect (D90 / D93 retrieval ladder)."""

import logging

from app.core.common.dtos.intellect_query_dtos import IntellectHit, IntellectQueryCtx
from app.core.common.retrieval_ladder import (
    CONFIG_BASELINE,
    LoadJsonlCorpusReq,
    NormalizeConfigReq,
    RetrievalReq,
    load_jsonl_corpus,
    normalize_config,
    retrieve,
)
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.common.vector_search import ResolveStorePathReq, resolve_store_path
from app.core.services.intellect_query_service import IntellectQueryService

log = logging.getLogger(__name__)


class IntellectQueryServiceImpl(IntellectQueryService):
    def query(self, ctx: IntellectQueryCtx) -> int:
        ctx.resp.hits = []
        ctx.resp.error = ""
        ctx.resp.config = CONFIG_BASELINE
        q = (ctx.req.query or "").strip()
        if not q:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = "query is required"
            return INVALID_INPUT
        limit = ctx.req.limit if ctx.req.limit and ctx.req.limit > 0 else 5
        try:
            config = normalize_config(NormalizeConfigReq(value=ctx.req.config))
            ctx.resp.config = config
            store = resolve_store_path(ResolveStorePathReq())
            corpus = load_jsonl_corpus(LoadJsonlCorpusReq(store_path=store))
            hits = retrieve(RetrievalReq(query=q, corpus=corpus, limit=limit, config=config))
            ctx.resp.hits = [IntellectHit(id=h["id"], text=h["text"], score=float(h["score"])) for h in hits]
            ctx.resp.code = SUCCESS
            return SUCCESS
        except ValueError as exc:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = str(exc)
            return INVALID_INPUT
        except Exception:
            log.exception("intellect query failed")
            ctx.resp.code = FAILURE
            ctx.resp.error = "query failed"
            return FAILURE
