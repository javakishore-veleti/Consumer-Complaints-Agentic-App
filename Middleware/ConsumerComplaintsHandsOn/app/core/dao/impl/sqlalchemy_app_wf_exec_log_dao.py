"""AppWfExecLogDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord
from app.core.common.return_codes import FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.impl.models import AppWfExecLogModel, AppWfModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(row: AppWfExecLogModel) -> AppWfExecLogRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    times = {name: getattr(row, name) for name in ("requested_at", "started_at", "finished_at")}
    times = {
        name: value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
        for name, value in times.items()
    }
    return AppWfExecLogRecord(
        id=row.id,
        workflow_id=row.workflow_id,
        workflow_name=row.workflow_name,
        engine_type=row.engine_type,
        engine_workflow_id=row.engine_workflow_id,
        config_used=row.config_used,
        engine_run_id=row.engine_run_id,
        status=row.status,
        message=row.message,
        **times,
    )


def _new_row(workflow: AppWfModel) -> AppWfExecLogModel:
    """A requested execution that keeps the workflow's details as they are now (D56)."""
    return AppWfExecLogModel(
        id=str(uuid4()),
        workflow_id=workflow.id,
        workflow_name=workflow.workflow_name,
        engine_type=workflow.engine_type,
        engine_workflow_id=workflow.engine_workflow_id,
        config_used=deepcopy(workflow.config),  # a copy, so a later edit of the workflow cannot reach this row
        status=ExecStatus.REQUESTED.value,
        requested_at=_now(),
    )


class SqlAlchemyAppWfExecLogDao(AppWfExecLogDao):
    def create(self, ctx: AppWfExecLogCtx) -> int:
        if not ctx.req.workflow_id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                workflow = session.get(AppWfModel, ctx.req.workflow_id)
                if workflow is None:
                    return NOT_FOUND
                row = _new_row(workflow)
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log create failed")
            return FAILURE

    def get(self, ctx: AppWfExecLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfExecLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log get failed")
            return FAILURE
