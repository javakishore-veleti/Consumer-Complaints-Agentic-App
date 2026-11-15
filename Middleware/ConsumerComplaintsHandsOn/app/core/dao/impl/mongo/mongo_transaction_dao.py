"""TransactionDao on Mongo: process-local handle with before-image rollback (D79)."""

import logging

from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.impl.mongo.client import get_mongo_db
from app.core.dao.impl.mongo.unit_of_work import MongoHandleConfig, MongoTxnHandle
from app.core.dao.transaction_dao import TransactionDao

log = logging.getLogger(__name__)


class MongoTransactionDao(TransactionDao):
    def begin(self, ctx: TransactionCtx) -> int:
        try:
            ctx.handle = MongoTxnHandle(MongoHandleConfig(db=get_mongo_db(), tracking=True))
            return SUCCESS
        except Exception:
            log.exception("mongo begin transaction failed")
            return FAILURE

    def commit(self, ctx: TransactionCtx) -> int:
        if not isinstance(ctx.handle, MongoTxnHandle):
            return INVALID_INPUT
        try:
            ctx.handle.commit()
            return SUCCESS
        except Exception:
            log.exception("mongo commit failed")
            return FAILURE
        finally:
            ctx.handle = None

    def rollback(self, ctx: TransactionCtx) -> int:
        if not isinstance(ctx.handle, MongoTxnHandle):
            return INVALID_INPUT
        try:
            ctx.handle.rollback()
            return SUCCESS
        except Exception:
            log.exception("mongo rollback failed")
            return FAILURE
        finally:
            ctx.handle = None
