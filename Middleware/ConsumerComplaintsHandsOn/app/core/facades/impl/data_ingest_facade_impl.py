"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.data_ingest_constants import OP_CREATE, OP_DELETE, OP_GET, OP_LIST, OP_UPDATE
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.impl.tasks.data_ingest_call_dao_task import DataIngestCallDaoTask
from app.core.facades.impl.tasks.data_ingest_collect_response_task import DataIngestCollectResponseTask
from app.core.facades.impl.tasks.data_ingest_prepare_dao_ctx_task import DataIngestPrepareDaoCtxTask
from app.core.facades.impl.tasks.data_ingest_validate_request_task import DataIngestValidateRequestTask


class DataIngestFacadeImpl(DataIngestFacade):
    def __init__(self):
        # The same ordered tasks for every operation; each task reads ctx.operation.
        self._tasks = [
            DataIngestValidateRequestTask(),
            DataIngestPrepareDaoCtxTask(),
            DataIngestCallDaoTask(),
            DataIngestCollectResponseTask(),
        ]

    def create(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = OP_CREATE
        return self._run(ctx)

    def get(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = OP_GET
        return self._run(ctx)

    def list(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = OP_LIST
        return self._run(ctx)

    def update(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = OP_UPDATE
        return self._run(ctx)

    def delete(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = OP_DELETE
        return self._run(ctx)

    def _run(self, ctx: DataIngestFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
