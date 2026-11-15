"""Ctx, Req and Resp of the MIO status service: every MIO with its latest ingest and that ingest's executions
(DESIGN.md D61)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogRecord
from app.core.common.return_codes import SUCCESS


@dataclass
class MioStatusIngest:
    id: str
    mio_id: str
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    rows_loaded: int | None
    batch_count: int | None
    increment_marker: str | None
    executions: list[AppWfExecLogRecord] = field(default_factory=list)


@dataclass
class MioStatusAllowedWorkflow:
    """Enabled workflow allowed for this MIO (D84). Same fields as GET /workflows (D66), no config."""

    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    enabled: bool


@dataclass
class MioStatusEntry:
    id: str
    name: str
    description: str | None
    latest_ingest: MioStatusIngest | None = None
    allowed_workflows: list[MioStatusAllowedWorkflow] = field(default_factory=list)


@dataclass
class MioStatusReq:
    """Optional mio_id: when given, only that MIO. None means every MIO."""

    mio_id: str | None = None


@dataclass
class MioStatusResp:
    entries: list[MioStatusEntry] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class MioStatusCtx:
    req: MioStatusReq = field(default_factory=MioStatusReq)
    resp: MioStatusResp = field(default_factory=MioStatusResp)
