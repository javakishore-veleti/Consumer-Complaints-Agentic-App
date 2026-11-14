"""Tasks of the data ingest facade. Each does one step on the facade ctx.

Tasks are singletons and hold no state: the operation being run is read from ctx.operation.
"""

from app.core.common.data_ingest_constants import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT, VALID_STATUSES
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.data_ingest_facade_task import DataIngestFacadeTask

OP_CREATE = "create"
OP_GET = "get"
OP_LIST = "list"
OP_UPDATE = "update"
OP_DELETE = "delete"


class ValidateRequestTask(DataIngestFacadeTask):
    """Checks the request for the operation, so the DAO only sees valid input."""

    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        req = ctx.req
        operation = ctx.operation
        if req.status is not None and req.status not in VALID_STATUSES:
            return INVALID_INPUT
        if operation == OP_CREATE and not (req.purpose and req.purpose.strip()):
            return INVALID_INPUT
        if operation in (OP_GET, OP_UPDATE, OP_DELETE) and not req.id:
            return INVALID_INPUT
        if operation == OP_UPDATE and req.status is None and req.run_id is None and req.message is None:
            return INVALID_INPUT
        if operation == OP_LIST:
            if req.limit is not None and not 1 <= req.limit <= MAX_LIST_LIMIT:
                return INVALID_INPUT
            if req.offset is not None and req.offset < 0:
                return INVALID_INPUT
        return SUCCESS


class PrepareDaoCtxTask(DataIngestFacadeTask):
    """Fills the DAO's own ctx (ctx.data_ingest_ctx) from the facade request."""

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


class CallDaoTask(DataIngestFacadeTask):
    """Gets the DAO singleton from the DAO package's factory and calls it with the DAO ctx."""

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


class CollectResponseTask(DataIngestFacadeTask):
    """Copies the DAO's result into the facade response."""

    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.resp.records = ctx.data_ingest_ctx.resp.records
        return SUCCESS
