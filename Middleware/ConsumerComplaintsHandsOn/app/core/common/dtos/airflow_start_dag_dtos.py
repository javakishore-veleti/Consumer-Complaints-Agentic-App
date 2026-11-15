from dataclasses import dataclass, field


@dataclass
class AirflowDagRunTriggerReq:
    dag_id: str
    execution_id: str


@dataclass
class AirflowDagRunTriggerResp:
    dag_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowDagRunTriggerCtx:
    req: AirflowDagRunTriggerReq
    resp: AirflowDagRunTriggerResp = field(default_factory=AirflowDagRunTriggerResp)


@dataclass
class AirflowStartDagReq:
    execution_id: str | None = None


@dataclass
class AirflowStartDagResp:
    engine_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowStartDagCtx:
    req: AirflowStartDagReq
    resp: AirflowStartDagResp = field(default_factory=AirflowStartDagResp)
