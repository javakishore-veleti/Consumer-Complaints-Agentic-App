from abc import abstractmethod

from app.core.common.dtos.risk_radar_facade_dtos import RiskRadarFacadeCtx
from app.core.common.singleton import SingletonMeta


class RiskRadarFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: RiskRadarFacadeCtx) -> int: ...
