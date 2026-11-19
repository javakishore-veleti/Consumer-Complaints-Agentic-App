from typing import Any

from pydantic import BaseModel, Field


class QueryAstBody(BaseModel):
    ast: dict[str, Any]
    execute: bool = False


class QueryAstOut(BaseModel):
    sql: str
    executed: bool = False
    count: int | None = None
    k_anon_ok: bool | None = None
    error: str = Field(default="")
