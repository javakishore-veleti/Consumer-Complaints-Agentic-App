"""Copies the DAO's result into the facade response."""

from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.data_ingest_facade_task import DataIngestFacadeTask


class DataIngestCollectResponseTask(DataIngestFacadeTask):
    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.resp.records = ctx.data_ingest_ctx.resp.records
        return SUCCESS
