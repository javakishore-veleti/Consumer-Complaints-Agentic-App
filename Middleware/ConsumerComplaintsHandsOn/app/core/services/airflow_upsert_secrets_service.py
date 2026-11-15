from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowUpsertSecretsCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsService(metaclass=SingletonMeta):
    @abstractmethod
    def upsert(self, ctx: AirflowUpsertSecretsCtx) -> int:
        """Read Airflow_Variables_Upsert.txt, copy each name from the environment into Airflow Variables.
        SUCCESS when every name is created or updated; FAILURE when any is missing or Airflow fails.
        resp.results never includes values."""
