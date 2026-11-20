"""Append-only invocation chronicle helpers for exec-log JSON columns (M57-0001 / #398).

Append to the list only when optional JSON payload is present (non-null). Null inputs → no append.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone

INVOCATIONS_KEY = "invocations"
MAX_INVOCATIONS = 100
EMPTY_CHRONICLE: dict = {INVOCATIONS_KEY: []}


@dataclass
class WfInvocationBuildReq:
    """One object for D37 / ctx-only signatures."""

    invoked_for: str
    invoked_configs: dict | None = None
    invoked_info: dict | None = None


@dataclass
class WfInvocationAppendReq:
    """Merge a built element into an existing chronicle document."""

    chronicle: dict | None
    element: dict


def build_invocation_if_payload(req: WfInvocationBuildReq) -> dict | None:
    """Return an invocation element, or None when both JSON fields are null (do not append)."""
    if req.invoked_configs is None and req.invoked_info is None:
        return None
    element: dict = {
        "invoked_for": req.invoked_for,
        "invoked_at": datetime.now(timezone.utc).isoformat(),
    }
    if req.invoked_configs is not None:
        element["invoked_configs"] = deepcopy(req.invoked_configs)
    if req.invoked_info is not None:
        element["invoked_info"] = deepcopy(req.invoked_info)
    return element


def append_invocation(req: WfInvocationAppendReq) -> dict:
    """Return a new chronicle with element appended (capped)."""
    base = deepcopy(req.chronicle) if isinstance(req.chronicle, dict) else {INVOCATIONS_KEY: []}
    invocations = base.get(INVOCATIONS_KEY)
    if not isinstance(invocations, list):
        invocations = []
    invocations = list(invocations) + [deepcopy(req.element)]
    if len(invocations) > MAX_INVOCATIONS:
        invocations = invocations[-MAX_INVOCATIONS:]
    base[INVOCATIONS_KEY] = invocations
    return base
