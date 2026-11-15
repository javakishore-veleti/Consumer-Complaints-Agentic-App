"""The facade only iterates over its tasks. Singleton; task list built once (D64 package)."""

from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.wf_list.tasks.wf_list_call_service_task import WfListCallServiceTask
from app.core.facades.wf_list_facade import WfListFacade


class WfListFacadeImpl(WfListFacade):
    def __init__(self):
        self._tasks = [WfListCallServiceTask()]

    def list(self, ctx: WfListFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
