"""MioAclDao on SQLAlchemy (D89)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.app_types_constants import MioAudience
from app.core.common.dtos.mio_acl_dtos import MioAclCtx, MioAclRecord, MioAclReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import MioAclModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_acl_dao import MioAclDao

log = logging.getLogger(__name__)


def _to_record(row: MioAclModel) -> MioAclRecord:
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioAclRecord(id=row.id, mio_id=row.mio_id, audience=row.audience, created_at=created)


def _same_query(req: MioAclReq) -> Select:
    return select(MioAclModel.id).where(
        MioAclModel.mio_id == req.mio_id, MioAclModel.audience == req.audience
    )


class SqlAlchemyMioAclDao(MioAclDao):
    def create(self, ctx: MioAclCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.audience):
            return INVALID_INPUT
        if req.audience not in MioAudience.values():
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None:
                    return NOT_FOUND
                if session.scalars(_same_query(req)).first() is not None:
                    return CONFLICT
                row = MioAclModel(
                    id=str(uuid4()),
                    mio_id=req.mio_id,
                    audience=req.audience,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("mios_acl create failed")
            return FAILURE

    def list(self, ctx: MioAclCtx) -> int:
        req = ctx.req
        try:
            query = select(MioAclModel)
            if req.mio_id is not None:
                query = query.where(MioAclModel.mio_id == req.mio_id)
            if req.audience is not None:
                query = query.where(MioAclModel.audience == req.audience)
            query = query.order_by(MioAclModel.created_at, MioAclModel.id)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_acl list failed")
            return FAILURE

    def delete(self, ctx: MioAclCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioAclModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios_acl delete failed")
            return FAILURE
