"""Callback + portal routes for dataset_import_runs (M11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.dataset_import_run_models import (
    DatasetImportRunCreateReq,
    DatasetImportRunListReq,
    DatasetImportRunOut,
    DatasetImportRunUpdateReq,
)
from app.core.common.dtos.dataset_import_run_dtos import (
    DatasetImportRunCtx,
    DatasetImportRunReq,
)
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


def _out(record) -> DatasetImportRunOut:
    return DatasetImportRunOut.model_validate(record, from_attributes=True)


def _check(code: int) -> None:
    if code == SUCCESS:
        return
    if code == NOT_FOUND:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "import run not found")
    if code == CONFLICT:
        raise HTTPException(status.HTTP_409_CONFLICT, "import run conflict")
    if code == INVALID_INPUT:
        raise HTTPException(422, "invalid request")
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")


class DatasetImportRunCallbackApi(metaclass=SingletonMeta):
    """Engine-facing create/update under /callbacks (secret attached by factory)."""

    def __init__(self):
        self.router = APIRouter(prefix="/callbacks", tags=["callbacks"])
        self.router.add_api_route(
            "/dataset-import-runs",
            self.create,
            methods=["POST"],
            response_model=DatasetImportRunOut,
        )
        self.router.add_api_route(
            "/dataset-import-runs/{import_id}",
            self.update,
            methods=["PATCH"],
            response_model=DatasetImportRunOut,
        )

    def create(self, req: Annotated[DatasetImportRunCreateReq, Depends()]) -> DatasetImportRunOut:
        body = req.body
        ctx = DatasetImportRunCtx(
            req=DatasetImportRunReq(
                id=body.id,
                run_folder_name=body.run_folder_name,
                location_kind=body.location_kind,
                location_ref=body.location_ref,
                source_snapshot_start=body.source_snapshot_start,
                source_snapshot_end=body.source_snapshot_end,
                workflow_started_at=body.workflow_started_at,
                status=body.status,
                execution_id=body.execution_id,
                mio_id=body.mio_id,
                part_count=body.part_count,
                message=body.message,
            )
        )
        code = FacadesObjectsFactory.get_dataset_import_run_facade().create(ctx)
        _check(code)
        return _out(ctx.resp.records[0])

    def update(self, req: Annotated[DatasetImportRunUpdateReq, Depends()]) -> DatasetImportRunOut:
        body = req.body
        ctx = DatasetImportRunCtx(
            req=DatasetImportRunReq(
                id=req.import_id,
                status=body.status,
                workflow_completed_at=body.workflow_completed_at,
                ingested_at=body.ingested_at,
                part_count=body.part_count,
                message=body.message,
                execution_id=body.execution_id,
            )
        )
        code = FacadesObjectsFactory.get_dataset_import_run_facade().update(ctx)
        _check(code)
        return _out(ctx.resp.records[0])


class DatasetImportRunApi(metaclass=SingletonMeta):
    """Portal-facing list under /dataset-import-runs (no callback secret)."""

    def __init__(self):
        self.router = APIRouter(prefix="/dataset-import-runs", tags=["dataset-import-runs"])
        self.router.add_api_route(
            "",
            self.list_runs,
            methods=["GET"],
            response_model=list[DatasetImportRunOut],
        )

    def list_runs(
        self, req: Annotated[DatasetImportRunListReq, Depends()]
    ) -> list[DatasetImportRunOut]:
        ctx = DatasetImportRunCtx(
            req=DatasetImportRunReq(
                eligible_only=req.eligible_only,
                status=req.status,
                limit=req.limit,
                offset=req.offset,
            )
        )
        code = FacadesObjectsFactory.get_dataset_import_run_facade().list(ctx)
        _check(code)
        return [_out(r) for r in ctx.resp.records]
