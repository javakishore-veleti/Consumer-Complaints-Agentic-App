"""MioDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioDatasetModel to keep the in-use rule (no foreign keys, D57)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.mio_dtos import MioCtx, MioRecord, MioReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import MioDatasetModel, MioModel, MioWorkflowModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_dao import MioDao

log = logging.getLogger(__name__)

NAME_MAX = 100


def _to_record(row: MioModel) -> MioRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return MioRecord(id=row.id, name=row.name, description=row.description, created_at=created, updated_at=updated)


def _name_of(req: MioReq) -> str | None:
    """The name without leading or trailing spaces. Names are case sensitive."""
    return None if req.name is None else req.name.strip()


def _name_is_not_text(req: MioReq) -> bool:
    """True when a name was given but is not a string. Checked before the name is trimmed."""
    return req.name is not None and not isinstance(req.name, str)


def _has_invalid_field(req: MioReq) -> bool:
    if _name_is_not_text(req):
        return True
    name = _name_of(req)
    return name is not None and (not name or len(name) > NAME_MAX)


def _taken_query(req: MioReq) -> Select:
    """Ids of rows that already use the given name."""
    return select(MioModel.id).where(MioModel.name == _name_of(req))


class SqlAlchemyMioDao(MioDao):
    def create(self, ctx: MioCtx) -> int:
        req = ctx.req
        if _has_invalid_field(req) or not _name_of(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.scalars(_taken_query(req)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = MioModel(
                    id=str(uuid4()),
                    name=_name_of(req),
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios create failed")
            return FAILURE

    def get(self, ctx: MioCtx) -> int:
        req = ctx.req
        if _name_is_not_text(req) or not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if req.id:
                    row = session.get(MioModel, req.id)
                else:
                    row = session.scalars(select(MioModel).where(MioModel.name == _name_of(req))).first()
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios get failed")
            return FAILURE

    def list(self, ctx: MioCtx) -> int:
        try:
            with unit_of_work(ctx) as session:
                query = select(MioModel).order_by(MioModel.name)
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios list failed")
            return FAILURE

    def update(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioModel, req.id)
                if row is None:
                    return NOT_FOUND
                new_name = _name_of(req) if _name_of(req) != row.name else None
                if new_name is not None:
                    if session.scalars(_taken_query(req).where(MioModel.id != row.id)).first() is not None:
                        return CONFLICT
                    row.name = new_name
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios update failed")
            return FAILURE

    def delete(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioModel, req.id)
                if row is None:
                    return NOT_FOUND
                has_link = select(MioDatasetModel.id).where(MioDatasetModel.mio_id == row.id)
                if session.scalars(has_link).first() is not None:
                    return CONFLICT
                has_wf = select(MioWorkflowModel.id).where(MioWorkflowModel.mio_id == row.id)
                if session.scalars(has_wf).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios delete failed")
            return FAILURE
