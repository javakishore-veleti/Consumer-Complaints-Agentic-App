from abc import abstractmethod

from app.core.common.dtos.airflow_start_dag_facade_dtos import AirflowStartDagFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowStartDagFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: AirflowStartDagFacadeCtx) -> int:
        ...
