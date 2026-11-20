"""M55-0005: hydrate_raw must not DELETE a missing Iceberg table."""

from tests.conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "hydrate_raw_3m.py"


def test_hydrate_raw_uses_create_or_replace_not_bare_delete():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "createOrReplace()" in text
    assert "CREATE NAMESPACE IF NOT EXISTS demo.raw" in text
    assert "DELETE FROM {args.target_table}" not in text
