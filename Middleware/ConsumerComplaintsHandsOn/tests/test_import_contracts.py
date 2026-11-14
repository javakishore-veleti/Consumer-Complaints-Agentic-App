"""The layer rules (.importlinter) run as part of the test suite, so a violation fails the build."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_import_contracts_are_kept():
    result = subprocess.run(
        [str(Path(sys.executable).parent / "lint-imports")], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
