"""DAO interface for dataset_import_runs (M11)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.common.singleton import SingletonMeta


class DatasetImportRunDao(metaclass=SingletonMeta):
    @abstractmethod
    def create(self, ctx: DatasetImportRunCtx) -> int:
        """Create a staging/landed import run. Needs run_folder_name, location_*, snapshots, workflow_started_at."""

    @abstractmethod
    def get(self, ctx: DatasetImportRunCtx) -> int:
        """Needs req.id."""

    @abstractmethod
    def list(self, ctx: DatasetImportRunCtx) -> int:
        """Optional status / eligible_only / paging. Newest workflow_started_at first."""

    @abstractmethod
    def update(self, ctx: DatasetImportRunCtx) -> int:
        """Update status and related fields by id. CONFLICT on illegal transitions."""
