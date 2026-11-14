"""MioIngestLogDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioModel to check the MIO on create (no foreign key, D57 and D58)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy import update as sql_update

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogRecord, MioIngestLogReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import MioIngestLogModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao

log = logging.getLogger(__name__)

MARKER_MAX = 255
NOTE_FIELDS = ("message", "rows_loaded", "batch_count", "increment_marker")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(row: MioIngestLogModel) -> MioIngestLogRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    times = {name: getattr(row, name) for name in ("requested_at", "started_at", "finished_at")}
    times = {
        name: value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
        for name, value in times.items()
    }
    return MioIngestLogRecord(
        id=row.id,
        mio_id=row.mio_id,
        status=row.status,
        message=row.message,
        rows_loaded=row.rows_loaded,
        batch_count=row.batch_count,
        increment_marker=row.increment_marker,
        **times,
    )


def _has_invalid_volume(req: MioIngestLogReq) -> bool:
    """True when rows_loaded or batch_count is given but is not a whole number of 0 or more (a bool is not one),
    or increment_marker is given but is not a string of up to MARKER_MAX characters."""
    for count in (req.rows_loaded, req.batch_count):
        if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
            return True
    marker = req.increment_marker
    return marker is not None and (not isinstance(marker, str) or len(marker) > MARKER_MAX)


def _notes_of(req: MioIngestLogReq) -> dict:
    """The given message and volume fields: informational, so they may change on any row."""
    return {name: getattr(req, name) for name in NOTE_FIELDS if getattr(req, name) is not None}


def _new_row(req: MioIngestLogReq) -> MioIngestLogModel:
    """A requested ingest of req.mio_id with the given notes."""
    return MioIngestLogModel(
        id=str(uuid4()),
        mio_id=req.mio_id,
        status=ExecStatus.REQUESTED.value,
        requested_at=_now(),
        **_notes_of(req),
    )


class SqlAlchemyMioIngestLogDao(MioIngestLogDao):
    def create(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.mio_id or _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None:
                    return NOT_FOUND
                row = _new_row(req)
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log create failed")
            return FAILURE

    def get(self, ctx: MioIngestLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioIngestLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log get failed")
            return FAILURE

    def list(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if (req.limit is not None and req.limit < 0) or (req.offset is not None and req.offset < 0):
            return INVALID_INPUT  # SQLite would return every row, Postgres would fail: reject on both
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        try:
            query = select(MioIngestLogModel)
            if req.mio_id:
                query = query.where(MioIngestLogModel.mio_id == req.mio_id)
            if req.status:
                query = query.where(MioIngestLogModel.status == req.status)
            query = query.order_by(MioIngestLogModel.requested_at.desc(), MioIngestLogModel.id)
            if req.limit is not None:
                query = query.limit(req.limit)
            if req.offset:
                query = query.offset(req.offset)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log list failed")
            return FAILURE

    def update(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioIngestLogModel, req.id)
                if row is None:
                    return NOT_FOUND
                current = ExecStatus(row.status)
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT
                notes = _notes_of(req)
                if changes_status:
                    changes = {**notes, "status": target.value}
                    if target == ExecStatus.STARTED:
                        changes["started_at"] = _now()
                    elif target.is_final:
                        changes["finished_at"] = _now()
                    # The write only matches while the row still has the status read above, so when two callbacks
                    # race the second one finds no row to change instead of overwriting the first (D30).
                    moved = session.execute(
                        sql_update(MioIngestLogModel)
                        .where(MioIngestLogModel.id == req.id, MioIngestLogModel.status == current.value)
                        .values(**changes)
                    ).rowcount
                    session.refresh(row)
                    if not moved:
                        if row.status != target.value:
                            return CONFLICT  # a rival moved the row somewhere else first; nothing was changed
                        # A rival made the same move first (a retry): keep its status and times, add only the notes.
                        for name, value in notes.items():
                            setattr(row, name, value)
                else:
                    for name, value in notes.items():
                        setattr(row, name, value)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log update failed")
            return FAILURE
