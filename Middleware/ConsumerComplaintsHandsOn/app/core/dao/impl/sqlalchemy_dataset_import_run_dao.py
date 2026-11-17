"""DatasetImportRunDao on SQLAlchemy (M11)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.dataset_import_run_dtos import (
    ELIGIBLE_FOR_INGEST,
    STATUS_FAILED,
    STATUS_INGESTED,
    STATUS_INGESTING,
    STATUS_LANDED,
    STATUS_STAGING,
    DatasetImportRunCtx,
    DatasetImportRunRecord,
)
from app.core.common.return_codes import (
    CONFLICT,
    FAILURE,
    INVALID_INPUT,
    NOT_FOUND,
    SUCCESS,
)
from app.core.dao.dataset_import_run_dao import DatasetImportRunDao
from app.core.dao.impl.models import DatasetImportRunModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

_ALLOWED = frozenset({STATUS_STAGING, STATUS_LANDED, STATUS_INGESTING, STATUS_INGESTED, STATUS_FAILED})
_TRANSITIONS = {
    STATUS_STAGING: frozenset({STATUS_LANDED, STATUS_FAILED}),
    STATUS_LANDED: frozenset({STATUS_INGESTING, STATUS_FAILED}),
    STATUS_INGESTING: frozenset({STATUS_INGESTED, STATUS_FAILED, STATUS_INGESTING}),
    STATUS_FAILED: frozenset({STATUS_INGESTING, STATUS_LANDED, STATUS_FAILED}),
    STATUS_INGESTED: frozenset({STATUS_INGESTED}),
}


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _to_record(row: DatasetImportRunModel) -> DatasetImportRunRecord:
    return DatasetImportRunRecord(
        id=row.id,
        run_folder_name=row.run_folder_name,
        location_kind=row.location_kind,
        location_ref=row.location_ref,
        source_snapshot_start=_aware(row.source_snapshot_start),  # type: ignore[arg-type]
        source_snapshot_end=_aware(row.source_snapshot_end),  # type: ignore[arg-type]
        status=row.status,
        workflow_started_at=_aware(row.workflow_started_at),  # type: ignore[arg-type]
        workflow_completed_at=_aware(row.workflow_completed_at),
        ingested_at=_aware(row.ingested_at),
        mio_id=row.mio_id,
        execution_id=row.execution_id,
        part_count=row.part_count,
        message=row.message,
        created_at=_aware(row.created_at),  # type: ignore[arg-type]
        updated_at=_aware(row.updated_at),  # type: ignore[arg-type]
    )


class SqlAlchemyDatasetImportRunDao(DatasetImportRunDao):
    def create(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if not (
            req.run_folder_name
            and req.location_kind
            and req.location_ref
            and req.source_snapshot_start
            and req.source_snapshot_end
            and req.workflow_started_at
        ):
            return INVALID_INPUT
        status = req.status or STATUS_STAGING
        if status not in _ALLOWED:
            return INVALID_INPUT
        now = _now()
        try:
            with unit_of_work(ctx) as session:
                row = DatasetImportRunModel(
                    id=(req.id.strip() if req.id and req.id.strip() else str(uuid4())),
                    run_folder_name=req.run_folder_name.strip(),
                    location_kind=req.location_kind.strip(),
                    location_ref=req.location_ref.strip(),
                    source_snapshot_start=req.source_snapshot_start,
                    source_snapshot_end=req.source_snapshot_end,
                    status=status,
                    workflow_started_at=req.workflow_started_at,
                    workflow_completed_at=req.workflow_completed_at,
                    ingested_at=req.ingested_at,
                    mio_id=req.mio_id,
                    execution_id=req.execution_id,
                    part_count=req.part_count,
                    message=req.message,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("dataset_import_run create failed")
            return FAILURE

    def get(self, ctx: DatasetImportRunCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetImportRunModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("dataset_import_run get failed")
            return FAILURE

    def list(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if req.limit is not None and (isinstance(req.limit, bool) or req.limit < 0):
            return INVALID_INPUT
        if req.offset is not None and (isinstance(req.offset, bool) or req.offset < 0):
            return INVALID_INPUT
        if req.status is not None and req.status not in _ALLOWED:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                q = select(DatasetImportRunModel).order_by(
                    DatasetImportRunModel.workflow_started_at.desc(),
                    DatasetImportRunModel.id.desc(),
                )
                if req.ids:
                    q = q.where(DatasetImportRunModel.id.in_(list(req.ids)))
                if req.status:
                    q = q.where(DatasetImportRunModel.status == req.status)
                if req.eligible_only:
                    q = q.where(DatasetImportRunModel.status.in_(sorted(ELIGIBLE_FOR_INGEST)))
                if req.offset:
                    q = q.offset(req.offset)
                if req.limit is not None:
                    q = q.limit(req.limit)
                rows = session.scalars(q).all()
                ctx.resp.records = [_to_record(r) for r in rows]
            return SUCCESS
        except Exception:
            log.exception("dataset_import_run list failed")
            return FAILURE

    def update(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in _ALLOWED:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetImportRunModel, req.id)
                if row is None:
                    return NOT_FOUND
                if req.status is not None and req.status != row.status:
                    allowed = _TRANSITIONS.get(row.status, frozenset())
                    if req.status not in allowed:
                        return CONFLICT
                    # optimistic: only match current status
                    values: dict = {"status": req.status, "updated_at": _now()}
                    if req.workflow_completed_at is not None:
                        values["workflow_completed_at"] = req.workflow_completed_at
                    if req.ingested_at is not None:
                        values["ingested_at"] = req.ingested_at
                    if req.part_count is not None:
                        values["part_count"] = req.part_count
                    if req.message is not None:
                        values["message"] = req.message
                    if req.status == STATUS_INGESTED and "ingested_at" not in values:
                        values["ingested_at"] = _now()
                    result = session.execute(
                        sql_update(DatasetImportRunModel)
                        .where(
                            DatasetImportRunModel.id == req.id,
                            DatasetImportRunModel.status == row.status,
                        )
                        .values(**values)
                    )
                    if result.rowcount != 1:
                        return CONFLICT
                    session.refresh(row)
                else:
                    changed = False
                    for name in (
                        "workflow_completed_at",
                        "ingested_at",
                        "part_count",
                        "message",
                        "execution_id",
                    ):
                        val = getattr(req, name)
                        if val is not None:
                            setattr(row, name, val)
                            changed = True
                    if changed:
                        row.updated_at = _now()
                        session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("dataset_import_run update failed")
            return FAILURE
