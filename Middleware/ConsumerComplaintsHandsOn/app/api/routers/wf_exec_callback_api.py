"""The status callback a workflow engine (Airflow) calls, as a class (D29, D60). It is a singleton.

The callback secret check (D59) is not attached here: ApiObjectsFactory attaches it to the whole router when it
includes it. The method is plain `def` so FastAPI runs the blocking database calls in a worker thread.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.wf_exec_callback_models import (
    AppWfExecLogOut,
    MioIngestLogOut,
    WfExecStatusOut,
    WfExecStatusReportReq,
)
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusReq
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class WfExecCallbackApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/callbacks", tags=["callbacks"])
        self.router.add_api_route(
            "/workflow-executions/{execution_id}/status",
            self.report_status,
            methods=["POST"],
            response_model=WfExecStatusOut,
        )

    def report_status(self, req: Annotated[WfExecStatusReportReq, Depends()]) -> WfExecStatusOut:
        ctx = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id=req.execution_id, **req.body.model_dump()))
        FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx)
        self._check(ctx)
        ingest = ctx.resp.ingest
        return WfExecStatusOut(
            execution=AppWfExecLogOut.model_validate(ctx.resp.execution),
            ingest=MioIngestLogOut.model_validate(ingest) if ingest is not None else None,
        )

    @staticmethod
    def _check(ctx: WfExecStatusFacadeCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow execution not found")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "status change not allowed in the current state")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
