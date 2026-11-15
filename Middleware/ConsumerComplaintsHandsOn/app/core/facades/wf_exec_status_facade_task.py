"""The task interface dedicated to the workflow execution status facade. Every task of this facade implements it."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusFacadeTask(metaclass=SingletonMeta):
    """A singleton (every task is), so a task keeps no state of its own: what it needs is in the ctx."""

    @abstractmethod
    def execute(self, ctx: WfExecStatusFacadeCtx) -> int:
        """Do one step. Return SUCCESS to let the next task run, any other code to stop the facade."""
