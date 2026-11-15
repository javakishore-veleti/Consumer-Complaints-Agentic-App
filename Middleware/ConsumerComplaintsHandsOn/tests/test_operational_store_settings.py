"""D75: operational store profile resolution and validation (SQLite / Postgres / MongoDB)."""

import pytest

from app.core.common.config import get_settings
from app.core.dao.objects_factory import DaoObjectsFactory


def test_default_is_sqlite_when_store_and_url_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("CCA_OPERATIONAL_STORE", raising=False)
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    monkeypatch.delenv("CCA_MONGO_OPERATIONAL_URL", raising=False)
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    settings = get_settings()
    assert settings.operational_store == "sqlite"
    assert settings.db_url == f"sqlite:///{tmp_path.resolve()}/operational.sqlite"
    assert settings.mongo_operational_url is None


def test_postgres_inferred_from_cca_db_url(monkeypatch, tmp_path):
    monkeypatch.delenv("CCA_OPERATIONAL_STORE", raising=False)
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CCA_DB_URL", "postgresql+psycopg://u:p@localhost:5432/cca")
    settings = get_settings()
    assert settings.operational_store == "postgres"
    assert settings.db_url.startswith("postgresql")


def test_explicit_sqlite_store(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", " SQLite ")
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    assert get_settings().operational_store == "sqlite"


def test_explicit_postgres_requires_postgres_url(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "postgres")
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="CCA_DB_URL"):
        get_settings()


def test_mongodb_requires_mongo_operational_url(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "mongodb")
    monkeypatch.delenv("CCA_MONGO_OPERATIONAL_URL", raising=False)
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="CCA_MONGO_OPERATIONAL_URL"):
        get_settings()


def test_mongodb_profile_sets_store_and_url(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "mongodb")
    monkeypatch.setenv("CCA_MONGO_OPERATIONAL_URL", "mongodb://localhost:27017/cca_operational")
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    settings = get_settings()
    assert settings.operational_store == "mongodb"
    assert settings.mongo_operational_url == "mongodb://localhost:27017/cca_operational"


def test_invalid_operational_store_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "redis")
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="CCA_OPERATIONAL_STORE"):
        get_settings()


def test_dao_factory_registers_mongodb_daos(monkeypatch, tmp_path):
    import mongomock

    from app.core.dao.impl.mongo.client import MongoDbOverride, set_mongo_db_override
    from app.core.dao.impl.mongo.mongo_app_wf_dao import MongoAppWfDao

    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "mongodb")
    monkeypatch.setenv("CCA_MONGO_OPERATIONAL_URL", "mongodb://localhost:27017/cca_operational")
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    set_mongo_db_override(MongoDbOverride(db=mongomock.MongoClient().cca_operational))
    DaoObjectsFactory.reset()
    try:
        DaoObjectsFactory.init()
        assert isinstance(DaoObjectsFactory.get_app_wf_dao(), MongoAppWfDao)
    finally:
        DaoObjectsFactory.reset()
        set_mongo_db_override(MongoDbOverride(db=None))
