"""DatasetImportRunService → DAO (M11)."""

from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.dataset_import_run_service import DatasetImportRunService


class DatasetImportRunServiceImpl(DatasetImportRunService):
    def create(self, ctx: DatasetImportRunCtx) -> int:
        return DaoObjectsFactory.get_dataset_import_run_dao().create(ctx)

    def update(self, ctx: DatasetImportRunCtx) -> int:
        return DaoObjectsFactory.get_dataset_import_run_dao().update(ctx)

    def get(self, ctx: DatasetImportRunCtx) -> int:
        return DaoObjectsFactory.get_dataset_import_run_dao().get(ctx)

    def list(self, ctx: DatasetImportRunCtx) -> int:
        return DaoObjectsFactory.get_dataset_import_run_dao().list(ctx)
