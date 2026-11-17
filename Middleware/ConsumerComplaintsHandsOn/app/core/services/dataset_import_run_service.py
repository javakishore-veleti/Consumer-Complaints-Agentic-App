"""Service interface for dataset_import_runs (M11)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.common.singleton import SingletonMeta


class DatasetImportRunService(metaclass=SingletonMeta):
    @abstractmethod
    def create(self, ctx: DatasetImportRunCtx) -> int:
        """Register a new import run."""

    @abstractmethod
    def update(self, ctx: DatasetImportRunCtx) -> int:
        """Update status / finalize fields."""

    @abstractmethod
    def get(self, ctx: DatasetImportRunCtx) -> int:
        """Get one by id."""

    @abstractmethod
    def list(self, ctx: DatasetImportRunCtx) -> int:
        """List (optional eligible_only)."""
