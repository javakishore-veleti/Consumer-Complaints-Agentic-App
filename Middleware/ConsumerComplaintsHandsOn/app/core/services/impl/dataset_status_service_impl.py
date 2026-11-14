"""DatasetStatusService: each operation is an ordered list of steps run inside one transaction.

A step takes the ctx and returns an integer code. The first step that does not return SUCCESS stops the run and the
transaction is rolled back; otherwise it is committed. The service is a singleton and keeps no per-call state.
"""

import logging

from app.core.common.data_ingest_constants import STATUS_COMPLETED, STATUS_FAILED, STATUS_STARTED
from app.core.common.dataset_constants import (
    DATASET_RUNNING,
    DATASET_STATUS_OF_LOG_STATUS,
    OP_RECORD,
    OP_REQUEST,
    USECASES,
)
from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestReq
from app.core.common.dtos.dataset_status_dtos import DatasetStatusCtx
from app.core.common.dtos.system_datasets_dtos import SystemDatasetsCtx, SystemDatasetsReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.dataset_status_service import DatasetStatusService

log = logging.getLogger(__name__)

REPORTABLE_STATUSES = (STATUS_STARTED, STATUS_COMPLETED, STATUS_FAILED)


class DatasetStatusServiceImpl(DatasetStatusService):
    def __init__(self):
        self._steps = {
            OP_REQUEST: [self._valid_usecase, self._refuse_if_running, self._create_log, self._sync_dataset],
            OP_RECORD: [self._valid_report, self._find_latest_log, self._update_log, self._sync_dataset],
        }

    def request(self, ctx: DatasetStatusCtx) -> int:
        ctx.operation = OP_REQUEST
        return self._run(ctx)

    def record(self, ctx: DatasetStatusCtx) -> int:
        ctx.operation = OP_RECORD
        return self._run(ctx)

    def read(self, ctx: DatasetStatusCtx) -> int:
        dao_ctx = SystemDatasetsCtx()
        code = DaoObjectsFactory.get_system_datasets_dao().list(dao_ctx)
        ctx.resp.records = dao_ctx.resp.records
        ctx.resp.code = code
        return code

    def _run(self, ctx: DatasetStatusCtx) -> int:
        transaction_dao = DaoObjectsFactory.get_transaction_dao()
        ctx.transaction = TransactionCtx()
        code = transaction_dao.begin(ctx.transaction)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        try:
            for step in self._steps[ctx.operation]:
                code = step(ctx)
                if code != SUCCESS:
                    break
        except Exception:
            log.exception("dataset status %s failed", ctx.operation)
            code = FAILURE
        if code == SUCCESS:
            code = transaction_dao.commit(ctx.transaction)
        else:
            transaction_dao.rollback(ctx.transaction)
        ctx.transaction = None
        ctx.resp.code = code
        return code

    # ---- steps (each takes the ctx; the shared transaction is ctx.transaction)

    @staticmethod
    def _valid_usecase(ctx: DatasetStatusCtx) -> int:
        return SUCCESS if ctx.req.usecase in USECASES else INVALID_INPUT

    @staticmethod
    def _valid_report(ctx: DatasetStatusCtx) -> int:
        valid = ctx.req.usecase in USECASES and ctx.req.status in REPORTABLE_STATUSES
        return SUCCESS if valid else INVALID_INPUT

    def _refuse_if_running(self, ctx: DatasetStatusCtx) -> int:
        dataset, stage = USECASES[ctx.req.usecase]
        dao_ctx = SystemDatasetsCtx(req=SystemDatasetsReq(dataset=dataset, stage=stage), transaction=ctx.transaction)
        code = DaoObjectsFactory.get_system_datasets_dao().get(dao_ctx)
        if code == NOT_FOUND:
            return SUCCESS  # no row yet, so nothing is running
        if code != SUCCESS:
            return code
        return CONFLICT if dao_ctx.resp.records[0].status == DATASET_RUNNING else SUCCESS

    @staticmethod
    def _create_log(ctx: DatasetStatusCtx) -> int:
        dao_ctx = DataIngestCtx(req=DataIngestReq(purpose=ctx.req.usecase), transaction=ctx.transaction)
        code = DaoObjectsFactory.get_data_ingest_dao().create(dao_ctx)
        if code == SUCCESS:
            ctx.resp.log = dao_ctx.resp.records[0]
        return code

    @staticmethod
    def _find_latest_log(ctx: DatasetStatusCtx) -> int:
        dao_ctx = DataIngestCtx(req=DataIngestReq(purpose=ctx.req.usecase, limit=1), transaction=ctx.transaction)
        code = DaoObjectsFactory.get_data_ingest_dao().list(dao_ctx)
        if code != SUCCESS:
            return code
        if not dao_ctx.resp.records:
            return NOT_FOUND
        latest = dao_ctx.resp.records[0]
        if ctx.req.run_id and latest.run_id and latest.run_id != ctx.req.run_id:
            return CONFLICT  # a report from an older run must not change the newest one
        ctx.resp.log = latest
        return SUCCESS

    @staticmethod
    def _update_log(ctx: DatasetStatusCtx) -> int:
        req = ctx.req
        dao_ctx = DataIngestCtx(
            req=DataIngestReq(id=ctx.resp.log.id, status=req.status, run_id=req.run_id, message=req.message),
            transaction=ctx.transaction,
        )
        code = DaoObjectsFactory.get_data_ingest_dao().update(dao_ctx)
        if code == SUCCESS:
            ctx.resp.log = dao_ctx.resp.records[0]
        return code

    @staticmethod
    def _sync_dataset(ctx: DatasetStatusCtx) -> int:
        """The dataset row follows the log row (ctx.resp.log), by the map in dataset_constants."""
        dataset, stage = USECASES[ctx.req.usecase]
        req = SystemDatasetsReq(
            dataset=dataset,
            stage=stage,
            status=DATASET_STATUS_OF_LOG_STATUS[ctx.resp.log.status],
            last_log_id=ctx.resp.log.id,
        )
        dao = DaoObjectsFactory.get_system_datasets_dao()
        dao_ctx = SystemDatasetsCtx(req=req, transaction=ctx.transaction)
        code = dao.update(dao_ctx)
        if code == NOT_FOUND:
            code = dao.create(dao_ctx)
        if code == SUCCESS:
            ctx.resp.dataset = dao_ctx.resp.records[0]
        return code
