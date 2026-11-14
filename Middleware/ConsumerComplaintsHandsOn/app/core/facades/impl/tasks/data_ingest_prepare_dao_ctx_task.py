"""Fills the DAO's own ctx (ctx.data_ingest_ctx) from the facade request."""

from app.core.common.data_ingest_constants import DEFAULT_LIST_LIMIT
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.data_ingest_facade_task import DataIngestFacadeTask


class DataIngestPrepareDaoCtxTask(DataIngestFacadeTask):
    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        req = ctx.req
        dao_req = ctx.data_ingest_ctx.req
        dao_req.id = req.id
        dao_req.purpose = req.purpose.strip() if req.purpose else req.purpose
        dao_req.status = req.status
        dao_req.run_id = req.run_id
        dao_req.message = req.message
        dao_req.limit = req.limit if req.limit is not None else DEFAULT_LIST_LIMIT
        dao_req.offset = req.offset
        return SUCCESS
