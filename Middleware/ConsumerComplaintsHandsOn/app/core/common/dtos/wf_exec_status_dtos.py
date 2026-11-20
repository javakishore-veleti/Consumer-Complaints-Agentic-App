"""Ctx, Req and Resp of the workflow execution status service: an engine reports a status of one execution, and the
execution log and its MIO ingest log row change together in one transaction (DESIGN.md D60)."""

from dataclasses import dataclass, field

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogRecord
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogRecord
from app.core.common.dtos.transaction_dtos import TransactionalCtx
from app.core.common.return_codes import SUCCESS


@dataclass
class WfExecStatusReq:
    """What the engine reports. A field left as None means "not given". status is started, completed or failed;
    engine_run_id and message go to the execution; rows_loaded, batch_count and increment_marker go to the ingest row
    (ignored when the execution has none). invoked_configs / invoked_info append to wf_engine_data_json only when
    at least one is non-null."""

    execution_id: str | None = None
    status: str | None = None
    engine_run_id: str | None = None
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None
    invoked_configs: dict | None = None
    invoked_info: dict | None = None


@dataclass
class WfExecStatusResp:
    execution: AppWfExecLogRecord | None = None  # the execution after the call
    ingest: MioIngestLogRecord | None = None  # its ingest row after the call; None when it has none
    code: int = SUCCESS


@dataclass
class WfExecStatusCtx(TransactionalCtx):  # carries the transaction the service opens for the call
    req: WfExecStatusReq = field(default_factory=WfExecStatusReq)
    resp: WfExecStatusResp = field(default_factory=WfExecStatusResp)
