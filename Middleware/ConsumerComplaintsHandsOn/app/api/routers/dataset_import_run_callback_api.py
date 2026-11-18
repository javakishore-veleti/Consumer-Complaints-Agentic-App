"""Callback + portal routes for dataset_import_runs (M11 + M17-0004)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.dataset_import_run_models import (
    DatasetImportRunCreateReq,
    DatasetImportRunListReq,
    DatasetImportRunOut,
    DatasetImportRunTagOut,
    DatasetImportRunTagsListReq,
    DatasetImportRunTagsReq,
    DatasetImportRunUpdateReq,
)
from app.core.common.dtos.dataset_import_run_dtos import DatasetImportRunCtx, DatasetImportRunReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


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
                comment=body.comment,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().create(ctx)
        self._check(ctx)
        return DatasetImportRunOut.model_validate(ctx.resp.records[0], from_attributes=True)

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
                comment=body.comment,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().update(ctx)
        self._check(ctx)
        return DatasetImportRunOut.model_validate(ctx.resp.records[0], from_attributes=True)

    @staticmethod
    def _check(ctx: DatasetImportRunCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "import run not found")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "import run conflict")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")


class DatasetImportRunApi(metaclass=SingletonMeta):
    """Portal-facing list/tags under /dataset-import-runs (no callback secret)."""

    def __init__(self):
        self.router = APIRouter(prefix="/dataset-import-runs", tags=["dataset-import-runs"])
        self.router.add_api_route(
            "",
            self.list_runs,
            methods=["GET"],
            response_model=list[DatasetImportRunOut],
        )
        self.router.add_api_route(
            "/{import_id}/tags",
            self.add_tags,
            methods=["POST"],
            response_model=list[DatasetImportRunTagOut],
        )
        self.router.add_api_route(
            "/{import_id}/tags",
            self.list_tags,
            methods=["GET"],
            response_model=list[DatasetImportRunTagOut],
        )
        self.router.add_api_route(
            "/{import_id}",
            self.patch_run,
            methods=["PATCH"],
            response_model=DatasetImportRunOut,
        )

    def list_runs(
        self, req: Annotated[DatasetImportRunListReq, Depends()]
    ) -> list[DatasetImportRunOut]:
        ctx = DatasetImportRunCtx(
            req=DatasetImportRunReq(
                eligible_only=req.eligible_only,
                status=req.status,
                tag=req.tag,
                limit=req.limit,
                offset=req.offset,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().list(ctx)
        self._check(ctx)
        return [
            DatasetImportRunOut.model_validate(r, from_attributes=True) for r in ctx.resp.records
        ]

    def add_tags(
        self, req: Annotated[DatasetImportRunTagsReq, Depends()]
    ) -> list[DatasetImportRunTagOut]:
        ctx = DatasetImportRunCtx(
            req=DatasetImportRunReq(id=req.import_id, tags=list(req.body.tags))
        )
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().add_tags(ctx)
        self._check(ctx)
        return [
            DatasetImportRunTagOut.model_validate(r, from_attributes=True)
            for r in ctx.resp.tag_records
        ]

    def list_tags(
        self, req: Annotated[DatasetImportRunTagsListReq, Depends()]
    ) -> list[DatasetImportRunTagOut]:
        ctx = DatasetImportRunCtx(req=DatasetImportRunReq(id=req.import_id))
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().list_tags(ctx)
        self._check(ctx)
        return [
            DatasetImportRunTagOut.model_validate(r, from_attributes=True)
            for r in ctx.resp.tag_records
        ]

    def patch_run(
        self, req: Annotated[DatasetImportRunUpdateReq, Depends()]
    ) -> DatasetImportRunOut:
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
                comment=body.comment,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_dataset_import_run_facade().update(ctx)
        self._check(ctx)
        return DatasetImportRunOut.model_validate(ctx.resp.records[0], from_attributes=True)

    @staticmethod
    def _check(ctx: DatasetImportRunCtx) -> None:
        DatasetImportRunCallbackApi._check(ctx)
