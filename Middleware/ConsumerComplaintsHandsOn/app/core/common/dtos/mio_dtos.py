"""Ctx, Req and Resp for the mios table (managed information objects, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioRecord:
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class MioReq:
    """A field left as None means "not given". id (or, for get, name) identifies one row."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


@dataclass
class MioResp:
    records: list[MioRecord] = field(default_factory=list)


@dataclass
class MioCtx(TransactionalCtx):
    req: MioReq = field(default_factory=MioReq)
    resp: MioResp = field(default_factory=MioResp)
