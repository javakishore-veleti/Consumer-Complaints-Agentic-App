"""Interface: list every registered workflow without config (D66)."""

from abc import abstractmethod

from app.core.common.dtos.wf_list_dtos import WfListCtx
from app.core.common.singleton import SingletonMeta


class WfListService(metaclass=SingletonMeta):
    @abstractmethod
    def list(self, ctx: WfListCtx) -> int:
        """Return SUCCESS with resp.entries, or a DAO failure code."""
