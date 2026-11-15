from dataclasses import dataclass, field

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx, AirflowStartDagReq


@dataclass
class AirflowStartDagFacadeResp:
    engine_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowStartDagFacadeCtx:
    req: AirflowStartDagReq
    resp: AirflowStartDagFacadeResp = field(default_factory=AirflowStartDagFacadeResp)
    start_ctx: AirflowStartDagCtx | None = None
