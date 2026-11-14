"""MioDatasetDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioModel, DatasetModel and DatasetLocationModel to keep the parent rules (no foreign keys, D57)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetRecord, MioDatasetReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_dataset_dao import MioDatasetDao

log = logging.getLogger(__name__)


def _to_record(row: MioDatasetModel) -> MioDatasetRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioDatasetRecord(
        id=row.id,
        mio_id=row.mio_id,
        dataset_id=row.dataset_id,
        dataset_location_id=row.dataset_location_id,
        created_at=created,
    )


def _same_link_query(req: MioDatasetReq) -> Select:
    """Ids of rows where the MIO already uses the dataset."""
    return select(MioDatasetModel.id).where(
        MioDatasetModel.mio_id == req.mio_id, MioDatasetModel.dataset_id == req.dataset_id
    )


class SqlAlchemyMioDatasetDao(MioDatasetDao):
    def create(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.dataset_id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None or session.get(DatasetModel, req.dataset_id) is None:
                    return NOT_FOUND
                location = session.get(DatasetLocationModel, req.dataset_location_id)
                if location is None:
                    return NOT_FOUND
                if location.dataset_id != req.dataset_id:
                    return INVALID_INPUT
                if session.scalars(_same_link_query(req)).first() is not None:
                    return CONFLICT
                row = MioDatasetModel(
                    id=str(uuid4()),
                    mio_id=req.mio_id,
                    dataset_id=req.dataset_id,
                    dataset_location_id=req.dataset_location_id,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers linked the same MIO and dataset at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios_datasets create failed")
            return FAILURE

    def get(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets get failed")
            return FAILURE

    def list(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        try:
            query = select(MioDatasetModel)
            if req.mio_id is not None:
                query = query.where(MioDatasetModel.mio_id == req.mio_id)
            if req.dataset_id is not None:
                query = query.where(MioDatasetModel.dataset_id == req.dataset_id)
            query = query.order_by(MioDatasetModel.created_at, MioDatasetModel.id)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets list failed")
            return FAILURE

    def update(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                if (req.mio_id is not None and req.mio_id != row.mio_id) or (
                    req.dataset_id is not None and req.dataset_id != row.dataset_id
                ):
                    return INVALID_INPUT
                location = session.get(DatasetLocationModel, req.dataset_location_id)
                if location is None:
                    return NOT_FOUND
                if location.dataset_id != row.dataset_id:
                    return INVALID_INPUT
                row.dataset_location_id = req.dataset_location_id
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets update failed")
            return FAILURE

    def delete(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios_datasets delete failed")
            return FAILURE
