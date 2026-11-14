"""Write the one OpenAPI specification of the project to openapi.json (code-first: FastAPI generates it).

    uv run python scripts/export_openapi.py          # or: npm run local:api:openapi

The committed file is checked by tests/test_openapi_spec.py, so it cannot go stale.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.api.objects_factory import ApiObjectsFactory  # noqa: E402

SPEC_FILE = PROJECT_ROOT / "openapi.json"


def render() -> str:
    return json.dumps(ApiObjectsFactory.get_app().openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    SPEC_FILE.write_text(render())
    print(f"wrote {SPEC_FILE}")
