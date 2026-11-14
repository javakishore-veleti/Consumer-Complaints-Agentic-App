"""Gets the DAO singleton from the DAO package's factory and calls it with the DAO ctx."""

from app.core.common.data_ingest_constants import OP_CREATE, OP_DELETE, OP_GET, OP_LIST, OP_UPDATE
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.data_ingest_facade_task import DataIngestFacadeTask


class DataIngestCallDaoTask(DataIngestFacadeTask):
    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        dao = DaoObjectsFactory.get_data_ingest_dao()
        methods = {
            OP_CREATE: dao.create,
            OP_GET: dao.get,
            OP_LIST: dao.list,
            OP_UPDATE: dao.update,
            OP_DELETE: dao.delete,
        }
        return methods[ctx.operation](ctx.data_ingest_ctx)
