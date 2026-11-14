"""DataIngestDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common.data_ingest_constants import (
    ALLOWED_TRANSITIONS,
    FINISHED_STATUSES,
    STATUS_REQUESTED,
    STATUS_STARTED,
)
from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestRecord
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.impl.database import get_engine
from app.core.dao.impl.models import DataIngestLogModel

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(row: DataIngestLogModel) -> DataIngestRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    times = {name: getattr(row, name) for name in ("requested_at", "started_at", "finished_at")}
    times = {
        name: value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
        for name, value in times.items()
    }
    return DataIngestRecord(
        id=row.id, purpose=row.purpose, status=row.status, run_id=row.run_id, message=row.message, **times
    )


class SqlAlchemyDataIngestDao(DataIngestDao):
    def create(self, ctx: DataIngestCtx) -> int:
        req = ctx.req
        if not req.purpose:
            return INVALID_INPUT
        try:
            with Session(get_engine()) as session:
                row = DataIngestLogModel(
                    id=str(uuid4()),
                    purpose=req.purpose,
                    status=req.status or STATUS_REQUESTED,
                    run_id=req.run_id,
                    message=req.message,
                    requested_at=_now(),
                )
                session.add(row)
                session.commit()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("data_ingest_log create failed")
            return FAILURE

    def get(self, ctx: DataIngestCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with Session(get_engine()) as session:
                row = session.get(DataIngestLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("data_ingest_log get failed")
            return FAILURE

    def list(self, ctx: DataIngestCtx) -> int:
        req = ctx.req
        try:
            query = select(DataIngestLogModel)
            if req.purpose:
                query = query.where(DataIngestLogModel.purpose == req.purpose)
            if req.status:
                query = query.where(DataIngestLogModel.status == req.status)
            query = query.order_by(DataIngestLogModel.requested_at.desc(), DataIngestLogModel.id)
            if req.limit is not None:
                query = query.limit(req.limit)
            if req.offset:
                query = query.offset(req.offset)
            with Session(get_engine()) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("data_ingest_log list failed")
            return FAILURE

    def update(self, ctx: DataIngestCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with Session(get_engine()) as session:
                row = session.get(DataIngestLogModel, req.id)
                if row is None:
                    return NOT_FOUND
                changes_status = req.status is not None and req.status != row.status
                if changes_status and req.status not in ALLOWED_TRANSITIONS.get(row.status, ()):
                    return CONFLICT  # checked and written in this one transaction, so retries cannot race
                if req.run_id is not None:
                    row.run_id = req.run_id
                if req.message is not None:
                    row.message = req.message
                if changes_status:
                    row.status = req.status
                    if req.status == STATUS_STARTED:
                        row.started_at = _now()
                    elif req.status in FINISHED_STATUSES:
                        row.finished_at = _now()
                session.commit()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("data_ingest_log update failed")
            return FAILURE

    def delete(self, ctx: DataIngestCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with Session(get_engine()) as session:
                row = session.get(DataIngestLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.commit()
            return SUCCESS
        except Exception:
            log.exception("data_ingest_log delete failed")
            return FAILURE
