"""Checks the request for the operation, so the DAO only sees valid input."""

from app.core.common.data_ingest_constants import (
    MAX_LIST_LIMIT,
    OP_CREATE,
    OP_DELETE,
    OP_GET,
    OP_LIST,
    OP_UPDATE,
    STATUS_REQUESTED,
    VALID_STATUSES,
)
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx, DataIngestFacadeReq
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.facades.data_ingest_facade_task import DataIngestFacadeTask


class DataIngestValidateRequestTask(DataIngestFacadeTask):
    def execute(self, ctx: DataIngestFacadeCtx) -> int:
        req = ctx.req
        if req.status is not None and req.status not in VALID_STATUSES:
            return INVALID_INPUT
        valid = {
            OP_CREATE: self._valid_create,
            OP_GET: self._has_id,
            OP_DELETE: self._has_id,
            OP_UPDATE: self._valid_update,
            OP_LIST: self._valid_list,
        }[ctx.operation](req)
        return SUCCESS if valid else INVALID_INPUT

    @staticmethod
    def _has_id(req: DataIngestFacadeReq) -> bool:
        return bool(req.id)

    @staticmethod
    def _valid_create(req: DataIngestFacadeReq) -> bool:
        has_purpose = bool(req.purpose and req.purpose.strip())
        # a row always starts as "requested"; it moves on through update
        return has_purpose and req.status in (None, STATUS_REQUESTED)

    @staticmethod
    def _valid_update(req: DataIngestFacadeReq) -> bool:
        changes_something = any(value is not None for value in (req.status, req.run_id, req.message))
        return bool(req.id) and changes_something

    @staticmethod
    def _valid_list(req: DataIngestFacadeReq) -> bool:
        limit_ok = req.limit is None or 1 <= req.limit <= MAX_LIST_LIMIT
        offset_ok = req.offset is None or req.offset >= 0
        return limit_ok and offset_ok
