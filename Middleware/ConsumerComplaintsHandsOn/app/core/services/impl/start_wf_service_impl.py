"""Look up the workflow, optional ingest + location checks, create the exec log (D68/D73)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.start_wf_dtos import StartWfCtx
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory
from app.core.services.start_wf_service import StartWfService


class StartWfServiceImpl(StartWfService):
    def start(self, ctx: StartWfCtx) -> int:
        ctx.resp.execution_id = None
        ctx.resp.engine_type = None
        workflow_id = (ctx.req.workflow_id or "").strip()
        if not workflow_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT

        wf_ctx = AppWfCtx(req=AppWfReq(id=workflow_id))
        code = DaoObjectsFactory.get_app_wf_dao().get(wf_ctx)
        if code == NOT_FOUND:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        workflow = wf_ctx.resp.records[0]
        registered = {e.engine_type for e in ServicesObjectsFactory.get_workflow_engines()}
        if not workflow.enabled or workflow.engine_type not in registered:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT

        location_id = ctx.req.dataset_location_id
        if location_id is not None:
            location_id = location_id.strip()
            if not location_id:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            loc_ctx = DatasetLocationCtx(req=DatasetLocationReq(id=location_id))
            code = DaoObjectsFactory.get_dataset_location_dao().get(loc_ctx)
            if code != SUCCESS:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT

        ingest_id = None
        mio_id = ctx.req.mio_id
        if mio_id is not None:
            mio_id = mio_id.strip()
            if not mio_id:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            ingest_ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id))
            code = DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest_ctx)
            if code == NOT_FOUND:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            if code != SUCCESS:
                ctx.resp.code = code
                return code
            ingest_id = ingest_ctx.resp.records[0].id

        exec_ctx = AppWfExecLogCtx(
            req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=ingest_id)
        )
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().create(exec_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.execution_id = exec_ctx.resp.records[0].id
        ctx.resp.engine_type = workflow.engine_type
        ctx.resp.code = SUCCESS
        return SUCCESS
