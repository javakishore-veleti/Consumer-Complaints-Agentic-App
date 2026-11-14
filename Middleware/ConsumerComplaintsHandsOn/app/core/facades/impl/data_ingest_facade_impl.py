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
        return self._run(OP_CREATE, ctx)

    def get(self, ctx: DataIngestFacadeCtx) -> int:
        return self._run(OP_GET, ctx)

    def list(self, ctx: DataIngestFacadeCtx) -> int:
        return self._run(OP_LIST, ctx)

    def update(self, ctx: DataIngestFacadeCtx) -> int:
        return self._run(OP_UPDATE, ctx)

    def delete(self, ctx: DataIngestFacadeCtx) -> int:
        return self._run(OP_DELETE, ctx)

    def _run(self, operation: str, ctx: DataIngestFacadeCtx) -> int:
        ctx.operation = operation
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                return code
        return SUCCESS
