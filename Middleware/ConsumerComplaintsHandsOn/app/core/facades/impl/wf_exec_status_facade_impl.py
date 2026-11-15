"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.tasks.wf_exec_status_call_service_task import WfExecStatusCallServiceTask
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade


class WfExecStatusFacadeImpl(WfExecStatusFacade):
    def __init__(self):
        self._tasks = [WfExecStatusCallServiceTask()]

    def report(self, ctx: WfExecStatusFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
