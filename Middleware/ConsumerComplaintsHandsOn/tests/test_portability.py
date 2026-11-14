"""Nothing machine- or person-specific may be committed: a teammate clones the repo anywhere, on any OS.
Paths come from pathlib (Path(__file__)) or `dirname "$0"`; owner and repository names are never typed in."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", ".data", "__pycache__", ".pytest_cache", ".git", "node_modules"}
TEXT_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".md", ".mako", ".importlinter"}

# Built from pieces so this file does not trip its own check.
FORBIDDEN = {
    "an absolute home directory": re.compile(r"/" + r"Users/\w+|/" + r"home/\w+|[A-Za-z]:\\" + r"Users\\"),
    "a hardcoded GitHub owner in a URL": re.compile(r"github\.com/(?!actions/|astral-sh/)[\w-]+/[\w.-]+"),
}


def _project_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts) and (
            path.suffix in TEXT_SUFFIXES or path.name in {".importlinter"}
        ):
            yield path


def test_no_machine_or_person_specific_values():
    problems = []
    for path in _project_files():
        if path == Path(__file__).resolve() or path.name == "uv.lock":
            continue
        text = path.read_text(errors="ignore")
        for what, pattern in FORBIDDEN.items():
            for match in pattern.finditer(text):
                problems.append(f"{path.relative_to(ROOT)}: {what}: {match.group(0)}")
    assert not problems, "\n".join(problems)
