from abc import abstractmethod

from app.core.common.dtos.dag_context_dtos import DagContextCtx
from app.core.common.singleton import SingletonMeta


class DagContextService(metaclass=SingletonMeta):
    @abstractmethod
    def get(self, ctx: DagContextCtx) -> int:
        """Load config_used (+ optional dataset locations / app endpoint) for an execution."""
