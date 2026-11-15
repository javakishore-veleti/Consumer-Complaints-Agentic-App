"""Hands the prepare step to StartWfService."""

from app.core.common.dtos.start_wf_dtos import StartWfCtx
from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.facades.start_wf_facade_task import StartWfFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class StartWfCallServiceTask(StartWfFacadeTask):
    def execute(self, ctx: StartWfFacadeCtx) -> int:
        ctx.start_ctx = StartWfCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_start_wf_service().start(ctx.start_ctx)
        ctx.resp.execution_id = ctx.start_ctx.resp.execution_id
        ctx.resp.code = code
        return code
