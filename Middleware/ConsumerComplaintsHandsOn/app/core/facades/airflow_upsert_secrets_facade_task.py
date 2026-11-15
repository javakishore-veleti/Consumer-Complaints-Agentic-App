from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ...
