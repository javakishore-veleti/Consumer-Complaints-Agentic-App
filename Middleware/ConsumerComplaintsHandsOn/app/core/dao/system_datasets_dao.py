"""Interface of the DAO for the system_datasets table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.system_datasets_dtos import SystemDatasetsCtx
from app.core.common.singleton import SingletonMeta


class SystemDatasetsDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one SystemDatasetsCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits."""

    @abstractmethod
    def create(self, ctx: SystemDatasetsCtx) -> int:
        """Needs req.dataset and req.stage. Optional: status (default not_started), last_log_id.
        CONFLICT if the row exists."""

    @abstractmethod
    def get(self, ctx: SystemDatasetsCtx) -> int:
        """Needs req.dataset and req.stage. NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: SystemDatasetsCtx) -> int:
        """Optional filters: req.dataset, req.stage. Ordered by dataset, then stage."""

    @abstractmethod
    def update(self, ctx: SystemDatasetsCtx) -> int:
        """Needs req.dataset and req.stage. Changes the given status and last_log_id and sets updated_at.
        NOT_FOUND if there is no such row, INVALID_INPUT for an unknown status."""

    @abstractmethod
    def delete(self, ctx: SystemDatasetsCtx) -> int:
        """Needs req.dataset and req.stage. The deleted row is returned. NOT_FOUND if there is no such row."""
