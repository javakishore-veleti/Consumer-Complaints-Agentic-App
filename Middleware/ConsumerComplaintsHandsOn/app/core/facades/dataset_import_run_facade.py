"""Facade for dataset import run register/list (M11)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.common.singleton import SingletonMeta


class DatasetImportRunFacade(metaclass=SingletonMeta):
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
