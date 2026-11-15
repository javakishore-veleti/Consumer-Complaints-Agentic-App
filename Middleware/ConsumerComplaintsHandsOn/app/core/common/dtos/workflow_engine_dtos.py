"""Ctx, Req and Resp for starting a run in a workflow engine (DESIGN.md D73)."""

from dataclasses import dataclass, field


@dataclass
class WorkflowEngineReq:
    execution_id: str | None = None


@dataclass
class WorkflowEngineResp:
    engine_run_id: str | None = None
    code: int = 0


@dataclass
class WorkflowEngineCtx:
    req: WorkflowEngineReq = field(default_factory=WorkflowEngineReq)
    resp: WorkflowEngineResp = field(default_factory=WorkflowEngineResp)
