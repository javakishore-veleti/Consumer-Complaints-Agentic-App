"""Neutral Query AST → SparkSQL translator (M50-0001 / #338).

LCD leaf ops: EQ, NEQ, IN, NOT_IN. Combinators: AND, OR, NOT (max depth 3).
No LIKE/regex/joins — exact predicates only.
"""

from __future__ import annotations

from typing import Any, Mapping

ALLOWED_FIELDS = frozenset(
    {
        "primary_money_topic",
        "secondary_money_topic",
        "parent_org_id",
        "parent_org_name",
        "product",
        "state",
        "zip3",
        "is_fraud_scam",
        "is_money_transfer",
        "complaint_id",
    }
)
LEAF_OPS = frozenset({"EQ", "NEQ", "IN", "NOT_IN"})
BOOL_OPS = frozenset({"AND", "OR", "NOT"})
DEFAULT_TABLE = "demo.curated.cfpb_complaints_3m"
MAX_DEPTH = 3
K_ANON_MIN = 10


def _sql_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    s = str(value).replace("'", "''")
    return f"'{s}'"


def _leaf_sql(node: Mapping[str, Any]) -> str:
    op = str(node.get("op") or "").upper()
    field = str(node.get("field") or "").strip()
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"field not allowed in AST: {field!r}")
    if op not in LEAF_OPS:
        raise ValueError(f"leaf op not allowed: {op!r}")
    if op in {"EQ", "NEQ"}:
        lit = _sql_literal(node.get("value"))
        return f"{field} = {lit}" if op == "EQ" else f"{field} <> {lit}"
    values = node.get("values")
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{op} requires non-empty values list")
    joined = ", ".join(_sql_literal(v) for v in values)
    return f"{field} IN ({joined})" if op == "IN" else f"{field} NOT IN ({joined})"


def filter_tree_to_sql(node: Mapping[str, Any], *, depth: int = 0) -> str:
    if depth > MAX_DEPTH:
        raise ValueError(f"AST depth exceeds max {MAX_DEPTH}")
    op = str(node.get("op") or "").upper()
    if op in LEAF_OPS:
        return _leaf_sql(node)
    if op not in BOOL_OPS:
        raise ValueError(f"unknown AST op: {op!r}")
    args = node.get("args")
    if not isinstance(args, list) or not args:
        raise ValueError(f"{op} requires non-empty args")
    if op == "NOT":
        if len(args) != 1:
            raise ValueError("NOT requires exactly one arg")
        return f"NOT ({filter_tree_to_sql(args[0], depth=depth + 1)})"
    parts = [filter_tree_to_sql(a, depth=depth + 1) for a in args]
    joiner = f" {op} "
    return "(" + joiner.join(parts) + ")"


def ast_to_sql(envelope: Mapping[str, Any]) -> str:
    """Compile Query AST envelope to a COUNT(*) SparkSQL statement."""
    table = str(envelope.get("table") or DEFAULT_TABLE).strip() or DEFAULT_TABLE
    if not table.startswith("demo."):
        raise ValueError("table must be under demo.* for local gateway")
    tree = envelope.get("filter_tree")
    if not isinstance(tree, Mapping):
        raise ValueError("filter_tree is required")
    where = filter_tree_to_sql(tree)
    return f"SELECT COUNT(*) AS n FROM {table} WHERE {where}"


def assert_k_anonymous(count: int, *, min_n: int = K_ANON_MIN) -> None:
    if count < min_n:
        raise ValueError(f"k-anonymity violation: n={count} < {min_n}")
