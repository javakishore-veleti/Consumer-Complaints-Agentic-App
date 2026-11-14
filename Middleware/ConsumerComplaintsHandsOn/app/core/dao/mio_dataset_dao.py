"""Interface of the DAO for the mios_datasets table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx
from app.core.common.singleton import SingletonMeta


class MioDatasetDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioDatasetCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    A row says "this MIO uses this dataset, read from this location of it". A MIO has at most one row per dataset;
    many MIOs may share the same dataset and the same location (D57). This is the only link between a MIO and its
    data: nothing is derived from the MIO's name."""

    @abstractmethod
    def create(self, ctx: MioDatasetCtx) -> int:
        """Needs req.mio_id, req.dataset_id and req.dataset_location_id. INVALID_INPUT if one is missing or the
        location belongs to another dataset, NOT_FOUND if the MIO, the dataset or the location does not exist,
        CONFLICT if the MIO already uses the dataset."""

    @abstractmethod
    def get(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: MioDatasetCtx) -> int:
        """Optional filters: req.mio_id, req.dataset_id. Ordered by created_at, id."""

    @abstractmethod
    def update(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id and req.dataset_location_id: only the chosen location can change, and it must belong to the
        row's dataset (INVALID_INPUT otherwise). A req.mio_id or req.dataset_id that is not the row's own is
        INVALID_INPUT. NOT_FOUND if the row or the new location does not exist."""

    @abstractmethod
    def delete(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row."""
