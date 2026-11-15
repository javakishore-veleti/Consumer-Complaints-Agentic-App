"""Ctx, Req and Resp for the mios_workflows table (which workflows a MIO may start, DESIGN.md D84)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioWorkflowRecord:
    id: str
    mio_id: str
    workflow_id: str
    created_at: datetime


@dataclass
class MioWorkflowReq:
    """A field left as None means "not given". id identifies one row (get, delete)."""

    id: str | None = None
    mio_id: str | None = None
    workflow_id: str | None = None


@dataclass
class MioWorkflowResp:
    records: list[MioWorkflowRecord] = field(default_factory=list)


@dataclass
class MioWorkflowCtx(TransactionalCtx):
    req: MioWorkflowReq = field(default_factory=MioWorkflowReq)
    resp: MioWorkflowResp = field(default_factory=MioWorkflowResp)
