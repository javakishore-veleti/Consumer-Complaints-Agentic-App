"""A transaction that several DAO calls share (DESIGN.md, section 2.4).

A service asks the transaction DAO to begin one, puts it on the ctx of every DAO call that belongs to it, and then
commits or rolls back. The handle is opaque: only dao/impl knows what is inside. With no transaction on the ctx, a
DAO call runs and commits on its own.
"""

from dataclasses import dataclass


@dataclass
class TransactionCtx:
    handle: object | None = None


@dataclass
class TransactionalCtx:
    """Base of every DAO ctx: carries the optional shared transaction."""

    transaction: TransactionCtx | None = None
