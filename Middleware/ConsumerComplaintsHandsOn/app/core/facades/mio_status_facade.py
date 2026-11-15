"""Interface of the MIO status facade (the portal's read-status call, D61). The API depends on this, never on
facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class MioStatusFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioStatusFacadeCtx and returns an integer
    code (app.core.common.return_codes), also written to ctx.resp.code. The facade only runs its tasks in order and
    stops at the first task that does not return SUCCESS."""

    @abstractmethod
    def read(self, ctx: MioStatusFacadeCtx) -> int:
        """Read every MIO (or one) with its latest ingest and executions (ctx.req). Codes and entries are those of
        MioStatusService.read."""
