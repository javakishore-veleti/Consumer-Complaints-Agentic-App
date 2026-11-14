"""DatasetDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads DatasetLocationModel and MioDatasetModel to keep the in-use rules (no foreign keys, D57)."""

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetRecord, DatasetReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

NAME_MAX = 100
CODE_PATTERN = re.compile(r"[A-Z0-9]{1,15}")


def _to_record(row: DatasetModel) -> DatasetRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return DatasetRecord(
        id=row.id,
        name=row.name,
        code=row.code,
        description=row.description,
        created_at=created,
        updated_at=updated,
    )


def _name_of(req: DatasetReq) -> str | None:
    """The name without leading or trailing spaces. Names are case sensitive."""
    return None if req.name is None else req.name.strip()


def _has_invalid_field(req: DatasetReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    name = _name_of(req)
    if name is not None and (not name or len(name) > NAME_MAX):
        return True
    if req.code is not None and (not isinstance(req.code, str) or CODE_PATTERN.fullmatch(req.code) is None):
        return True
    return False


def _taken_query(req: DatasetReq) -> Select:
    """Ids of rows that already use the given name or the given code."""
    taken = []
    if _name_of(req) is not None:
        taken.append(DatasetModel.name == _name_of(req))
    if req.code is not None:
        taken.append(DatasetModel.code == req.code)
    return select(DatasetModel.id).where(or_(*taken))


class SqlAlchemyDatasetDao(DatasetDao):
    def create(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not (_name_of(req) and req.code) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.scalars(_taken_query(req)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = DatasetModel(
                    id=str(uuid4()),
                    name=_name_of(req),
                    code=req.code,
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name or code at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets create failed")
            return FAILURE

    def get(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if req.id:
                    row = session.get(DatasetModel, req.id)
                else:
                    row = session.scalars(select(DatasetModel).where(DatasetModel.name == _name_of(req))).first()
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("datasets get failed")
            return FAILURE

    def list(self, ctx: DatasetCtx) -> int:
        try:
            with unit_of_work(ctx) as session:
                query = select(DatasetModel).order_by(DatasetModel.name)
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("datasets list failed")
            return FAILURE

    def update(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                changed = DatasetReq(
                    name=_name_of(req) if _name_of(req) != row.name else None,
                    code=req.code if req.code != row.code else None,
                )
                if changed.name is not None or changed.code is not None:
                    if session.scalars(_taken_query(changed).where(DatasetModel.id != row.id)).first() is not None:
                        return CONFLICT
                if changed.code is not None:
                    holds_env_var = select(DatasetLocationModel.id).where(
                        DatasetLocationModel.dataset_id == row.id,
                        DatasetLocationModel.local_env_var_name.is_not(None),
                    )
                    if session.scalars(holds_env_var).first() is not None:
                        return CONFLICT
                if changed.name is not None:
                    row.name = changed.name
                if changed.code is not None:
                    row.code = changed.code
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name or code at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets update failed")
            return FAILURE

    def delete(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                has_location = select(DatasetLocationModel.id).where(DatasetLocationModel.dataset_id == row.id)
                has_link = select(MioDatasetModel.id).where(MioDatasetModel.dataset_id == row.id)
                if session.scalars(has_location).first() is not None or session.scalars(has_link).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("datasets delete failed")
            return FAILURE
