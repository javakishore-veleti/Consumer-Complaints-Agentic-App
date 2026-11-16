"""Ctx, Req and Resp for mios_acl (who may start a MIO, DESIGN.md D89)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioAclRecord:
    id: str
    mio_id: str
    audience: str
    created_at: datetime


@dataclass
class MioAclReq:
    id: str | None = None
    mio_id: str | None = None
    audience: str | None = None


@dataclass
class MioAclResp:
    records: list[MioAclRecord] = field(default_factory=list)


@dataclass
class MioAclCtx(TransactionalCtx):
    req: MioAclReq = field(default_factory=MioAclReq)
    resp: MioAclResp = field(default_factory=MioAclResp)
