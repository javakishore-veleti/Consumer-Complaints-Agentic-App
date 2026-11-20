"""AppWfExecLogDao on MongoDB (D79)."""

import logging
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord, AppWfExecLogReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.wf_invocation_chronicle import EMPTY_CHRONICLE, WfInvocationAppendReq, append_invocation
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoUpdateReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)

log = logging.getLogger(__name__)
COLL = "app_workflows_exec_log"
WF = "app_workflows"
INGEST = "mios_ingest_log"
RUN_ID_MAX = 128


def _now() -> datetime:
    return datetime.now(timezone.utc)




def _to_record(doc: MongoDocument) -> AppWfExecLogRecord:
    return AppWfExecLogRecord(
        id=doc["id"],
        workflow_id=doc["workflow_id"],
        workflow_name=doc["workflow_name"],
        engine_type=doc["engine_type"],
        engine_workflow_id=doc["engine_workflow_id"],
        config_used=doc.get("config_used"),
        engine_run_id=doc.get("engine_run_id"),
        status=doc["status"],
        message=doc.get("message"),
        mios_ingest_log_id=doc.get("mios_ingest_log_id"),
        requested_at=(doc["requested_at"].replace(tzinfo=timezone.utc) if doc["requested_at"].tzinfo is None else doc["requested_at"]),
        started_at=(None if doc.get("started_at") is None else (doc["started_at"].replace(tzinfo=timezone.utc) if doc["started_at"].tzinfo is None else doc["started_at"])),
        finished_at=(None if doc.get("finished_at") is None else (doc["finished_at"].replace(tzinfo=timezone.utc) if doc["finished_at"].tzinfo is None else doc["finished_at"])),
        wf_engine_data_json=doc.get("wf_engine_data_json"),
        wf_exec_data_json=doc.get("wf_exec_data_json"),
    )


def _has_invalid_notes(req: AppWfExecLogReq) -> bool:
    run_id = req.engine_run_id
    if run_id is not None and (not isinstance(run_id, str) or len(run_id) > RUN_ID_MAX):
        return True
    return req.message is not None and not isinstance(req.message, str)


def _has_invalid_paging(req: AppWfExecLogReq) -> bool:
    for number in (req.limit, req.offset):
        if number is not None and (isinstance(number, bool) or not isinstance(number, int) or number < 0):
            return True
    return False


class MongoAppWfExecLogDao(AppWfExecLogDao):
    def create(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if not req.workflow_id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                workflow = uow.find_one(MongoFindReq(collection=WF, query={"id": req.workflow_id}))
                if workflow is None:
                    return NOT_FOUND
                ingest_id = req.mios_ingest_log_id
                if ingest_id is not None and uow.find_one(MongoFindReq(collection=INGEST, query={"id": ingest_id})) is None:
                    return NOT_FOUND
                doc = {
                    "id": str(uuid4()),
                    "workflow_id": workflow["id"],
                    "workflow_name": workflow["workflow_name"],
                    "engine_type": workflow["engine_type"],
                    "engine_workflow_id": workflow["engine_workflow_id"],
                    "config_used": deepcopy(workflow.get("config")),
                    "engine_run_id": None,
                    "status": ExecStatus.REQUESTED.value,
                    "message": None,
                    "requested_at": _now(),
                    "started_at": None,
                    "finished_at": None,
                    "mios_ingest_log_id": ingest_id,
                    "wf_engine_data_json": deepcopy(EMPTY_CHRONICLE),
                    "wf_exec_data_json": deepcopy(EMPTY_CHRONICLE),
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows_exec_log create failed")
            return FAILURE

    def get(self, ctx: AppWfExecLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": ctx.req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows_exec_log get failed")
            return FAILURE

    def update(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if _has_invalid_notes(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                current = ExecStatus(doc["status"])
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT
                notes = {}
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
                    moved = uow.update_matching(MongoUpdateReq(collection=COLL, query={"id": req.id, "status": current.value}, changes=changes))
                    doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                    if not moved:
                        if doc is None:
                            return NOT_FOUND
                        if doc["status"] != target.value:
                            return CONFLICT
                        for name, value in notes.items():
                            doc[name] = value
                        uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                else:
                    for name, value in notes.items():
                        doc[name] = value
                if req.append_engine_invocation is not None:
                    doc["wf_engine_data_json"] = append_invocation(
                        WfInvocationAppendReq(
                            chronicle=doc.get("wf_engine_data_json"),
                            element=req.append_engine_invocation,
                        )
                    )
                if req.append_exec_invocation is not None:
                    doc["wf_exec_data_json"] = append_invocation(
                        WfInvocationAppendReq(
                            chronicle=doc.get("wf_exec_data_json"),
                            element=req.append_exec_invocation,
                        )
                    )
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id})))]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows_exec_log update failed")
            return FAILURE

    def list(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if _has_invalid_paging(req):
            return INVALID_INPUT
        try:
            query: dict = {}
            if req.workflow_id:
                query["workflow_id"] = req.workflow_id
            if req.status:
                query["status"] = req.status
            if req.engine_type:
                query["engine_type"] = req.engine_type
            if req.mios_ingest_log_id:
                query["mios_ingest_log_id"] = req.mios_ingest_log_id
            if req.engine_run_id is not None:
                query["engine_run_id"] = req.engine_run_id
            prefixes: list[str] = []
            if req.workflow_name_prefixes:
                prefixes.extend(req.workflow_name_prefixes)
            if req.workflow_name_prefix:
                prefixes.append(req.workflow_name_prefix)
            and_clauses: list[dict] = []
            if prefixes:
                and_clauses.append(
                    {"$or": [{"workflow_name": {"$regex": f"^{p}"}} for p in prefixes]}
                )
            if req.workflow_name_exclude_prefix:
                and_clauses.append(
                    {"workflow_name": {"$not": {"$regex": f"^{req.workflow_name_exclude_prefix}"}}}
                )
            if req.requested_after is not None or req.requested_before is not None:
                bounds: dict = {}
                if req.requested_after is not None:
                    bounds["$gte"] = req.requested_after
                if req.requested_before is not None:
                    bounds["$lte"] = req.requested_before
                and_clauses.append({"requested_at": bounds})
            if and_clauses:
                existing = [{k: v} for k, v in query.items()]
                query = {"$and": existing + and_clauses} if existing else {"$and": and_clauses}
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query, sort=[("requested_at", -1), ("id", 1)], skip=req.offset or 0, limit=req.limit,
                ))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows_exec_log list failed")
            return FAILURE
