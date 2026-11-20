"""GET /workflow-logs — Admin chronicle over app_workflows_exec_log (M55-0012 / #394)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.workflow_logs_models import WorkflowLogListHttpReq, WorkflowLogOut
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.common.workflow_log_categories import (
    CATEGORY_FILTERS,
    DISPLAY_STATUS,
    ENGINE_TYPE_LABELS,
    WORKFLOW_LOG_CATEGORIES,
)
from app.core.facades.objects_factory import FacadesObjectsFactory


class WorkflowLogsApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/workflow-logs", tags=["workflow-logs"])
        self.router.add_api_route("", self.list, methods=["GET"], response_model=list[WorkflowLogOut])

    def list(self, req: Annotated[WorkflowLogListHttpReq, Depends()]) -> list[WorkflowLogOut]:
        dao_req = AppWfExecLogReq(
            status=req.status,
            engine_type=req.engine_type,
            engine_run_id=req.engine_run_id,
            requested_after=req.requested_after,
            requested_before=req.requested_before,
            limit=req.limit,
            offset=req.offset,
        )
        if req.category is not None:
            if req.category not in WORKFLOW_LOG_CATEGORIES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid category")
            filt = CATEGORY_FILTERS[req.category]
            dao_req.workflow_name_prefixes = list(filt.prefixes)
            dao_req.workflow_name_exclude_prefix = filt.exclude_prefix
        ctx = AppWfExecLogCtx(req=dao_req)
        code = FacadesObjectsFactory.get_workflow_logs_facade().list(ctx)
        if code == INVALID_INPUT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid list filters")
        if code != SUCCESS:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="list failed")
        return [
            WorkflowLogOut(
                id=r.id,
                workflow_id=r.workflow_id,
                workflow_name=r.workflow_name,
                engine_type=r.engine_type,
                engine_label=ENGINE_TYPE_LABELS.get(r.engine_type, r.engine_type),
                engine_workflow_id=r.engine_workflow_id,
                engine_run_id=r.engine_run_id,
                status=r.status,
                display_status=DISPLAY_STATUS.get(r.status, r.status),
                message=r.message,
                mios_ingest_log_id=r.mios_ingest_log_id,
                requested_at=r.requested_at,
                started_at=r.started_at,
                finished_at=r.finished_at,
            )
            for r in ctx.resp.records
        ]
