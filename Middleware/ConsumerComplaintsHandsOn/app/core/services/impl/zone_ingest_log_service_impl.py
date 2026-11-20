"""Pass-through ZoneIngestLogService → DAO."""

from app.core.common.dtos.zone_ingest_log_dtos import ZoneIngestLogCtx
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.zone_ingest_log_service import ZoneIngestLogService


class ZoneIngestLogServiceImpl(ZoneIngestLogService):
    def create(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().create(ctx)

    def get(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().get(ctx)

    def list(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().list(ctx)

    def update(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().update(ctx)

    def delete(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().delete(ctx)

    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().claim_pending(ctx)

    def complete(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().complete(ctx)

    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int:
        return DaoObjectsFactory.get_zone_ingest_log_dao().reset_failed(ctx)
