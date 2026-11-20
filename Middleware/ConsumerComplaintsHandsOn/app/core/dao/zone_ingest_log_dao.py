"""Interface for zone ingest_log_* tables (one DAO covering all five zones)."""

from abc import abstractmethod

from app.core.common.dtos.zone_ingest_log_dtos import ZoneIngestLogCtx
from app.core.common.singleton import SingletonMeta


class ZoneIngestLogDao(metaclass=SingletonMeta):
    """Singleton. Methods take ZoneIngestLogCtx and return an int return_code; results in ctx.resp."""

    @abstractmethod
    def create(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone, partition_key, data_tech, source_end_point_id, dest_end_point_id.
        Creates status=pending. CONFLICT on unique key clash."""

    @abstractmethod
    def get(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone + id."""

    @abstractmethod
    def list(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone. Newest status_updated_on first. limit default/max 30.
        Optional filters: status, partition_key, workflow_execution_id, status_updated_from/to."""

    @abstractmethod
    def update(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone + id. Updates given fields; bumps status_updated_on; status_on when status changes."""

    @abstractmethod
    def delete(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone + id."""

    @abstractmethod
    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone. Claims up to min(claim_limit or 5, 5) pending rows → in_progress (oldest first)."""

    @abstractmethod
    def complete(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone + id + status in {done, failed}. Sets status and timestamps."""

    @abstractmethod
    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int:
        """Requires zone + id. failed → pending only; else CONFLICT."""
