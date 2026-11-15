"""Interface of the workflow execution status facade (the engine's status callback, D60). The API depends on this,
never on facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one WfExecStatusFacadeCtx and returns an integer
    code (app.core.common.return_codes), also written to ctx.resp.code. The facade only runs its tasks in order and
    stops at the first task that does not return SUCCESS."""

    @abstractmethod
    def report(self, ctx: WfExecStatusFacadeCtx) -> int:
        """An engine reports a status of one execution (ctx.req). The codes and the ingest rule are those of
        WfExecStatusService.record; the execution and its ingest row after the call are in ctx.resp."""
