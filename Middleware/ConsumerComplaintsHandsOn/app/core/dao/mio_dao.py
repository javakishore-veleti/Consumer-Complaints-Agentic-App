"""Interface of the DAO for the mios table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_dtos import MioCtx
from app.core.common.singleton import SingletonMeta


class MioDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    Names are trimmed and case sensitive, and are labels for people: no code reads a name or a description to choose
    data (D57). The data of a MIO is what mios_datasets links."""

    @abstractmethod
    def create(self, ctx: MioCtx) -> int:
        """Needs req.name (up to 100 characters). Optional: description. INVALID_INPUT for a missing or unacceptable
        name, CONFLICT if the name is taken."""

    @abstractmethod
    def get(self, ctx: MioCtx) -> int:
        """Needs req.id or req.name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is no such
        row."""

    @abstractmethod
    def list(self, ctx: MioCtx) -> int:
        """Every MIO, ordered by name."""

    @abstractmethod
    def update(self, ctx: MioCtx) -> int:
        """Needs req.id. Changes the given name and description and sets updated_at. NOT_FOUND if there is no such
        row, INVALID_INPUT for an unacceptable name, CONFLICT if the new name belongs to another row."""

    @abstractmethod
    def delete(self, ctx: MioCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a mios_datasets
        row still links the MIO (no foreign key: this DAO keeps the rule, D57)."""
