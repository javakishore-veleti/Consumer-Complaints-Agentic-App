"""Thin facade → DatasetImportRunService."""

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.facades.dataset_import_run_facade import DatasetImportRunFacade
from app.core.services.objects_factory import ServicesObjectsFactory


class DatasetImportRunFacadeImpl(DatasetImportRunFacade):
    def create(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().create(ctx)

    def update(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().update(ctx)

    def get(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().get(ctx)

    def list(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().list(ctx)

    def add_tags(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().add_tags(ctx)

    def list_tags(self, ctx: DatasetImportRunCtx) -> int:
        return ServicesObjectsFactory.get_dataset_import_run_service().list_tags(ctx)
