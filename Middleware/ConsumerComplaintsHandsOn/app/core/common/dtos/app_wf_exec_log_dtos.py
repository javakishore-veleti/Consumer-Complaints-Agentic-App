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
    mios_ingest_log_id: str | None
    wf_engine_data_json: dict | None = None
    wf_exec_data_json: dict | None = None


@dataclass
class AppWfExecLogReq:
    """A field left as None means "not given". id identifies one row. workflow_id is what create needs and list
    filters on; mios_ingest_log_id is optional on create and a list filter; engine_type and status are list filters;
    status, engine_run_id and message are what update changes. List also accepts workflow_name_prefix(es),
    workflow_name_exclude_prefix, requested_after/before, and engine_run_id exact match.
    append_engine_invocation / append_exec_invocation: when set, append that element to the JSON chronicle."""

    id: str | None = None
    workflow_id: str | None = None
    engine_type: str | None = None
    status: str | None = None
    engine_run_id: str | None = None
    message: str | None = None
    mios_ingest_log_id: str | None = None
    workflow_name_prefix: str | None = None
    workflow_name_prefixes: list[str] | None = None
    workflow_name_exclude_prefix: str | None = None
    requested_after: datetime | None = None
    requested_before: datetime | None = None
    append_engine_invocation: dict | None = None
    append_exec_invocation: dict | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class AppWfExecLogResp:
    records: list[AppWfExecLogRecord] = field(default_factory=list)


@dataclass
class AppWfExecLogCtx(TransactionalCtx):
    req: AppWfExecLogReq = field(default_factory=AppWfExecLogReq)
    resp: AppWfExecLogResp = field(default_factory=AppWfExecLogResp)
