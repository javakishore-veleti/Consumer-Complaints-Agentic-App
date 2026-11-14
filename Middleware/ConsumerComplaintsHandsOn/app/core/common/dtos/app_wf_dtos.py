"""Ctx, Req and Resp for the app_workflows table (the registry of workflows, DESIGN.md D43)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class AppWfRecord:
    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    config: dict | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class AppWfReq:
    """A field left as None means "not given". id (or, for get, workflow_name) identifies one row."""

    id: str | None = None
    workflow_name: str | None = None
    engine_type: str | None = None
    engine_workflow_id: str | None = None
    config: dict | None = None
    enabled: bool | None = None


@dataclass
class AppWfResp:
    records: list[AppWfRecord] = field(default_factory=list)


@dataclass
class AppWfCtx(TransactionalCtx):
    req: AppWfReq = field(default_factory=AppWfReq)
    resp: AppWfResp = field(default_factory=AppWfResp)
