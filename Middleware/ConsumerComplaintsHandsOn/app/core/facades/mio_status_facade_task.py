"""The task interface dedicated to the MIO status facade. Every task of this facade implements it."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class MioStatusFacadeTask(metaclass=SingletonMeta):
    """A singleton (every task is), so a task keeps no state of its own: what it needs is in the ctx."""

    @abstractmethod
    def execute(self, ctx: MioStatusFacadeCtx) -> int:
        """Do one step. Return SUCCESS to let the next task run, any other code to stop the facade."""
