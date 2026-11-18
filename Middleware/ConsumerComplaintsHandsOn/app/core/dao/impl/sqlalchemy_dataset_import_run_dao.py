"""DatasetImportRunDao on SQLAlchemy (M11 + M17-0004 tags)."""

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
    DatasetImportRunTagRecord,
)
from app.core.common.return_codes import (
    CONFLICT,
    FAILURE,
    INVALID_INPUT,
    NOT_FOUND,
    SUCCESS,
)
from app.core.dao.dataset_import_run_dao import DatasetImportRunDao
from app.core.dao.impl.models import DatasetImportRunModel, DatasetImportRunTagModel
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


def _to_record(row: DatasetImportRunModel) -> DatasetImportRunRecord:
    times = {
        name: getattr(row, name)
        for name in (
            "source_snapshot_start",
            "source_snapshot_end",
            "workflow_started_at",
            "workflow_completed_at",
            "ingested_at",
            "created_at",
            "updated_at",
        )
    }
    for name, value in list(times.items()):
        times[name] = (
            value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value
        )
    return DatasetImportRunRecord(
        id=row.id,
        run_folder_name=row.run_folder_name,
        location_kind=row.location_kind,
        location_ref=row.location_ref,
        source_snapshot_start=times["source_snapshot_start"],
        source_snapshot_end=times["source_snapshot_end"],
        status=row.status,
        workflow_started_at=times["workflow_started_at"],
        workflow_completed_at=times["workflow_completed_at"],
        ingested_at=times["ingested_at"],
        mio_id=row.mio_id,
        execution_id=row.execution_id,
        part_count=row.part_count,
        message=row.message,
        comment=row.comment,
        created_at=times["created_at"],
        updated_at=times["updated_at"],
    )


def _to_tag_record(row: DatasetImportRunTagModel) -> DatasetImportRunTagRecord:
    created = row.created_at
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return DatasetImportRunTagRecord(
        id=row.id,
        import_run_id=row.import_run_id,
        tag=row.tag,
        created_at=created,
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
                    comment=req.comment,
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
        tag = req.tag.strip() if isinstance(req.tag, str) else req.tag
        if req.tag is not None and (not isinstance(req.tag, str) or not tag):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                q = select(DatasetImportRunModel).order_by(
                    DatasetImportRunModel.workflow_started_at.desc(),
                    DatasetImportRunModel.id.desc(),
                )
                if tag:
                    q = q.where(
                        DatasetImportRunModel.id.in_(
                            select(DatasetImportRunTagModel.import_run_id).where(
                                DatasetImportRunTagModel.tag == tag
                            )
                        )
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
                    values: dict = {"status": req.status, "updated_at": _now()}
                    if req.workflow_completed_at is not None:
                        values["workflow_completed_at"] = req.workflow_completed_at
                    if req.ingested_at is not None:
                        values["ingested_at"] = req.ingested_at
                    if req.part_count is not None:
                        values["part_count"] = req.part_count
                    if req.message is not None:
                        values["message"] = req.message
                    if req.comment is not None:
                        values["comment"] = req.comment
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
                        "comment",
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

    def add_tags(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.tags is None:
            return INVALID_INPUT
        tags: list[str] = []
        seen: set[str] = set()
        for item in req.tags:
            if not isinstance(item, str):
                return INVALID_INPUT
            tag = item.strip()
            if not tag or len(tag) > 255:
                return INVALID_INPUT
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
        if not tags:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetImportRunModel, req.id)
                if row is None:
                    return NOT_FOUND
                existing = set(
                    session.scalars(
                        select(DatasetImportRunTagModel.tag).where(
                            DatasetImportRunTagModel.import_run_id == req.id,
                            DatasetImportRunTagModel.tag.in_(tags),
                        )
                    ).all()
                )
                now = _now()
                for tag in tags:
                    if tag in existing:
                        continue
                    session.add(
                        DatasetImportRunTagModel(
                            id=str(uuid4()),
                            import_run_id=req.id,
                            tag=tag,
                            created_at=now,
                        )
                    )
                session.flush()
                rows = session.scalars(
                    select(DatasetImportRunTagModel)
                    .where(DatasetImportRunTagModel.import_run_id == req.id)
                    .order_by(DatasetImportRunTagModel.tag.asc())
                ).all()
                ctx.resp.tag_records = [_to_tag_record(r) for r in rows]
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("dataset_import_run add_tags failed")
            return FAILURE

    def list_tags(self, ctx: DatasetImportRunCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetImportRunModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                rows = session.scalars(
                    select(DatasetImportRunTagModel)
                    .where(DatasetImportRunTagModel.import_run_id == ctx.req.id)
                    .order_by(DatasetImportRunTagModel.tag.asc())
                ).all()
                ctx.resp.tag_records = [_to_tag_record(r) for r in rows]
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("dataset_import_run list_tags failed")
            return FAILURE
