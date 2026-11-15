"""Interface of the service that reads every MIO with its latest ingest status (DESIGN.md D61)."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_dtos import MioStatusCtx
from app.core.common.singleton import SingletonMeta


class MioStatusService(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioStatusCtx and returns an integer code
    (app.core.common.return_codes), also written to ctx.resp.code."""

    @abstractmethod
    def read(self, ctx: MioStatusCtx) -> int:
        """Optional req.mio_id. Returns every MIO (or that one) ordered by name, each with its newest ingest and
        that ingest's executions (newest first). latest_ingest is None when the MIO has never been ingested.
        INVALID_INPUT for a blank mio_id; NOT_FOUND for an unknown mio_id; SUCCESS with entries otherwise."""
