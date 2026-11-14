"""AppWfDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select

from app.core.common.app_types_constants import EngineType
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.impl.models import AppWfModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

NAME_MAX = 100
ENGINE_WORKFLOW_ID_MAX = 255


def _to_record(row: AppWfModel) -> AppWfRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return AppWfRecord(
        id=row.id,
        workflow_name=row.workflow_name,
        engine_type=row.engine_type,
        engine_workflow_id=row.engine_workflow_id,
        config=row.config,
        enabled=row.enabled,
        created_at=created,
        updated_at=updated,
    )


def _has_invalid_field(req: AppWfReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    if req.workflow_name is not None and (not req.workflow_name.strip() or len(req.workflow_name) > NAME_MAX):
        return True
    if req.engine_type is not None and req.engine_type not in EngineType.values():
        return True
    if req.engine_workflow_id is not None and (
        not req.engine_workflow_id.strip() or len(req.engine_workflow_id) > ENGINE_WORKFLOW_ID_MAX
    ):
        return True
    return False


def _by_name_query(req: AppWfReq) -> Select:
    return select(AppWfModel).where(AppWfModel.workflow_name == req.workflow_name)


class SqlAlchemyAppWfDao(AppWfDao):
    def create(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (req.workflow_name and req.engine_type and req.engine_workflow_id) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.scalars(_by_name_query(req)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = AppWfModel(
                    id=str(uuid4()),
                    workflow_name=req.workflow_name,
                    engine_type=req.engine_type,
                    engine_workflow_id=req.engine_workflow_id,
                    config=req.config,
                    enabled=True if req.enabled is None else req.enabled,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows create failed")
            return FAILURE

    def get(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (req.id or req.workflow_name):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id) if req.id else session.scalars(_by_name_query(req)).first()
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows get failed")
            return FAILURE

    def list(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        try:
            query = select(AppWfModel)
            if req.engine_type is not None:
                query = query.where(AppWfModel.engine_type == req.engine_type)
            if req.enabled is not None:
                query = query.where(AppWfModel.enabled == req.enabled)
            query = query.order_by(AppWfModel.workflow_name)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows list failed")
            return FAILURE

    def update(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id)
                if row is None:
                    return NOT_FOUND
                if req.workflow_name is not None and req.workflow_name != row.workflow_name:
                    if session.scalars(_by_name_query(req)).first() is not None:
                        return CONFLICT
                if req.workflow_name is not None:
                    row.workflow_name = req.workflow_name
                if req.engine_type is not None:
                    row.engine_type = req.engine_type
                if req.engine_workflow_id is not None:
                    row.engine_workflow_id = req.engine_workflow_id
                if req.config is not None:
                    row.config = req.config
                if req.enabled is not None:
                    row.enabled = req.enabled
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows update failed")
            return FAILURE

    def delete(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("app_workflows delete failed")
            return FAILURE
