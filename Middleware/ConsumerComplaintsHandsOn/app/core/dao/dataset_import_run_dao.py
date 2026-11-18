"""DAO interface for dataset_import_runs (M11) + tags (M17-0004)."""

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
        """Optional status / eligible_only / tag / paging. Newest workflow_started_at first."""

    @abstractmethod
    def update(self, ctx: DatasetImportRunCtx) -> int:
        """Update status and related fields by id. CONFLICT on illegal transitions."""

    @abstractmethod
    def add_tags(self, ctx: DatasetImportRunCtx) -> int:
        """Add req.tags for req.id (import run). Idempotent on (import_run_id, tag)."""

    @abstractmethod
    def list_tags(self, ctx: DatasetImportRunCtx) -> int:
        """List tags for req.id into resp.tag_records."""
