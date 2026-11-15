"""DatasetLocationDao on MongoDB (D79)."""

import logging
from dataclasses import dataclass
import re
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import DatasetLocationType
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationRecord, DatasetLocationReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_location_dao import DatasetLocationDao
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
COLL = "datasets_location"
DATASETS = "datasets"
LINKS = "mios_datasets"
PATH_MAX = 1000
ENV_VAR_PREFIX = "LOCAL_DATA_PATH_"
CREDENTIALS_PATTERN = re.compile(r"[A-Za-z0-9_.\-]{1,100}")


@dataclass
class SamePlaceReq:
    uow: object
    merged: DatasetLocationReq
    exclude_id: str | None = None




def _to_record(doc: MongoDocument) -> DatasetLocationRecord:
    return DatasetLocationRecord(
        id=doc["id"],
        dataset_id=doc["dataset_id"],
        location_type=doc["location_type"],
        path=doc.get("path"),
        local_env_var_name=doc.get("local_env_var_name"),
        credentials_ref=doc.get("credentials_ref"),
        description=doc.get("description"),
        created_at=(doc["created_at"].replace(tzinfo=timezone.utc) if doc["created_at"].tzinfo is None else doc["created_at"]),
        updated_at=(doc["updated_at"].replace(tzinfo=timezone.utc) if doc["updated_at"].tzinfo is None else doc["updated_at"]),
    )


def _has_invalid_field(req: DatasetLocationReq) -> bool:
    if req.location_type is not None and req.location_type not in DatasetLocationType.values():
        return True
    if req.path is not None and (
        not isinstance(req.path, str) or not req.path.strip() or len(req.path.strip()) > PATH_MAX
    ):
        return True
    if req.local_env_var_name is not None and (
        not isinstance(req.local_env_var_name, str) or not req.local_env_var_name
    ):
        return True
    if req.path is not None and req.local_env_var_name is not None:
        return True
    if req.credentials_ref is not None and (
        not isinstance(req.credentials_ref, str) or CREDENTIALS_PATTERN.fullmatch(req.credentials_ref) is None
    ):
        return True
    return False


def _result_is_invalid(merged: DatasetLocationReq) -> bool:
    if (merged.path is None) == (merged.local_env_var_name is None):
        return True
    return merged.local_env_var_name is not None and merged.location_type != DatasetLocationType.LOCAL


def _same_place(req: SamePlaceReq) -> bool:
    merged = req.merged
    uow = req.uow
    if merged.path is not None:
        query = {
            "dataset_id": merged.dataset_id,
            "location_type": merged.location_type,
            "path": merged.path,
        }
    else:
        query = {
            "dataset_id": merged.dataset_id,
            "local_env_var_name": merged.local_env_var_name,
        }
    for doc in uow.find(MongoFindReq(collection=COLL, query=query)):
        if req.exclude_id is None or doc["id"] != req.exclude_id:
            return True
    return False




class MongoDatasetLocationDao(DatasetLocationDao):
    def create(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not (req.dataset_id and req.location_type) or _has_invalid_field(req):
            return INVALID_INPUT
        merged = DatasetLocationReq(
            dataset_id=req.dataset_id,
            location_type=req.location_type,
            path=None if req.path is None else req.path.strip(),
            local_env_var_name=req.local_env_var_name,
            credentials_ref=req.credentials_ref,
        )
        if _result_is_invalid(merged):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                dataset = uow.find_one(MongoFindReq(collection=DATASETS, query={"id": req.dataset_id}))
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset["code"]:
                    return INVALID_INPUT
                if _same_place(SamePlaceReq(uow=uow, merged=merged)):
                    return CONFLICT
                now = datetime.now(timezone.utc)
                doc = {
                    "id": str(uuid4()),
                    "dataset_id": merged.dataset_id,
                    "location_type": merged.location_type,
                    "path": merged.path,
                    "local_env_var_name": merged.local_env_var_name,
                    "credentials_ref": merged.credentials_ref,
                    "description": req.description,
                    "created_at": now,
                    "updated_at": now,
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo datasets_location create failed")
            return FAILURE

    def get(self, ctx: DatasetLocationCtx) -> int:
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
            log.exception("mongo datasets_location get failed")
            return FAILURE

    def list(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        try:
            query: dict = {}
            if req.dataset_id is not None:
                query["dataset_id"] = req.dataset_id
            if req.location_type is not None:
                query["location_type"] = req.location_type
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query))
                docs.sort(
                    key=lambda d: (
                        d["location_type"],
                        d.get("path") is None,
                        d.get("path") or "",
                        d["id"],
                    )
                )
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo datasets_location list failed")
            return FAILURE

    def update(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                if req.dataset_id is not None and req.dataset_id != doc["dataset_id"]:
                    return INVALID_INPUT
                if req.path is not None:
                    path, env_var_name = req.path.strip(), None
                elif req.local_env_var_name is not None:
                    path, env_var_name = None, req.local_env_var_name
                else:
                    path, env_var_name = doc.get("path"), doc.get("local_env_var_name")
                merged = DatasetLocationReq(
                    dataset_id=doc["dataset_id"],
                    location_type=req.location_type if req.location_type is not None else doc["location_type"],
                    path=path,
                    local_env_var_name=env_var_name,
                    credentials_ref=req.credentials_ref
                    if req.credentials_ref is not None
                    else doc.get("credentials_ref"),
                )
                if _result_is_invalid(merged):
                    return INVALID_INPUT
                dataset = uow.find_one(MongoFindReq(collection=DATASETS, query={"id": doc["dataset_id"]}))
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset["code"]:
                    return INVALID_INPUT
                if _same_place(SamePlaceReq(uow=uow, merged=merged, exclude_id=doc["id"])):
                    return CONFLICT
                doc["location_type"] = merged.location_type
                doc["path"] = merged.path
                doc["local_env_var_name"] = merged.local_env_var_name
                doc["credentials_ref"] = merged.credentials_ref
                if req.description is not None:
                    doc["description"] = req.description
                doc["updated_at"] = datetime.now(timezone.utc)
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo datasets_location update failed")
            return FAILURE

    def delete(self, ctx: DatasetLocationCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": ctx.req.id}))
                if doc is None:
                    return NOT_FOUND
                if uow.find_one(MongoFindReq(collection=LINKS, query={"dataset_location_id": doc["id"]})) is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(MongoDocument(doc))]
                uow.delete(MongoDeleteReq(collection=COLL, doc_id=ctx.req.id))
            return SUCCESS
        except Exception:
            log.exception("mongo datasets_location delete failed")
            return FAILURE
