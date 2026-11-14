"""Data ingest log endpoints, as a class. It is a singleton (like every class in api, facades, services and dao).

Every method takes exactly one request object (FastAPI fills it from the path, query string or body), builds a facade
ctx from it, calls the facade interface, and turns the facade's result code into an HTTP status. Methods are plain
`def` so FastAPI runs the blocking database calls in a worker thread.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.models.data_ingest_models import (
    DataIngestLogCreate,
    DataIngestLogIdReq,
    DataIngestLogListReq,
    DataIngestLogOut,
    DataIngestLogUpdateReq,
)
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx, DataIngestFacadeReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class DataIngestApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/data-ingest-logs", tags=["data-ingest-logs"])
        self.router.add_api_route(
            "", self.create_log, methods=["POST"], response_model=DataIngestLogOut, status_code=status.HTTP_201_CREATED
        )
        self.router.add_api_route("", self.list_logs, methods=["GET"], response_model=list[DataIngestLogOut])
        self.router.add_api_route("/{log_id}", self.get_log, methods=["GET"], response_model=DataIngestLogOut)
        self.router.add_api_route("/{log_id}", self.update_log, methods=["PATCH"], response_model=DataIngestLogOut)
        self.router.add_api_route(
            "/{log_id}", self.delete_log, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT
        )

    def create_log(self, req: DataIngestLogCreate) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(**req.model_dump()))
        FacadesObjectsFactory.get_data_ingest_facade().create(ctx)
        return self._one(ctx)

    def list_logs(self, req: Annotated[DataIngestLogListReq, Query()]) -> list[DataIngestLogOut]:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(**req.model_dump()))
        FacadesObjectsFactory.get_data_ingest_facade().list(ctx)
        self._check(ctx)
        return [DataIngestLogOut.model_validate(r) for r in ctx.resp.records]

    def get_log(self, req: Annotated[DataIngestLogIdReq, Depends()]) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=req.log_id))
        FacadesObjectsFactory.get_data_ingest_facade().get(ctx)
        return self._one(ctx)

    def update_log(self, req: Annotated[DataIngestLogUpdateReq, Depends()]) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=req.log_id, **req.body.model_dump()))
        FacadesObjectsFactory.get_data_ingest_facade().update(ctx)
        return self._one(ctx)

    def delete_log(self, req: Annotated[DataIngestLogIdReq, Depends()]) -> Response:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=req.log_id))
        FacadesObjectsFactory.get_data_ingest_facade().delete(ctx)
        self._check(ctx)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    def _one(self, ctx: DataIngestFacadeCtx) -> DataIngestLogOut:
        self._check(ctx)
        return DataIngestLogOut.model_validate(ctx.resp.records[0])

    @staticmethod
    def _check(ctx: DataIngestFacadeCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "data ingest log not found")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "status change not allowed in the current state")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
