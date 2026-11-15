"""AirflowStartDagFacade: one task calls the service (D64 af_start)."""

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagReq
from app.core.common.dtos.airflow_start_dag_facade_dtos import (
    AirflowStartDagFacadeCtx,
    AirflowStartDagFacadeResp,
)
from app.core.common.return_codes import INVALID_INPUT
from app.core.facades.objects_factory import FacadesObjectsFactory


def test_blank_execution_id_stops_at_invalid():
    ctx = AirflowStartDagFacadeCtx(
        req=AirflowStartDagReq(execution_id=""),
        resp=AirflowStartDagFacadeResp(),
    )
    assert FacadesObjectsFactory.get_airflow_start_dag_facade().start(ctx) == INVALID_INPUT
    assert ctx.resp.code == INVALID_INPUT
