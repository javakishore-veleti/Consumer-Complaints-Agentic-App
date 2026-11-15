"""Builds one status entry per MIO from the catalog, logs, and allowed workflows (D61 / D84)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq, MioRecord
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq, MioIngestLogRecord
from app.core.common.dtos.mio_status_dtos import (
    MioStatusAllowedWorkflow,
    MioStatusCtx,
    MioStatusEntry,
    MioStatusIngest,
)
from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowReq
from app.core.common.return_codes import FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.mio_status_service import MioStatusService


class MioStatusServiceImpl(MioStatusService):
    def read(self, ctx: MioStatusCtx) -> int:
        mios, code = self._mios(ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        entries: list[MioStatusEntry] = []
        for mio in mios:
            ingest, code = self._latest_ingest(mio)
            if code != SUCCESS:
                ctx.resp.code = code
                return code
            allowed, code = self._allowed_workflows(mio)
            if code != SUCCESS:
                ctx.resp.code = code
                return code
            entries.append(
                MioStatusEntry(
                    id=mio.id,
                    name=mio.name,
                    description=mio.description,
                    latest_ingest=ingest,
                    allowed_workflows=allowed,
                )
            )
        ctx.resp.entries = entries
        ctx.resp.code = SUCCESS
        return SUCCESS

    @staticmethod
    def _mios(ctx: MioStatusCtx) -> tuple[list[MioRecord], int]:
        mio_id = ctx.req.mio_id
        if mio_id is not None:
            if not str(mio_id).strip():
                return [], INVALID_INPUT
            dao_ctx = MioCtx(req=MioReq(id=str(mio_id).strip()))
            code = DaoObjectsFactory.get_mio_dao().get(dao_ctx)
            return (dao_ctx.resp.records, code) if code == SUCCESS else ([], code)
        dao_ctx = MioCtx()
        code = DaoObjectsFactory.get_mio_dao().list(dao_ctx)
        return (dao_ctx.resp.records, code) if code == SUCCESS else ([], code)

    @staticmethod
    def _latest_ingest(mio: MioRecord) -> tuple[MioStatusIngest | None, int]:
        ingest_ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.id, limit=1))
        code = DaoObjectsFactory.get_mio_ingest_log_dao().list(ingest_ctx)
        if code != SUCCESS:
            return None, FAILURE
        if not ingest_ctx.resp.records:
            return None, SUCCESS
        record = ingest_ctx.resp.records[0]
        executions, code = MioStatusServiceImpl._executions(record)
        if code != SUCCESS:
            return None, code
        return (
            MioStatusIngest(
                id=record.id,
                mio_id=record.mio_id,
                status=record.status,
                message=record.message,
                requested_at=record.requested_at,
                started_at=record.started_at,
                finished_at=record.finished_at,
                rows_loaded=record.rows_loaded,
                batch_count=record.batch_count,
                increment_marker=record.increment_marker,
                executions=executions,
            ),
            SUCCESS,
        )

    @staticmethod
    def _executions(ingest: MioIngestLogRecord) -> tuple[list, int]:
        exec_ctx = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=ingest.id))
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().list(exec_ctx)
        if code != SUCCESS:
            return [], FAILURE
        return exec_ctx.resp.records, SUCCESS

    @staticmethod
    def _allowed_workflows(mio: MioRecord) -> tuple[list[MioStatusAllowedWorkflow], int]:
        link_ctx = MioWorkflowCtx(req=MioWorkflowReq(mio_id=mio.id))
        code = DaoObjectsFactory.get_mio_workflow_dao().list(link_ctx)
        if code != SUCCESS:
            return [], FAILURE
        allowed: list[MioStatusAllowedWorkflow] = []
        for link in link_ctx.resp.records:
            wf_ctx = AppWfCtx(req=AppWfReq(id=link.workflow_id))
            code = DaoObjectsFactory.get_app_wf_dao().get(wf_ctx)
            if code == NOT_FOUND:
                continue
            if code != SUCCESS:
                return [], FAILURE
            wf = wf_ctx.resp.records[0]
            if not wf.enabled:
                continue
            allowed.append(
                MioStatusAllowedWorkflow(
                    id=wf.id,
                    workflow_name=wf.workflow_name,
                    engine_type=wf.engine_type,
                    engine_workflow_id=wf.engine_workflow_id,
                    enabled=wf.enabled,
                )
            )
        allowed.sort(key=lambda w: w.workflow_name)
        return allowed, SUCCESS
