"""SystemDatasetsDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.common.dataset_constants import DATASET_NOT_STARTED, VALID_DATASET_STATUSES
from app.core.common.dtos.system_datasets_dtos import SystemDatasetRecord, SystemDatasetsCtx
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import SystemDatasetModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.system_datasets_dao import SystemDatasetsDao

log = logging.getLogger(__name__)


def _to_record(row: SystemDatasetModel) -> SystemDatasetRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    stamp = row.updated_at
    if stamp is not None and stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return SystemDatasetRecord(
        dataset=row.dataset, stage=row.stage, status=row.status, last_log_id=row.last_log_id, updated_at=stamp
    )


class SqlAlchemySystemDatasetsDao(SystemDatasetsDao):
    def create(self, ctx: SystemDatasetsCtx) -> int:
        req = ctx.req
        if not (req.dataset and req.stage):
            return INVALID_INPUT
        status = req.status or DATASET_NOT_STARTED
        if status not in VALID_DATASET_STATUSES:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(SystemDatasetModel, (req.dataset, req.stage)) is not None:
                    return CONFLICT
                row = SystemDatasetModel(
                    dataset=req.dataset,
                    stage=req.stage,
                    status=status,
                    last_log_id=req.last_log_id,
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("system_datasets create failed")
            return FAILURE

    def get(self, ctx: SystemDatasetsCtx) -> int:
        req = ctx.req
        if not (req.dataset and req.stage):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(SystemDatasetModel, (req.dataset, req.stage))
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("system_datasets get failed")
            return FAILURE

    def list(self, ctx: SystemDatasetsCtx) -> int:
        req = ctx.req
        try:
            query = select(SystemDatasetModel)
            if req.dataset:
                query = query.where(SystemDatasetModel.dataset == req.dataset)
            if req.stage:
                query = query.where(SystemDatasetModel.stage == req.stage)
            query = query.order_by(SystemDatasetModel.dataset, SystemDatasetModel.stage)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("system_datasets list failed")
            return FAILURE

    def update(self, ctx: SystemDatasetsCtx) -> int:
        req = ctx.req
        if not (req.dataset and req.stage):
            return INVALID_INPUT
        if req.status is not None and req.status not in VALID_DATASET_STATUSES:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(SystemDatasetModel, (req.dataset, req.stage))
                if row is None:
                    return NOT_FOUND
                if req.status is not None:
                    row.status = req.status
                if req.last_log_id is not None:
                    row.last_log_id = req.last_log_id
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("system_datasets update failed")
            return FAILURE

    def delete(self, ctx: SystemDatasetsCtx) -> int:
        req = ctx.req
        if not (req.dataset and req.stage):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(SystemDatasetModel, (req.dataset, req.stage))
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("system_datasets delete failed")
            return FAILURE
