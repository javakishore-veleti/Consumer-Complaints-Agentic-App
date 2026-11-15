"""The task interface dedicated to the workflow list facade. Every task of this facade implements it."""

from abc import abstractmethod

from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfListFacadeTask(metaclass=SingletonMeta):
    """A singleton (every task is), so a task keeps no state of its own: what it needs is in the ctx."""

    @abstractmethod
    def execute(self, ctx: WfListFacadeCtx) -> int:
        """Do one step. Return SUCCESS to let the next task run, any other code to stop the facade."""
