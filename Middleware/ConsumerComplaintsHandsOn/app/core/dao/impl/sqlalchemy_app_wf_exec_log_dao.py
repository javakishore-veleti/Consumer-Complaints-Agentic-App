"""AppWfExecLogDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy import update as sql_update

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.impl.models import AppWfExecLogModel, AppWfModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

RUN_ID_MAX = 128


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

    def update(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if req.engine_run_id is not None and len(req.engine_run_id) > RUN_ID_MAX:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfExecLogModel, req.id)
                if row is None:
                    return NOT_FOUND
                current = ExecStatus(row.status)
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT
                notes = {}  # engine_run_id and message: informational, so they may change on any row
                if req.engine_run_id is not None:
                    notes["engine_run_id"] = req.engine_run_id
                if req.message is not None:
                    notes["message"] = req.message
                if changes_status:
                    changes = {**notes, "status": target.value}
                    if target == ExecStatus.STARTED:
                        changes["started_at"] = _now()
                    elif target.is_final:
                        changes["finished_at"] = _now()
                    # The write only matches while the row still has the status read above, so when two callbacks
                    # race the second one finds no row to change instead of overwriting the first (D30).
                    moved = session.execute(
                        sql_update(AppWfExecLogModel)
                        .where(AppWfExecLogModel.id == req.id, AppWfExecLogModel.status == current.value)
                        .values(**changes)
                    ).rowcount
                    session.refresh(row)
                    if not moved:
                        if row.status != target.value:
                            return CONFLICT  # a rival moved the row somewhere else first; nothing was changed
                        # A rival made the same move first (a retry): keep its status and times, add only the notes.
                        for name, value in notes.items():
                            setattr(row, name, value)
                else:
                    for name, value in notes.items():
                        setattr(row, name, value)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log update failed")
            return FAILURE

    def list(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if (req.limit is not None and req.limit < 0) or (req.offset is not None and req.offset < 0):
            return INVALID_INPUT  # SQLite would return every row, Postgres would fail: reject on both
        try:
            query = select(AppWfExecLogModel)
            if req.workflow_id:
                query = query.where(AppWfExecLogModel.workflow_id == req.workflow_id)
            if req.status:
                query = query.where(AppWfExecLogModel.status == req.status)
            if req.engine_type:
                query = query.where(AppWfExecLogModel.engine_type == req.engine_type)
            query = query.order_by(AppWfExecLogModel.requested_at.desc(), AppWfExecLogModel.id)
            if req.limit is not None:
                query = query.limit(req.limit)
            if req.offset:
                query = query.offset(req.offset)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log list failed")
            return FAILURE
