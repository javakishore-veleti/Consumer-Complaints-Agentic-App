from app.core.common.dtos.risk_radar_dtos import RiskRadarCtx
from app.core.common.dtos.risk_radar_facade_dtos import RiskRadarFacadeCtx
from app.core.facades.risk_radar_facade_task import RiskRadarFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class RiskRadarCallServiceTask(RiskRadarFacadeTask):
    def execute(self, ctx: RiskRadarFacadeCtx) -> int:
        svc_ctx = RiskRadarCtx(req=ctx.req, resp=ctx.resp)
        return ServicesObjectsFactory.get_risk_radar_service().run(svc_ctx)
