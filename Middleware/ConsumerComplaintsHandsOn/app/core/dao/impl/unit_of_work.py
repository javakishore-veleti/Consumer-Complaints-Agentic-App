"""One database session per DAO call, or the shared one when the ctx carries a transaction."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.common.dtos.transaction_dtos import TransactionalCtx
from app.core.dao.impl.database import get_engine


@contextmanager
def unit_of_work(ctx: TransactionalCtx) -> Iterator[Session]:
    shared = ctx.transaction.handle if ctx.transaction is not None else None
    if isinstance(shared, Session):
        yield shared
        shared.flush()  # the owner of the transaction commits
        return
    with Session(get_engine()) as session:
        yield session
        session.commit()
