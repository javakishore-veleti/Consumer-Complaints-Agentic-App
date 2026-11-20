"""Thin facade → ZoneIngestLogService."""

from app.core.common.dtos.zone_ingest_log_dtos import ZoneIngestLogCtx
from app.core.facades.zone_ingest_log_facade import ZoneIngestLogFacade
from app.core.services.objects_factory import ServicesObjectsFactory


class ZoneIngestLogFacadeImpl(ZoneIngestLogFacade):
    def create(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().create(ctx)

    def get(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().get(ctx)

    def list(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().list(ctx)

    def update(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().update(ctx)

    def delete(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().delete(ctx)

    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().claim_pending(ctx)

    def complete(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().complete(ctx)

    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int:
        return ServicesObjectsFactory.get_zone_ingest_log_service().reset_failed(ctx)
