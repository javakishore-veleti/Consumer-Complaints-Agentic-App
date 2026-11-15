"""pymongo client/database for the operational/admin store (D79)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.common.config import get_settings

_client = None
_db = None
_override_db = None


@dataclass
class MongoDbOverride:
    """Pass to set_mongo_db_override; db=None clears the override."""

    db: object | None


def get_mongo_db():
    """Return the operational Mongo database. Tests may call set_mongo_db_override."""
    global _client, _db
    if _override_db is not None:
        return _override_db
    if _db is None:
        from pymongo import MongoClient

        settings = get_settings()
        url = settings.mongo_operational_url
        if not url:
            raise RuntimeError("CCA_MONGO_OPERATIONAL_URL is not set")
        _client = MongoClient(url)
        path = (urlparse(url).path or "").lstrip("/")
        db_name = path.split("?", 1)[0] or "cca_operational"
        _db = _client[db_name]
    return _db


def set_mongo_db_override(req: MongoDbOverride) -> None:
    """Inject a database (mongomock) for tests. Pass MongoDbOverride(db=None) to clear."""
    global _override_db, _client, _db
    _override_db = req.db
    if req.db is None:
        reset_mongo_client()


def reset_mongo_client() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
