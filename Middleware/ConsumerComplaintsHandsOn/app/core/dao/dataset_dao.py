"""Interface of the DAO for the datasets table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_dtos import DatasetCtx
from app.core.common.singleton import SingletonMeta


class DatasetDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DatasetCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    Names are trimmed and case sensitive. The code is 1 to 15 characters of A-Z and 0-9 and builds the local env var
    name LOCAL_DATA_PATH_<code> (D57). A CONFLICT caused by two writers taking the same name or code at once comes
    from the database constraint; inside a shared transaction the session is then unusable and the owner must
    roll back."""

    @abstractmethod
    def create(self, ctx: DatasetCtx) -> int:
        """Needs req.name (up to 100 characters) and req.code. Optional: description. INVALID_INPUT for a missing or
        unacceptable field, CONFLICT if the name or the code is taken."""

    @abstractmethod
    def get(self, ctx: DatasetCtx) -> int:
        """Needs req.id or req.name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is no such
        row."""

    @abstractmethod
    def list(self, ctx: DatasetCtx) -> int:
        """Every dataset, ordered by name."""

    @abstractmethod
    def update(self, ctx: DatasetCtx) -> int:
        """Needs req.id. Changes the given name, code and description and sets updated_at. NOT_FOUND if there is no
        such row, INVALID_INPUT for an unacceptable field, CONFLICT if the new name or code belongs to another row, or
        if the code changes while a location of the dataset holds an env var name built from the old code."""

    @abstractmethod
    def delete(self, ctx: DatasetCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a location or a
        mios_datasets row still uses the dataset (no foreign key: this DAO keeps the rule, D57)."""
