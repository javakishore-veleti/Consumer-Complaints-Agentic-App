"""The layer rules from ARCHITECTURE.md, checked by reading the source (a stand-in for import-linter)."""

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
IMPORT = re.compile(r"^\s*(?:from|import)\s+(app\.[\w.]+)", re.MULTILINE)


def _imports(path: Path) -> set[str]:
    return set(IMPORT.findall(path.read_text()))


def test_nobody_imports_another_packages_impl():
    for path in APP.rglob("*.py"):
        own_impl = "/impl/" in path.as_posix()
        for target in _imports(path):
            if ".impl" in target and "objects_factory" not in path.name:
                # impl modules may import their own package's impl siblings
                package = path.as_posix().split("/impl/")[0].split("/app/")[-1].replace("/", ".")
                assert own_impl and target.startswith(f"app.{package}.impl"), f"{path} imports {target}"


def test_api_only_depends_on_facades_and_common():
    for path in (APP / "api").rglob("*.py"):
        for target in _imports(path):
            assert not target.startswith(("app.core.dao", "app.core.services")), f"{path} imports {target}"
