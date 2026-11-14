"""Ctx, Req and Resp for the app_workflows_exec_log table (every execution of every workflow, DESIGN.md D50)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class AppWfExecLogRecord:
    id: str
    workflow_id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    config_used: dict | None
    engine_run_id: str | None
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


@dataclass
class AppWfExecLogReq:
    """A field left as None means "not given". id identifies one row. workflow_id is what create needs and list
    filters on; engine_type and status are list filters; status, engine_run_id and message are what update changes."""

    id: str | None = None
    workflow_id: str | None = None
    engine_type: str | None = None
    status: str | None = None
    engine_run_id: str | None = None
    message: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class AppWfExecLogResp:
    records: list[AppWfExecLogRecord] = field(default_factory=list)


@dataclass
class AppWfExecLogCtx(TransactionalCtx):
    req: AppWfExecLogReq = field(default_factory=AppWfExecLogReq)
    resp: AppWfExecLogResp = field(default_factory=AppWfExecLogResp)
