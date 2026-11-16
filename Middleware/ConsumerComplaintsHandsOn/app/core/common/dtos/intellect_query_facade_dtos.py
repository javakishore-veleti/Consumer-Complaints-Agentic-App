"""Facade ctx for Intellect query (D90)."""

from dataclasses import dataclass, field

from app.core.common.dtos.intellect_query_dtos import IntellectQueryReq, IntellectQueryResp


@dataclass
class IntellectQueryFacadeCtx:
    req: IntellectQueryReq = field(default_factory=IntellectQueryReq)
    resp: IntellectQueryResp = field(default_factory=IntellectQueryResp)
