"""Interface of the DAO for the datasets_location table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx
from app.core.common.singleton import SingletonMeta


class DatasetLocationDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DatasetLocationCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    A location has a path (a literal path or a URL) or a local_env_var_name, never both and never neither. The
    local_env_var_name is only allowed for the type "local", is only a NAME (never a value), and must be exactly
    LOCAL_DATA_PATH_ plus the code of the dataset. credentials_ref is a name (letters, digits, _ . -), never a
    secret. Types are the values of DatasetLocationType (D57)."""

    @abstractmethod
    def create(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.dataset_id, req.location_type and exactly one of req.path (up to 1000 characters after
        trimming) and req.local_env_var_name. Optional: credentials_ref, description. NOT_FOUND if the dataset does
        not exist, INVALID_INPUT for a missing or unacceptable field, CONFLICT if the dataset already has that type and
        path, or that env var name."""

    @abstractmethod
    def get(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: DatasetLocationCtx) -> int:
        """Optional filters: req.dataset_id, req.location_type. Ordered by location_type, rows with a path before
        rows without, path, id."""

    @abstractmethod
    def update(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. Changes the given location_type, path, local_env_var_name, credentials_ref and description
        and sets updated_at. Giving path clears local_env_var_name and giving local_env_var_name clears path; giving
        both is INVALID_INPUT. The resulting row must follow the rules above. A req.dataset_id that is not the row's
        own is INVALID_INPUT (a location does not move). NOT_FOUND if there is no such row, CONFLICT if the result
        equals another location of the dataset."""

    @abstractmethod
    def delete(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a mios_datasets
        row chose this location (no foreign key: this DAO keeps the rule, D57)."""
