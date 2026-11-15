"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.tasks.mio_status_call_service_task import MioStatusCallServiceTask
from app.core.facades.mio_status_facade import MioStatusFacade


class MioStatusFacadeImpl(MioStatusFacade):
    def __init__(self):
        self._tasks = [MioStatusCallServiceTask()]

    def read(self, ctx: MioStatusFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
