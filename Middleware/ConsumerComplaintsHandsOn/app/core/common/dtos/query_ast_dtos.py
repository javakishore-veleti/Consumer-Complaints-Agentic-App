"""Ctx for Intellect Query AST gateway (M52-0001 / #352)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryAstReq:
    ast: dict[str, Any] | None = None
    execute: bool = False


@dataclass
class QueryAstResp:
    sql: str = ""
    executed: bool = False
    count: int | None = None
    k_anon_ok: bool | None = None
    code: int = 0
    error: str = ""


@dataclass
class QueryAstCtx:
    req: QueryAstReq = field(default_factory=QueryAstReq)
    resp: QueryAstResp = field(default_factory=QueryAstResp)
