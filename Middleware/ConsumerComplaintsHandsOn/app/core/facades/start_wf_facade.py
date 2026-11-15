from abc import abstractmethod

from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.singleton import SingletonMeta


class StartWfFacade(metaclass=SingletonMeta):
    @abstractmethod
    def start(self, ctx: StartWfFacadeCtx) -> int:
        """Prepare the execution and trigger the engine; codes match StartWfService / Airflow start."""
