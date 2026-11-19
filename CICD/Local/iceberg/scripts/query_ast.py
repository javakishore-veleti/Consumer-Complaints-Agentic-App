"""Shim for prove scripts — canonical module lives in Middleware app.core.common.query_ast."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[4] / "Middleware" / "ConsumerComplaintsHandsOn"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from app.core.common.query_ast import (  # noqa: E402
    ALLOWED_FIELDS,
    BOOL_OPS,
    DEFAULT_TABLE,
    K_ANON_MIN,
    LEAF_OPS,
    MAX_DEPTH,
    AstToSqlReq,
    FilterTreeReq,
    KAnonReq,
    assert_k_anonymous,
    ast_to_sql,
    filter_tree_to_sql,
)

__all__ = [
    "ALLOWED_FIELDS",
    "BOOL_OPS",
    "DEFAULT_TABLE",
    "K_ANON_MIN",
    "LEAF_OPS",
    "MAX_DEPTH",
    "AstToSqlReq",
    "FilterTreeReq",
    "KAnonReq",
    "assert_k_anonymous",
    "ast_to_sql",
    "filter_tree_to_sql",
]
