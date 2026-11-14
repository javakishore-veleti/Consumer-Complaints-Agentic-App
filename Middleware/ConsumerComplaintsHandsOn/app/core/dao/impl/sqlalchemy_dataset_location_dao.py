"""DatasetLocationDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads DatasetModel and MioDatasetModel to keep the parent and in-use rules (no foreign keys, D57)."""

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.app_types_constants import DatasetLocationType
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationRecord, DatasetLocationReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

PATH_MAX = 1000
ENV_VAR_PREFIX = "LOCAL_DATA_PATH_"
CREDENTIALS_PATTERN = re.compile(r"[A-Za-z0-9_.\-]{1,100}")


def _to_record(row: DatasetLocationModel) -> DatasetLocationRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return DatasetLocationRecord(
        id=row.id,
        dataset_id=row.dataset_id,
        location_type=row.location_type,
        path=row.path,
        local_env_var_name=row.local_env_var_name,
        credentials_ref=row.credentials_ref,
        description=row.description,
        created_at=created,
        updated_at=updated,
    )


def _has_invalid_field(req: DatasetLocationReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    if req.location_type is not None and req.location_type not in DatasetLocationType.values():
        return True
    if req.path is not None and (
        not isinstance(req.path, str) or not req.path.strip() or len(req.path.strip()) > PATH_MAX
    ):
        return True
    if req.local_env_var_name is not None and (
        not isinstance(req.local_env_var_name, str) or not req.local_env_var_name
    ):
        return True
    if req.path is not None and req.local_env_var_name is not None:
        return True
    if req.credentials_ref is not None and (
        not isinstance(req.credentials_ref, str) or CREDENTIALS_PATTERN.fullmatch(req.credentials_ref) is None
    ):
        return True
    return False


def _result_is_invalid(merged: DatasetLocationReq) -> bool:
    """The rules for the whole row: exactly one of path and env var name, and an env var name only for "local"."""
    if (merged.path is None) == (merged.local_env_var_name is None):
        return True
    return merged.local_env_var_name is not None and merged.location_type != DatasetLocationType.LOCAL


def _same_place_query(merged: DatasetLocationReq) -> Select:
    """Ids of rows of the same dataset that have the same type and path, or the same env var name."""
    query = select(DatasetLocationModel.id).where(DatasetLocationModel.dataset_id == merged.dataset_id)
    if merged.path is not None:
        return query.where(
            DatasetLocationModel.location_type == merged.location_type, DatasetLocationModel.path == merged.path
        )
    return query.where(DatasetLocationModel.local_env_var_name == merged.local_env_var_name)


class SqlAlchemyDatasetLocationDao(DatasetLocationDao):
    def create(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not (req.dataset_id and req.location_type) or _has_invalid_field(req):
            return INVALID_INPUT
        merged = DatasetLocationReq(
            dataset_id=req.dataset_id,
            location_type=req.location_type,
            path=None if req.path is None else req.path.strip(),
            local_env_var_name=req.local_env_var_name,
            credentials_ref=req.credentials_ref,
        )
        if _result_is_invalid(merged):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                dataset = session.get(DatasetModel, req.dataset_id)
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset.code:
                    return INVALID_INPUT
                if session.scalars(_same_place_query(merged)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = DatasetLocationModel(
                    id=str(uuid4()),
                    dataset_id=merged.dataset_id,
                    location_type=merged.location_type,
                    path=merged.path,
                    local_env_var_name=merged.local_env_var_name,
                    credentials_ref=merged.credentials_ref,
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same place at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets_location create failed")
            return FAILURE

    def get(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("datasets_location get failed")
            return FAILURE

    def list(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        try:
            query = select(DatasetLocationModel)
            if req.dataset_id is not None:
                query = query.where(DatasetLocationModel.dataset_id == req.dataset_id)
            if req.location_type is not None:
                query = query.where(DatasetLocationModel.location_type == req.location_type)
            # SQLite and Postgres sort NULLs differently, so "rows with a path first" is spelled out.
            query = query.order_by(
                DatasetLocationModel.location_type,
                DatasetLocationModel.path.is_(None),
                DatasetLocationModel.path,
                DatasetLocationModel.id,
            )
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("datasets_location list failed")
            return FAILURE

    def update(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                if req.dataset_id is not None and req.dataset_id != row.dataset_id:
                    return INVALID_INPUT
                # The row as it would be after the update. Giving a path clears the env var name and the other way round.
                if req.path is not None:
                    path, env_var_name = req.path.strip(), None
                elif req.local_env_var_name is not None:
                    path, env_var_name = None, req.local_env_var_name
                else:
                    path, env_var_name = row.path, row.local_env_var_name
                merged = DatasetLocationReq(
                    dataset_id=row.dataset_id,
                    location_type=req.location_type if req.location_type is not None else row.location_type,
                    path=path,
                    local_env_var_name=env_var_name,
                    credentials_ref=req.credentials_ref if req.credentials_ref is not None else row.credentials_ref,
                )
                if _result_is_invalid(merged):
                    return INVALID_INPUT
                dataset = session.get(DatasetModel, row.dataset_id)
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset.code:
                    return INVALID_INPUT
                if session.scalars(_same_place_query(merged).where(DatasetLocationModel.id != row.id)).first() is not None:
                    return CONFLICT
                row.location_type = merged.location_type
                row.path = merged.path
                row.local_env_var_name = merged.local_env_var_name
                row.credentials_ref = merged.credentials_ref
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same place at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets_location update failed")
            return FAILURE

    def delete(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                chosen = select(MioDatasetModel.id).where(MioDatasetModel.dataset_location_id == row.id)
                if session.scalars(chosen).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("datasets_location delete failed")
            return FAILURE
