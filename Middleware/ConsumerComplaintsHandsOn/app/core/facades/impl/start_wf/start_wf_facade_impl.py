"""The facade only iterates over its tasks. Singleton; task list built once (D64 package)."""

from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.start_wf.tasks.start_wf_call_service_task import StartWfCallServiceTask
from app.core.facades.impl.start_wf.tasks.start_wf_trigger_engine_task import (
    StartWfTriggerEngineTask,
)
from app.core.facades.start_wf_facade import StartWfFacade


class StartWfFacadeImpl(StartWfFacade):
    def __init__(self):
        self._tasks = [StartWfCallServiceTask(), StartWfTriggerEngineTask()]

    def start(self, ctx: StartWfFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
