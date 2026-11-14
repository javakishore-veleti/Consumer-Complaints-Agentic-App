"""The signature rule (DESIGN.md, D37): a function or method takes nothing, or exactly one ctx / request / DTO object.
Never several loose arguments and never a bare primitive. Objects carry the values, so adding a field never changes a
signature. Only signatures that a library dictates are listed below, with the reason."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ["app", "alembic", "scripts", "main.py"]

# Signatures dictated by a library, so they cannot take a ctx.
LIBRARY_DICTATED = {
    "alembic/env.py:_include_name": "Alembic calls it with (name, type_, parent_names)",
    "app/core/dao/impl/database.py:_attach_schemas": "SQLAlchemy's connect event passes (dbapi_connection, record)",
    "app/core/common/singleton.py:__call__": "the metaclass call protocol passes the constructor arguments through",
}
BARE_TYPES = re.compile(r"\b(str|int|float|bool|bytes|datetime|date|dict|list|set|tuple|Path)\b")


def _functions():
    for entry in SCANNED:
        target = ROOT / entry
        for path in [target] if target.is_file() else sorted(target.rglob("*.py")):
            if ".venv" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield path.relative_to(ROOT).as_posix(), node


def _problem(node: ast.FunctionDef) -> str | None:
    args = node.args
    params = [a for a in args.posonlyargs + args.args + args.kwonlyargs if a.arg not in ("self", "cls")]
    if args.vararg or args.kwarg:
        return "takes *args or **kwargs"
    if len(params) > 1:
        return f"takes {len(params)} separate arguments ({', '.join(a.arg for a in params)})"
    if params:
        if params[0].annotation is None:
            return f"argument '{params[0].arg}' has no type, so it cannot be shown to be an object"
        if BARE_TYPES.search(ast.unparse(params[0].annotation)):
            return f"argument '{params[0].arg}' is a bare value ({ast.unparse(params[0].annotation)}), not an object"
    return None


def test_every_function_takes_nothing_or_one_object():
    problems = []
    for path, node in _functions():
        if f"{path}:{node.name}" in LIBRARY_DICTATED:
            continue
        reason = _problem(node)
        if reason:
            problems.append(f"{path}:{node.lineno} {node.name}() {reason}")
    assert not problems, "\n".join(problems)


def test_the_library_dictated_list_has_no_stale_entries():
    present = {f"{path}:{node.name}" for path, node in _functions()}
    assert set(LIBRARY_DICTATED) <= present
