"""WfExecStatusService: the execution and its MIO ingest row change in one transaction (D39, D60).

Each step takes the ctx and returns an integer code; the first step that does not return SUCCESS stops the run and the
transaction is rolled back, otherwise it is committed. The service is a singleton and keeps no per-call state.
"""

import logging

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.wf_exec_status_service import WfExecStatusService

log = logging.getLogger(__name__)

REPORTED_STATUSES = (ExecStatus.STARTED.value, ExecStatus.COMPLETED.value, ExecStatus.FAILED.value)


class WfExecStatusServiceImpl(WfExecStatusService):
    def __init__(self):
        self._steps = [self._update_execution, self._read_ingest, self._follow_ingest]

    def record(self, ctx: WfExecStatusCtx) -> int:
        ctx.resp.execution = None
        ctx.resp.ingest = None
        if not self._is_valid_report(ctx):
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        transaction_dao = DaoObjectsFactory.get_transaction_dao()
        ctx.transaction = TransactionCtx()
        code = transaction_dao.begin(ctx.transaction)
        if code != SUCCESS:
            ctx.transaction = None
            ctx.resp.code = code
            return code
        try:
            for step in self._steps:
                code = step(ctx)
                if code != SUCCESS:
                    break
        except Exception:
            log.exception("workflow execution status report failed")
            code = FAILURE
        if code == SUCCESS:
            code = transaction_dao.commit(ctx.transaction)
        else:
            transaction_dao.rollback(ctx.transaction)
        ctx.transaction = None
        if code != SUCCESS:
            ctx.resp.execution = None
            ctx.resp.ingest = None
        ctx.resp.code = code
        return code

    # ---- steps (each takes the ctx; the shared transaction is ctx.transaction)

    @staticmethod
    def _is_valid_report(ctx: WfExecStatusCtx) -> bool:
        execution_id = ctx.req.execution_id
        has_id = isinstance(execution_id, str) and bool(execution_id.strip())
        return has_id and ctx.req.status in REPORTED_STATUSES

    @staticmethod
    def _update_execution(ctx: WfExecStatusCtx) -> int:
        req = ctx.req
        change = AppWfExecLogReq(
            id=req.execution_id, status=req.status, engine_run_id=req.engine_run_id, message=req.message
        )
        dao_ctx = AppWfExecLogCtx(req=change, transaction=ctx.transaction)
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().update(dao_ctx)
        if code == SUCCESS:
            ctx.resp.execution = dao_ctx.resp.records[0]
        return code  # NOT_FOUND, INVALID_INPUT and CONFLICT describe the execution

    @staticmethod
    def _read_ingest(ctx: WfExecStatusCtx) -> int:
        ingest_id = ctx.resp.execution.mios_ingest_log_id
        if ingest_id is None:
            return SUCCESS  # a workflow without a MIO: only the execution changes
        dao_ctx = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id), transaction=ctx.transaction)
        code = DaoObjectsFactory.get_mio_ingest_log_dao().get(dao_ctx)
        if code != SUCCESS:
            log.error("mios_ingest_log row %s of execution %s cannot be read", ingest_id, ctx.resp.execution.id)
            return FAILURE  # the reference never dangles (no delete, D58); NOT_FOUND here would describe the execution
        ctx.resp.ingest = dao_ctx.resp.records[0]
        return SUCCESS

    def _follow_ingest(self, ctx: WfExecStatusCtx) -> int:
        if ctx.resp.ingest is None:
            return SUCCESS
        req = ctx.req
        target = self._ingest_target(ctx)
        change = MioIngestLogReq(
            id=ctx.resp.ingest.id,
            status=target,
            message=req.message if target is not None else None,
            rows_loaded=req.rows_loaded,
            batch_count=req.batch_count,
            increment_marker=req.increment_marker,
        )
        dao_ctx = MioIngestLogCtx(req=change, transaction=ctx.transaction)
        code = DaoObjectsFactory.get_mio_ingest_log_dao().update(dao_ctx)
        if code == SUCCESS:
            ctx.resp.ingest = dao_ctx.resp.records[0]
            return SUCCESS
        if code == INVALID_INPUT:
            return INVALID_INPUT  # an invalid volume field
        # CONFLICT (a rival moved the ingest between the read and the write) or FAILURE: retryable, and never the
        # execution's 409.
        log.warning("mios_ingest_log row %s could not follow execution %s", change.id, ctx.resp.execution.id)
        return FAILURE

    def _ingest_target(self, ctx: WfExecStatusCtx) -> str | None:
        """The status the ingest moves to after this report, or None to leave its status as it is."""
        execution = ExecStatus(ctx.resp.execution.status)
        ingest = ExecStatus(ctx.resp.ingest.status)
        if execution == ExecStatus.COMPLETED and not self._every_execution_completed(ctx):
            return None
        return execution.value if execution in ingest.next_statuses else None

    @staticmethod
    def _every_execution_completed(ctx: WfExecStatusCtx) -> bool:
        """True when every execution of the ingest (this one included, already changed in this transaction) is
        completed."""
        req = AppWfExecLogReq(mios_ingest_log_id=ctx.resp.ingest.id)
        dao_ctx = AppWfExecLogCtx(req=req, transaction=ctx.transaction)
        if DaoObjectsFactory.get_app_wf_exec_log_dao().list(dao_ctx) != SUCCESS:
            raise RuntimeError("the executions of the ingest cannot be listed")
        return all(record.status == ExecStatus.COMPLETED.value for record in dao_ctx.resp.records)
