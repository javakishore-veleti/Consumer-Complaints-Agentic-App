"""Mongo unit of work: shared handle across DAO calls, or auto-commit per call (D39/D79)."""

from __future__ import annotations

import copy
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from pymongo.errors import DuplicateKeyError

from app.core.common.dtos.transaction_dtos import TransactionalCtx
from app.core.dao.impl.mongo.client import get_mongo_db
from app.core.dao.impl.mongo.docs import MongoDocument


@dataclass
class MongoFindReq:
    collection: str
    query: dict = field(default_factory=dict)
    sort: list | None = None
    skip: int = 0
    limit: int | None = None


@dataclass
class MongoWriteReq:
    collection: str
    doc: MongoDocument


@dataclass
class MongoUpdateReq:
    collection: str
    query: dict
    changes: dict


@dataclass
class MongoDeleteReq:
    collection: str
    doc_id: str


@dataclass
class MongoHandleConfig:
    db: object
    tracking: bool = False


class MongoTxnHandle:
    """Applies writes immediately; keeps before-images when tracking=True for rollback."""

    def __init__(self, config: MongoHandleConfig) -> None:
        self.db = config.db
        self.tracking = config.tracking
        self._lock = threading.RLock()
        self._before: list[tuple[str, str, MongoDocument | None]] = []

    def find_one(self, req: MongoFindReq) -> MongoDocument | None:
        with self._lock:
            found = self.db[req.collection].find_one(req.query)
            return MongoDocument(found) if found is not None else None

    def find(self, req: MongoFindReq) -> list[MongoDocument]:
        with self._lock:
            cursor = self.db[req.collection].find(req.query)
            if req.sort is not None:
                cursor = cursor.sort(req.sort)
            if req.skip:
                cursor = cursor.skip(req.skip)
            if req.limit is not None:
                cursor = cursor.limit(req.limit)
            return [MongoDocument(d) for d in cursor]

    def insert(self, req: MongoWriteReq) -> None:
        with self._lock:
            doc_id = req.doc["id"]
            if self.tracking:
                self._before.append((req.collection, doc_id, None))
            to_store = {**req.doc, "_id": doc_id}
            self.db[req.collection].insert_one(to_store)

    def replace(self, req: MongoWriteReq) -> None:
        with self._lock:
            doc_id = req.doc["id"]
            if self.tracking:
                old = self.db[req.collection].find_one({"id": doc_id})
                self._before.append(
                    (req.collection, doc_id, MongoDocument(copy.deepcopy(old)) if old else None)
                )
            to_store = {**req.doc, "_id": doc_id}
            self.db[req.collection].replace_one({"id": doc_id}, to_store, upsert=False)

    def update_matching(self, req: MongoUpdateReq) -> int:
        with self._lock:
            existing = self.db[req.collection].find_one(req.query)
            if existing is None:
                return 0
            if self.tracking:
                self._before.append((req.collection, existing["id"], MongoDocument(copy.deepcopy(existing))))
            new_doc = {**existing, **req.changes}
            new_doc["_id"] = new_doc["id"]
            result = self.db[req.collection].replace_one(
                {"_id": existing["_id"], **{k: req.query[k] for k in req.query}},
                new_doc,
            )
            return int(result.modified_count)

    def delete(self, req: MongoDeleteReq) -> MongoDocument | None:
        with self._lock:
            old = self.db[req.collection].find_one({"id": req.doc_id})
            if old is None:
                return None
            if self.tracking:
                self._before.append((req.collection, req.doc_id, MongoDocument(copy.deepcopy(old))))
            self.db[req.collection].delete_one({"id": req.doc_id})
            return MongoDocument(old)

    def rollback(self) -> None:
        with self._lock:
            for collection, doc_id, old in reversed(self._before):
                if old is None:
                    self.db[collection].delete_one({"id": doc_id})
                else:
                    restored = {**old, "_id": old.get("id", doc_id)}
                    self.db[collection].replace_one({"id": doc_id}, restored, upsert=True)
            self._before.clear()

    def commit(self) -> None:
        with self._lock:
            self._before.clear()


@contextmanager
def mongo_unit_of_work(ctx: TransactionalCtx) -> Iterator[MongoTxnHandle]:
    shared = ctx.transaction.handle if ctx.transaction is not None else None
    if isinstance(shared, MongoTxnHandle):
        yield shared
        return
    handle = MongoTxnHandle(MongoHandleConfig(db=get_mongo_db(), tracking=False))
    yield handle


def is_duplicate_key(exc: BaseException) -> bool:
    return isinstance(exc, DuplicateKeyError)
