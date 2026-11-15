"""Ctx, Req and Resp of the workflow list service (DESIGN.md D66)."""

from dataclasses import dataclass, field

from app.core.common.return_codes import SUCCESS


@dataclass
class WfListEntry:
    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    enabled: bool


@dataclass
class WfListReq:
    """No filters for MVP (D54, D66)."""


@dataclass
class WfListResp:
    entries: list[WfListEntry] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class WfListCtx:
    req: WfListReq = field(default_factory=WfListReq)
    resp: WfListResp = field(default_factory=WfListResp)
