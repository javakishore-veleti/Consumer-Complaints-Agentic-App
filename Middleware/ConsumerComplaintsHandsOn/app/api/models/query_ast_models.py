from typing import Any

from pydantic import BaseModel, Field


class QueryAstBody(BaseModel):
    ast: dict[str, Any]
    execute: bool = False
    relax: bool = False


class QueryAstRelaxStepOut(BaseModel):
    step: str
    reason: str
    sql: str
    ast: dict[str, Any] = Field(default_factory=dict)


class QueryAstOut(BaseModel):
    sql: str
    executed: bool = False
    count: int | None = None
    k_anon_ok: bool | None = None
    relaxation: list[QueryAstRelaxStepOut] = Field(default_factory=list)
    error: str = Field(default="")
