from app.core.common.dtos.intellect_query_dtos import IntellectQueryCtx
from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.facades.intellect_query_facade_task import IntellectQueryFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class IntellectQueryCallServiceTask(IntellectQueryFacadeTask):
    def execute(self, ctx: IntellectQueryFacadeCtx) -> int:
        svc_ctx = IntellectQueryCtx(req=ctx.req, resp=ctx.resp)
        return ServicesObjectsFactory.get_intellect_query_service().query(svc_ctx)
