"""Interface of the DAO for the data_ingest_log table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.data_ingest_dtos import DataIngestCtx
from app.core.common.singleton import SingletonMeta


class DataIngestDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DataIngestCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records."""

    @abstractmethod
    def create(self, ctx: DataIngestCtx) -> int:
        """Needs req.purpose. Optional: status (default "requested"), run_id, message."""

    @abstractmethod
    def get(self, ctx: DataIngestCtx) -> int:
        """Needs req.id. NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: DataIngestCtx) -> int:
        """Optional filters: req.purpose, req.status. Optional paging: req.limit, req.offset. Newest first."""

    @abstractmethod
    def update(self, ctx: DataIngestCtx) -> int:
        """Needs req.id. Changes the given status, run_id and message. Sets started_at / finished_at
        when the status becomes started / completed or failed. NOT_FOUND if there is no such row."""

    @abstractmethod
    def delete(self, ctx: DataIngestCtx) -> int:
        """Needs req.id. The deleted row is returned in resp.records. NOT_FOUND if there is no such row."""
