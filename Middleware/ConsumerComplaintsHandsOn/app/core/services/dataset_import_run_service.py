"""Service interface for dataset_import_runs (M11 + M17-0004)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.common.singleton import SingletonMeta


class DatasetImportRunService(metaclass=SingletonMeta):
    @abstractmethod
    def create(self, ctx: DatasetImportRunCtx) -> int:
        ...

    @abstractmethod
    def update(self, ctx: DatasetImportRunCtx) -> int:
        ...

    @abstractmethod
    def get(self, ctx: DatasetImportRunCtx) -> int:
        ...

    @abstractmethod
    def list(self, ctx: DatasetImportRunCtx) -> int:
        ...

    @abstractmethod
    def add_tags(self, ctx: DatasetImportRunCtx) -> int:
        ...

    @abstractmethod
    def list_tags(self, ctx: DatasetImportRunCtx) -> int:
        ...
