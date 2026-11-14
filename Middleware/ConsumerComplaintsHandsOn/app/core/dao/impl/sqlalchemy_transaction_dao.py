"""TransactionDao on SQLAlchemy: the handle is a Session."""

import logging

from sqlalchemy.orm import Session

from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.impl.database import get_engine
from app.core.dao.transaction_dao import TransactionDao

log = logging.getLogger(__name__)


class SqlAlchemyTransactionDao(TransactionDao):
    def begin(self, ctx: TransactionCtx) -> int:
        try:
            ctx.handle = Session(get_engine())
            return SUCCESS
        except Exception:
            log.exception("begin transaction failed")
            return FAILURE

    def commit(self, ctx: TransactionCtx) -> int:
        if not isinstance(ctx.handle, Session):
            return INVALID_INPUT
        try:
            ctx.handle.commit()
            return SUCCESS
        except Exception:
            log.exception("commit failed")
            return FAILURE
        finally:
            ctx.handle.close()
            ctx.handle = None

    def rollback(self, ctx: TransactionCtx) -> int:
        if not isinstance(ctx.handle, Session):
            return INVALID_INPUT
        try:
            ctx.handle.rollback()
            return SUCCESS
        except Exception:
            log.exception("rollback failed")
            return FAILURE
        finally:
            ctx.handle.close()
            ctx.handle = None
