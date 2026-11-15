"""Hands the report to the service, which validates it and changes both logs in one transaction, and puts the
service's response on the facade ctx."""

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.facades.wf_exec_status_facade_task import WfExecStatusFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class WfExecStatusCallServiceTask(WfExecStatusFacadeTask):
    def execute(self, ctx: WfExecStatusFacadeCtx) -> int:
        ctx.status_ctx = WfExecStatusCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_wf_exec_status_service().record(ctx.status_ctx)
        ctx.resp = ctx.status_ctx.resp
        return code
