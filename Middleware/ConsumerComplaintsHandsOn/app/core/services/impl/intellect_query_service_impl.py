"""Rank local JSONL vectors for Intellect (D90)."""

import logging

from app.core.common.dtos.intellect_query_dtos import IntellectHit, IntellectQueryCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.common.vector_search import ResolveStorePathReq, SearchLocalVectorsReq, resolve_store_path, search_local_vectors
from app.core.services.intellect_query_service import IntellectQueryService

log = logging.getLogger(__name__)


class IntellectQueryServiceImpl(IntellectQueryService):
    def query(self, ctx: IntellectQueryCtx) -> int:
        ctx.resp.hits = []
        ctx.resp.error = ""
        q = (ctx.req.query or "").strip()
        if not q:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = "query is required"
            return INVALID_INPUT
        limit = ctx.req.limit if ctx.req.limit and ctx.req.limit > 0 else 5
        try:
            store = resolve_store_path(ResolveStorePathReq())
            hits = search_local_vectors(
                SearchLocalVectorsReq(query=q, store_path=store, limit=limit)
            )
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
