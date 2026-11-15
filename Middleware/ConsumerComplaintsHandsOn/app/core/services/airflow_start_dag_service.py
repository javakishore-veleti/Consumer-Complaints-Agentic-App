from abc import abstractmethod

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx
from app.core.common.singleton import SingletonMeta


class AirflowStartDagService(metaclass=SingletonMeta):
    @abstractmethod
    def start(self, ctx: AirflowStartDagCtx) -> int:
        """Load execution, trigger Airflow DAG run, store engine_run_id; status stays requested."""
