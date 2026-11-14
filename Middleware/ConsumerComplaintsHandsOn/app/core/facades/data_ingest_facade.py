"""Interface of the data ingest facade. The API depends on this, never on facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.singleton import SingletonMeta


class DataIngestFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DataIngestFacadeCtx and returns an integer
    code (app.core.common.return_codes).

    The facade only runs its tasks in order and stops at the first task that does not return SUCCESS.
    Results are written to ctx.resp.records."""

    @abstractmethod
    def create(self, ctx: DataIngestFacadeCtx) -> int: ...

    @abstractmethod
    def get(self, ctx: DataIngestFacadeCtx) -> int: ...

    @abstractmethod
    def list(self, ctx: DataIngestFacadeCtx) -> int: ...

    @abstractmethod
    def update(self, ctx: DataIngestFacadeCtx) -> int: ...

    @abstractmethod
    def delete(self, ctx: DataIngestFacadeCtx) -> int: ...
