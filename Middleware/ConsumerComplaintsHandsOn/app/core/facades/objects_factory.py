"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade


class FacadesObjectsFactory:
    _initialized = False
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if FacadesObjectsFactory._initialized:
            return
        with FacadesObjectsFactory._lock:
            if FacadesObjectsFactory._initialized:
                return
            from app.core.facades.impl.airflow_upsert_secrets_facade_impl import (
                AirflowUpsertSecretsFacadeImpl,
            )
            from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl
            from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl
            from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl

            bean_registry.register(DataIngestFacade, DataIngestFacadeImpl())
            bean_registry.register(MioStatusFacade, MioStatusFacadeImpl())
            bean_registry.register(WfExecStatusFacade, WfExecStatusFacadeImpl())
            bean_registry.register(AirflowUpsertSecretsFacade, AirflowUpsertSecretsFacadeImpl())
            FacadesObjectsFactory._initialized = True

    @staticmethod
    def get_data_ingest_facade() -> DataIngestFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(DataIngestFacade)  # type: ignore[return-value]

    @staticmethod
    def get_mio_status_facade() -> MioStatusFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(MioStatusFacade)  # type: ignore[return-value]

    @staticmethod
    def get_wf_exec_status_facade() -> WfExecStatusFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(WfExecStatusFacade)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_upsert_secrets_facade() -> AirflowUpsertSecretsFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(AirflowUpsertSecretsFacade)  # type: ignore[return-value]
