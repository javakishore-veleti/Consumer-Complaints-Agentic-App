from abc import abstractmethod

from app.core.common.dtos.airflow_start_dag_facade_dtos import AirflowStartDagFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowStartDagFacade(metaclass=SingletonMeta):
    @abstractmethod
    def start(self, ctx: AirflowStartDagFacadeCtx) -> int:
        """Trigger Airflow DAG for an execution; codes match AirflowStartDagService.start."""
