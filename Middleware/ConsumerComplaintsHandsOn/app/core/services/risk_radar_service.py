from abc import abstractmethod

from app.core.common.dtos.risk_radar_dtos import RiskRadarCtx
from app.core.common.singleton import SingletonMeta


class RiskRadarService(metaclass=SingletonMeta):
    @abstractmethod
    def run(self, ctx: RiskRadarCtx) -> int: ...
