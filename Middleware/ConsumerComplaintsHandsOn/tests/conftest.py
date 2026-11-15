import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory
from app.core.common.config import PROJECT_ROOT
from app.core.dao.impl.database import reset_engine

# Test temp folders live in the repository's git-ignored runtime_data/tmp, not the system /tmp.
REPO_ROOT = PROJECT_ROOT.parents[1]


def pytest_configure(config):
    if not config.option.basetemp:
        base = REPO_ROOT / "runtime_data" / "tmp" / "pytest"
        base.parent.mkdir(parents=True, exist_ok=True)  # git-ignored, so a fresh clone does not have it yet
        config.option.basetemp = base


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """A fresh, migrated operational database in a temporary folder."""
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    monkeypatch.delenv("CCA_OPERATIONAL_STORE", raising=False)
    monkeypatch.delenv("CCA_MONGO_OPERATIONAL_URL", raising=False)
    reset_engine()
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    yield tmp_path
    reset_engine()


@pytest.fixture
def client(data_dir):
    return TestClient(ApiObjectsFactory.get_app())
