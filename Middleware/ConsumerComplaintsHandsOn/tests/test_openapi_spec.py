import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _exporter():
    spec = importlib.util.spec_from_file_location("export_openapi", ROOT / "scripts" / "export_openapi.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_openapi_spec_is_up_to_date():
    exporter = _exporter()
    assert exporter.SPEC_FILE.exists(), "openapi.json is missing: run `npm run local:api:openapi`"
    assert exporter.SPEC_FILE.read_text() == exporter.render(), (
        "openapi.json is out of date: run `npm run local:api:openapi` and commit the result"
    )
