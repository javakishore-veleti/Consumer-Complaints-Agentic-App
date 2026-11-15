"""Hands the list to the service and puts the service's response on the facade ctx."""

from app.core.common.dtos.wf_list_dtos import WfListCtx
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.facades.wf_list_facade_task import WfListFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class WfListCallServiceTask(WfListFacadeTask):
    def execute(self, ctx: WfListFacadeCtx) -> int:
        ctx.list_ctx = WfListCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_wf_list_service().list(ctx.list_ctx)
        ctx.resp = ctx.list_ctx.resp
        return code
