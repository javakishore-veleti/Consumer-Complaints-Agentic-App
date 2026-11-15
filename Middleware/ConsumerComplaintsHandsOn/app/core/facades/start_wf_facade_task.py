from abc import abstractmethod

from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.singleton import SingletonMeta


class StartWfFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: StartWfFacadeCtx) -> int:
        """One step of the start-workflow facade."""
