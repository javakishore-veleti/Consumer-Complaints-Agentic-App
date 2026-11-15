"""Maps AppWfDao.list rows to safe portal entries (D66)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListEntry
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.wf_list_service import WfListService


class WfListServiceImpl(WfListService):
    def list(self, ctx: WfListCtx) -> int:
        dao_ctx = AppWfCtx()
        code = DaoObjectsFactory.get_app_wf_dao().list(dao_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.entries = [
            WfListEntry(
                id=r.id,
                workflow_name=r.workflow_name,
                engine_type=r.engine_type,
                engine_workflow_id=r.engine_workflow_id,
                enabled=r.enabled,
            )
            for r in dao_ctx.resp.records
        ]
        ctx.resp.code = SUCCESS
        return SUCCESS
