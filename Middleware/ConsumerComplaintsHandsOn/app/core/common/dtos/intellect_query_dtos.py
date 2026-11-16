"""Ctx for Intellect local vector query (D90)."""

from dataclasses import dataclass, field


@dataclass
class IntellectHit:
    id: str
    text: str
    score: float


@dataclass
class IntellectQueryReq:
    query: str | None = None
    limit: int = 5


@dataclass
class IntellectQueryResp:
    hits: list[IntellectHit] = field(default_factory=list)
    code: int = 0
    error: str = ""


@dataclass
class IntellectQueryCtx:
    req: IntellectQueryReq = field(default_factory=IntellectQueryReq)
    resp: IntellectQueryResp = field(default_factory=IntellectQueryResp)
