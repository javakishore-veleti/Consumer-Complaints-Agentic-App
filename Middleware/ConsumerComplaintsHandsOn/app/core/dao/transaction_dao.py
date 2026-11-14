"""Interface of the DAO that starts and ends a transaction several DAO calls share (DESIGN.md, section 2.4)."""

from abc import abstractmethod

from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.singleton import SingletonMeta


class TransactionDao(metaclass=SingletonMeta):
    """Every method takes one TransactionCtx and returns an integer code. begin() fills ctx.handle; put the ctx on
    every DAO ctx that belongs to the transaction (`dao_ctx.transaction = ctx`); then commit() or rollback()."""

    @abstractmethod
    def begin(self, ctx: TransactionCtx) -> int: ...

    @abstractmethod
    def commit(self, ctx: TransactionCtx) -> int: ...

    @abstractmethod
    def rollback(self, ctx: TransactionCtx) -> int: ...
