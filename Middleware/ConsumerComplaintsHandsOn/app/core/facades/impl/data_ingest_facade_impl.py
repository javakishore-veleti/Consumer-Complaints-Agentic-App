"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.impl.data_ingest_tasks import (
    OP_CREATE,
    OP_DELETE,
    OP_GET,
    OP_LIST,
    OP_UPDATE,
    CallDaoTask,
    CollectResponseTask,
    PrepareDaoCtxTask,
    ValidateRequestTask,
)


class DataIngestFacadeImpl(DataIngestFacade):
    def __init__(self):
        # The same ordered tasks for every operation; each task reads ctx.operation.
        self._tasks = [ValidateRequestTask(), PrepareDaoCtxTask(), CallDaoTask(), CollectResponseTask()]

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
