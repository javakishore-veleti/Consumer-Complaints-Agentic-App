"""M51-0001 / #341: alembic seed for hydrate_raw_iceberg_3m."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import REPO_ROOT

REV = (
    REPO_ROOT
    / "Middleware"
    / "ConsumerComplaintsHandsOn"
    / "alembic"
    / "versions"
    / "0026_seed_hydrate_raw_iceberg_3m_workflow.py"
)


def test_0026_seeds_hydrate_raw_workflow_and_3m_bind():
    text = REV.read_text(encoding="utf-8")
    assert 'workflow_name="hydrate_raw_iceberg_3m"' in text
    assert 'engine_workflow_id="hydrate_raw_iceberg_3m"' in text
    assert "a10fbfe0-ac03-5f3f-8d20-5132d470b03a" in text  # 3m MIO
    assert "e73565a9-73dc-542e-b45d-18c9b6de39cf" in text
    assert "down_revision" in text and "0025" in text
