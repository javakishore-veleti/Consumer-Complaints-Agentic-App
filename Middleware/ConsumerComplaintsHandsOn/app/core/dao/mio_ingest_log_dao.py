"""Interface of the DAO for the mios_ingest_log table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx
from app.core.common.singleton import SingletonMeta


class MioIngestLogDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioIngestLogCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    One row per ingest of a MIO (D50, D58). The log is append-only: there is no delete. mio_id is a plain column
    with no foreign key; create checks that the MIO exists. The volume fields are rows_loaded and batch_count
    (whole numbers, 0 or more) and increment_marker (an opaque string of up to 255 characters that no code reads
    inside); a bool is not a whole number here."""

    @abstractmethod
    def create(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.mio_id. Optional: message, rows_loaded, batch_count, increment_marker. The new row is always
        "requested", whatever req.status says, and is returned. INVALID_INPUT without a mio_id or for an invalid
        volume field, NOT_FOUND if there is no such MIO (read in the same transaction)."""

    @abstractmethod
    def get(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: MioIngestLogCtx) -> int:
        """Optional filters: req.mio_id, req.status; optional req.limit and req.offset. Newest first (requested_at
        descending, then id). An empty result is SUCCESS with no records. INVALID_INPUT for a negative limit or
        offset or an unknown status."""

    @abstractmethod
    def update(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.id. Changes the given status, message, rows_loaded, batch_count and increment_marker; mio_id
        never changes. Status moves follow D30: requested to started or failed, started to completed or failed,
        completed and failed are final, the same status again is accepted and keeps its times. started_at is set on
        the move to started, finished_at on the move to completed or failed. NOT_FOUND if there is no such row,
        INVALID_INPUT for an unknown status or an invalid volume field, CONFLICT for any other move; a CONFLICT
        changes nothing.

        Two callbacks at once: the status write only matches a row that still has the status that was read, so the
        first to commit wins. The second gets CONFLICT, or SUCCESS if the first made the very same move (a retry).

        message and the volume fields are notes, not part of the D30 rules: they may be set on any row, also a
        final one, so a late callback can still fill in the final volume."""
