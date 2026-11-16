from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.intellect.tasks.intellect_query_call_service_task import (
    IntellectQueryCallServiceTask,
)
from app.core.facades.intellect_query_facade import IntellectQueryFacade


class IntellectQueryFacadeImpl(IntellectQueryFacade):
    def __init__(self):
        self._tasks = [IntellectQueryCallServiceTask()]

    def query(self, ctx: IntellectQueryFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
