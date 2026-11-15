"""Interface of the workflow list facade (the portal's list-workflows call, D66). The API depends on this, never on
facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfListFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one WfListFacadeCtx and returns an integer
    code (app.core.common.return_codes), also written to ctx.resp.code. The facade only runs its tasks in order and
    stops at the first task that does not return SUCCESS."""

    @abstractmethod
    def list(self, ctx: WfListFacadeCtx) -> int:
        """List every registered workflow without config (ctx.req). Codes and entries are those of
        WfListService.list."""
