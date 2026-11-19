from dataclasses import dataclass, field

from app.core.common.dtos.risk_radar_dtos import RiskRadarReq, RiskRadarResp


@dataclass
class RiskRadarFacadeCtx:
    req: RiskRadarReq = field(default_factory=RiskRadarReq)
    resp: RiskRadarResp = field(default_factory=RiskRadarResp)
