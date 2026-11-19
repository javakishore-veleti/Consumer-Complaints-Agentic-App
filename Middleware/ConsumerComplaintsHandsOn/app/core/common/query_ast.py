"""Neutral Query AST → SparkSQL translator (M50-0001 / #338; Middleware home M52-0001 / #352).

LCD leaf ops: EQ, NEQ, IN, NOT_IN. Combinators: AND, OR, NOT (max depth 3).
No LIKE/regex/joins — exact predicates only.
"""

from __future__ import annotations

from typing import Any, Mapping, NamedTuple

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


class SqlLiteralReq(NamedTuple):
    value: Any


class LeafSqlReq(NamedTuple):
    node: Mapping[str, Any]


class FilterTreeReq(NamedTuple):
    node: Mapping[str, Any]
    depth: int = 0


class AstToSqlReq(NamedTuple):
    envelope: Mapping[str, Any]


class KAnonReq(NamedTuple):
    count: int
    min_n: int = K_ANON_MIN


def _sql_literal(req: SqlLiteralReq) -> str:
    value = req.value
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    s = str(value).replace("'", "''")
    return f"'{s}'"


def _leaf_sql(req: LeafSqlReq) -> str:
    node = req.node
    op = str(node.get("op") or "").upper()
    field = str(node.get("field") or "").strip()
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"field not allowed in AST: {field!r}")
    if op not in LEAF_OPS:
        raise ValueError(f"leaf op not allowed: {op!r}")
    if op in {"EQ", "NEQ"}:
        lit = _sql_literal(SqlLiteralReq(node.get("value")))
        return f"{field} = {lit}" if op == "EQ" else f"{field} <> {lit}"
    values = node.get("values")
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{op} requires non-empty values list")
    joined = ", ".join(_sql_literal(SqlLiteralReq(v)) for v in values)
    return f"{field} IN ({joined})" if op == "IN" else f"{field} NOT IN ({joined})"


def filter_tree_to_sql(req: FilterTreeReq) -> str:
    if req.depth > MAX_DEPTH:
        raise ValueError(f"AST depth exceeds max {MAX_DEPTH}")
    node = req.node
    op = str(node.get("op") or "").upper()
    if op in LEAF_OPS:
        return _leaf_sql(LeafSqlReq(node))
    if op not in BOOL_OPS:
        raise ValueError(f"unknown AST op: {op!r}")
    args = node.get("args")
    if not isinstance(args, list) or not args:
        raise ValueError(f"{op} requires non-empty args")
    if op == "NOT":
        if len(args) != 1:
            raise ValueError("NOT requires exactly one arg")
        return f"NOT ({filter_tree_to_sql(FilterTreeReq(args[0], req.depth + 1))})"
    parts = [filter_tree_to_sql(FilterTreeReq(a, req.depth + 1)) for a in args]
    joiner = f" {op} "
    return "(" + joiner.join(parts) + ")"


def ast_to_sql(req: AstToSqlReq) -> str:
    """Compile Query AST envelope to a COUNT(*) SparkSQL statement."""
    envelope = req.envelope
    table = str(envelope.get("table") or DEFAULT_TABLE).strip() or DEFAULT_TABLE
    if not table.startswith("demo."):
        raise ValueError("table must be under demo.* for local gateway")
    tree = envelope.get("filter_tree")
    if not isinstance(tree, Mapping):
        raise ValueError("filter_tree is required")
    where = filter_tree_to_sql(FilterTreeReq(tree))
    return f"SELECT COUNT(*) AS n FROM {table} WHERE {where}"


def assert_k_anonymous(req: KAnonReq) -> None:
    if req.count < req.min_n:
        raise ValueError(f"k-anonymity violation: n={req.count} < {req.min_n}")


# --- M54 zero-hit relaxation -------------------------------------------------

# Drop order: most specific geo/product first; keep Money Topic when possible.
_RELAX_DROP_FIELDS = ("zip3", "product", "state", "parent_org_id", "parent_org_name")


class RelaxAstReq(NamedTuple):
    envelope: Mapping[str, Any]


class RelaxStep(NamedTuple):
    step: str
    reason: str
    ast: dict[str, Any]
    sql: str


class _CopyAstReq(NamedTuple):
    envelope: Mapping[str, Any]


class _IterAndLeavesReq(NamedTuple):
    node: Mapping[str, Any]


class _DropFieldReq(NamedTuple):
    node: Mapping[str, Any]
    field: str


def _copy_ast(req: _CopyAstReq) -> dict[str, Any]:
    import copy

    return copy.deepcopy(dict(req.envelope))


def _iter_and_leaves(req: _IterAndLeavesReq) -> list[dict[str, Any]]:
    node = req.node
    op = str(node.get("op") or "").upper()
    if op in LEAF_OPS:
        return [dict(node)]
    if op == "AND":
        out: list[dict[str, Any]] = []
        for arg in node.get("args") or []:
            if isinstance(arg, Mapping):
                out.extend(_iter_and_leaves(_IterAndLeavesReq(arg)))
        return out
    return []


def _drop_field_from_and(req: _DropFieldReq) -> dict[str, Any] | None:
    """Return tree with EQ/IN leaves on `field` removed, or None if the leaf itself is dropped."""
    node = req.node
    field = req.field
    op = str(node.get("op") or "").upper()
    if op in LEAF_OPS:
        if str(node.get("field") or "") == field:
            return None
        return dict(node)
    if op != "AND":
        return dict(node)
    kept: list[Any] = []
    dropped = False
    for arg in node.get("args") or []:
        if not isinstance(arg, Mapping):
            continue
        child = _drop_field_from_and(_DropFieldReq(arg, field))
        if child is None:
            dropped = True
            continue
        kept.append(child)
    if not dropped:
        return dict(node)
    if not kept:
        return None
    if len(kept) == 1:
        return kept[0]
    return {"op": "AND", "args": kept}


def relax_ast(req: RelaxAstReq) -> list[RelaxStep]:
    """Produce ordered broaden steps (AST + SQL) without executing against a warehouse."""
    envelope = _copy_ast(_CopyAstReq(req.envelope))
    tree = envelope.get("filter_tree")
    if not isinstance(tree, Mapping):
        return []
    steps: list[RelaxStep] = []
    current = envelope
    for field in _RELAX_DROP_FIELDS:
        ft = current.get("filter_tree")
        if not isinstance(ft, Mapping):
            break
        leaves = _iter_and_leaves(_IterAndLeavesReq(ft))
        if not any(str(leaf.get("field") or "") == field for leaf in leaves):
            continue
        new_tree = _drop_field_from_and(_DropFieldReq(ft, field))
        if new_tree is None or new_tree == ft:
            continue
        nxt = _copy_ast(_CopyAstReq(current))
        nxt["filter_tree"] = new_tree
        sql = ast_to_sql(AstToSqlReq(nxt))
        steps.append(
            RelaxStep(
                step=f"drop_{field}",
                reason=f"Broaden by removing predicate on {field}",
                ast=nxt,
                sql=sql,
            )
        )
        current = nxt
    return steps
