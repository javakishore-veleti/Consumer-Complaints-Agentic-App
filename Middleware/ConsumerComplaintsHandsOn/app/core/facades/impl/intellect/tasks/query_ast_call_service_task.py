from app.core.common.dtos.query_ast_dtos import QueryAstCtx
from app.core.common.dtos.query_ast_facade_dtos import QueryAstFacadeCtx
from app.core.facades.query_ast_facade_task import QueryAstFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class QueryAstCallServiceTask(QueryAstFacadeTask):
    def execute(self, ctx: QueryAstFacadeCtx) -> int:
        svc_ctx = QueryAstCtx(req=ctx.req, resp=ctx.resp)
        return ServicesObjectsFactory.get_query_ast_service().run(svc_ctx)
