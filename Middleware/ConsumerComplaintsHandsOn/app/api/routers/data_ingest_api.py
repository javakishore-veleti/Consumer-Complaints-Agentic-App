"""Data ingest log endpoints, as a class. It is a singleton (like every class in api, facades, services and dao).

Each method builds a ctx, calls the facade interface, and turns the integer code into an HTTP status. Methods are
plain `def` so FastAPI runs the blocking database calls in a worker thread. HTTP parameters cannot be a ctx, so the
methods take the request pieces FastAPI gives them and put them into the facade ctx straight away.
"""

from fastapi import APIRouter, HTTPException, Response, status

from app.api.models.data_ingest_models import DataIngestLogCreate, DataIngestLogOut, DataIngestLogUpdate
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

    def create_log(self, body: DataIngestLogCreate) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(**body.model_dump()))
        self._check(FacadesObjectsFactory.get_data_ingest_facade().create(ctx))
        return DataIngestLogOut.model_validate(ctx.resp.records[0])

    def list_logs(
        self,
        purpose: str | None = None,
        status_: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[DataIngestLogOut]:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(purpose=purpose, status=status_, limit=limit, offset=offset))
        self._check(FacadesObjectsFactory.get_data_ingest_facade().list(ctx))
        return [DataIngestLogOut.model_validate(r) for r in ctx.resp.records]

    def get_log(self, log_id: str) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id))
        self._check(FacadesObjectsFactory.get_data_ingest_facade().get(ctx))
        return DataIngestLogOut.model_validate(ctx.resp.records[0])

    def update_log(self, log_id: str, body: DataIngestLogUpdate) -> DataIngestLogOut:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id, **body.model_dump()))
        self._check(FacadesObjectsFactory.get_data_ingest_facade().update(ctx))
        return DataIngestLogOut.model_validate(ctx.resp.records[0])

    def delete_log(self, log_id: str) -> Response:
        ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id))
        self._check(FacadesObjectsFactory.get_data_ingest_facade().delete(ctx))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _check(code: int) -> None:
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "data ingest log not found")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "status change not allowed in the current state")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
