"""Creates the execution (and optional MIO ingest) before the engine is triggered (D68)."""

from abc import abstractmethod

from app.core.common.dtos.start_wf_dtos import StartWfCtx
from app.core.common.singleton import SingletonMeta


class StartWfService(metaclass=SingletonMeta):
    @abstractmethod
    def start(self, ctx: StartWfCtx) -> int:
        """Prepare ingest + exec log; codes: SUCCESS, INVALID_INPUT, FAILURE."""
