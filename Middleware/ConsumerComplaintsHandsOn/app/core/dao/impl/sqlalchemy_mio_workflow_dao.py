"""MioWorkflowDao on SQLAlchemy (D84)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowRecord, MioWorkflowReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import AppWfModel, MioModel, MioWorkflowModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_workflow_dao import MioWorkflowDao

log = logging.getLogger(__name__)


def _to_record(row: MioWorkflowModel) -> MioWorkflowRecord:
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioWorkflowRecord(
        id=row.id,
        mio_id=row.mio_id,
        workflow_id=row.workflow_id,
        created_at=created,
    )


def _same_link_query(req: MioWorkflowReq) -> Select:
    return select(MioWorkflowModel.id).where(
        MioWorkflowModel.mio_id == req.mio_id, MioWorkflowModel.workflow_id == req.workflow_id
    )


class SqlAlchemyMioWorkflowDao(MioWorkflowDao):
    def create(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.workflow_id):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None or session.get(AppWfModel, req.workflow_id) is None:
                    return NOT_FOUND
                if session.scalars(_same_link_query(req)).first() is not None:
                    return CONFLICT
                row = MioWorkflowModel(
                    id=str(uuid4()),
                    mio_id=req.mio_id,
                    workflow_id=req.workflow_id,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("mios_workflows create failed")
            return FAILURE

    def get(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioWorkflowModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_workflows get failed")
            return FAILURE

    def list(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        try:
            query = select(MioWorkflowModel)
            if req.mio_id is not None:
                query = query.where(MioWorkflowModel.mio_id == req.mio_id)
            if req.workflow_id is not None:
                query = query.where(MioWorkflowModel.workflow_id == req.workflow_id)
            query = query.order_by(MioWorkflowModel.created_at, MioWorkflowModel.id)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_workflows list failed")
            return FAILURE

    def delete(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioWorkflowModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios_workflows delete failed")
            return FAILURE
