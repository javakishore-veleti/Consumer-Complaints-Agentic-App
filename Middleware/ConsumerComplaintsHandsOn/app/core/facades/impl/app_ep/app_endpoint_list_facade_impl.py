from app.core.common.dtos.app_endpoint_list_facade_dtos import AppEndpointListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.app_endpoint_list_facade import AppEndpointListFacade
from app.core.facades.impl.app_ep.tasks.app_endpoint_list_call_service_task import (
    AppEndpointListCallServiceTask,
)


class AppEndpointListFacadeImpl(AppEndpointListFacade):
    def __init__(self):
        self._tasks = [AppEndpointListCallServiceTask()]

    def list(self, ctx: AppEndpointListFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code

    def get(self, ctx: AppEndpointListFacadeCtx) -> int:
        return self.list(ctx)
