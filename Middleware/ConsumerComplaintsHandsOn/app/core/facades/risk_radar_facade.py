from abc import abstractmethod

from app.core.common.dtos.risk_radar_facade_dtos import RiskRadarFacadeCtx
from app.core.common.singleton import SingletonMeta


class RiskRadarFacade(metaclass=SingletonMeta):
    @abstractmethod
    def run(self, ctx: RiskRadarFacadeCtx) -> int: ...
