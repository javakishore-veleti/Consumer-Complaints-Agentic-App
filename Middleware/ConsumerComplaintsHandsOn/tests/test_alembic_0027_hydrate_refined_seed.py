"""M51-0002 / #342: alembic seed for hydrate_refined_iceberg_3m."""

from tests.conftest import REPO_ROOT

REV = (
    REPO_ROOT
    / "Middleware"
    / "ConsumerComplaintsHandsOn"
    / "alembic"
    / "versions"
    / "0027_seed_hydrate_refined_iceberg_3m_workflow.py"
)


def test_0027_seeds_refined_workflow():
    text = REV.read_text(encoding="utf-8")
    assert 'workflow_name="hydrate_refined_iceberg_3m"' in text
    assert "0026" in text
    assert "e5d00f51-f8af-5055-a153-23426590c86d" in text
