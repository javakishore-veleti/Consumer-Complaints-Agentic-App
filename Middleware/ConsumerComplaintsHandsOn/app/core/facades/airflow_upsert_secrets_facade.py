from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsFacade(metaclass=SingletonMeta):
    @abstractmethod
    def upsert(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        """Copies listed env names into Airflow Variables. Codes match AirflowUpsertSecretsService.upsert."""
