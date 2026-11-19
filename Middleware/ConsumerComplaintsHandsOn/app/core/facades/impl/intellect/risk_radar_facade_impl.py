from app.core.common.dtos.risk_radar_facade_dtos import RiskRadarFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.intellect.tasks.risk_radar_call_service_task import (
    RiskRadarCallServiceTask,
)
from app.core.facades.risk_radar_facade import RiskRadarFacade


class RiskRadarFacadeImpl(RiskRadarFacade):
    def __init__(self):
        self._tasks = [RiskRadarCallServiceTask()]

    def run(self, ctx: RiskRadarFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
