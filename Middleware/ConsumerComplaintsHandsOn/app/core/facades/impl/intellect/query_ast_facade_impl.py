from app.core.common.dtos.query_ast_facade_dtos import QueryAstFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.intellect.tasks.query_ast_call_service_task import QueryAstCallServiceTask
from app.core.facades.query_ast_facade import QueryAstFacade


class QueryAstFacadeImpl(QueryAstFacade):
    def __init__(self):
        self._tasks = [QueryAstCallServiceTask()]

    def run(self, ctx: QueryAstFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
