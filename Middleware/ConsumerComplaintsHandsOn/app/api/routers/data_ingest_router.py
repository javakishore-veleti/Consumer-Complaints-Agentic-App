"""Data ingest log endpoints. The API only builds a ctx, calls the facade interface, and turns the integer code
into an HTTP status. Handlers are plain `def` so FastAPI runs the blocking database calls in a worker thread."""

from fastapi import APIRouter, HTTPException, Response, status

from app.api.models.data_ingest_models import DataIngestLogCreate, DataIngestLogOut, DataIngestLogUpdate
from app.core.common.dtos.data_ingest_facade_dtos import DataIngestFacadeCtx, DataIngestFacadeReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.facades.objects_factory import FacadesObjectsFactory

router = APIRouter(prefix="/data-ingest-logs", tags=["data-ingest-logs"])


def _check(code: int) -> None:
    if code == SUCCESS:
        return
    if code == NOT_FOUND:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "data ingest log not found")
    if code == INVALID_INPUT:
        raise HTTPException(422, "invalid request")
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")


@router.post("", response_model=DataIngestLogOut, status_code=status.HTTP_201_CREATED)
def create_log(body: DataIngestLogCreate) -> DataIngestLogOut:
    ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(**body.model_dump()))
    _check(FacadesObjectsFactory.get_data_ingest_facade().create(ctx))
    return DataIngestLogOut.model_validate(ctx.resp.records[0])


@router.get("", response_model=list[DataIngestLogOut])
def list_logs(
    purpose: str | None = None,
    status_: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[DataIngestLogOut]:
    ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(purpose=purpose, status=status_, limit=limit, offset=offset))
    _check(FacadesObjectsFactory.get_data_ingest_facade().list(ctx))
    return [DataIngestLogOut.model_validate(r) for r in ctx.resp.records]


@router.get("/{log_id}", response_model=DataIngestLogOut)
def get_log(log_id: str) -> DataIngestLogOut:
    ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id))
    _check(FacadesObjectsFactory.get_data_ingest_facade().get(ctx))
    return DataIngestLogOut.model_validate(ctx.resp.records[0])


@router.patch("/{log_id}", response_model=DataIngestLogOut)
def update_log(log_id: str, body: DataIngestLogUpdate) -> DataIngestLogOut:
    ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id, **body.model_dump()))
    _check(FacadesObjectsFactory.get_data_ingest_facade().update(ctx))
    return DataIngestLogOut.model_validate(ctx.resp.records[0])


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(log_id: str) -> Response:
    ctx = DataIngestFacadeCtx(req=DataIngestFacadeReq(id=log_id))
    _check(FacadesObjectsFactory.get_data_ingest_facade().delete(ctx))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
