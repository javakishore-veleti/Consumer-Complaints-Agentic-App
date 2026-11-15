"""The portal's read of every MIO with its latest ingest status, as a class (D29, D61). It is a singleton.

No callback secret: the portal calls this from a browser (D59). Methods are plain `def` so FastAPI runs the blocking
database calls in a worker thread.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.models.mio_status_models import MioStatusIngestOut, MioStatusListReq, MioStatusOut
from app.api.models.wf_exec_callback_models import AppWfExecLogOut
from app.core.common.dtos.mio_status_dtos import MioStatusEntry, MioStatusReq
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class MioStatusApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/mios", tags=["mios"])
        self.router.add_api_route(
            "/status",
            self.list_status,
            methods=["GET"],
            response_model=list[MioStatusOut],
        )

    def list_status(self, req: Annotated[MioStatusListReq, Query()]) -> list[MioStatusOut]:
        ctx = MioStatusFacadeCtx(req=MioStatusReq(mio_id=req.mio_id))
        FacadesObjectsFactory.get_mio_status_facade().read(ctx)
        self._check(ctx)
        return [self._entry(e) for e in ctx.resp.entries]

    @staticmethod
    def _entry(entry: MioStatusEntry) -> MioStatusOut:
        ingest = entry.latest_ingest
        return MioStatusOut(
            id=entry.id,
            name=entry.name,
            description=entry.description,
            latest_ingest=(
                None
                if ingest is None
                else MioStatusIngestOut(
                    id=ingest.id,
                    mio_id=ingest.mio_id,
                    status=ingest.status,
                    message=ingest.message,
                    rows_loaded=ingest.rows_loaded,
                    batch_count=ingest.batch_count,
                    increment_marker=ingest.increment_marker,
                    requested_at=ingest.requested_at,
                    started_at=ingest.started_at,
                    finished_at=ingest.finished_at,
                    executions=[AppWfExecLogOut.model_validate(x) for x in ingest.executions],
                )
            ),
        )

    @staticmethod
    def _check(ctx: MioStatusFacadeCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "mio not found")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
