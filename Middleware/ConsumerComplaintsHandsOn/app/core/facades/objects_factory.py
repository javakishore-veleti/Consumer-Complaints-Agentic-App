"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.facades.airflow_start_dag_facade import AirflowStartDagFacade
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.start_wf_facade import StartWfFacade
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade
from app.core.facades.wf_list_facade import WfListFacade


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
            from app.core.facades.impl.af_start.airflow_start_dag_facade_impl import (
                AirflowStartDagFacadeImpl,
            )
            from app.core.facades.impl.airflow_upsert_secrets_facade_impl import (
                AirflowUpsertSecretsFacadeImpl,
            )
            from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl
            from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl
            from app.core.facades.impl.start_wf.start_wf_facade_impl import StartWfFacadeImpl
            from app.core.facades.impl.wf_list.wf_list_facade_impl import WfListFacadeImpl

            bean_registry.register(MioStatusFacade, MioStatusFacadeImpl())
            bean_registry.register(WfExecStatusFacade, WfExecStatusFacadeImpl())
            bean_registry.register(AirflowUpsertSecretsFacade, AirflowUpsertSecretsFacadeImpl())
            bean_registry.register(WfListFacade, WfListFacadeImpl())
            bean_registry.register(AirflowStartDagFacade, AirflowStartDagFacadeImpl())
            bean_registry.register(StartWfFacade, StartWfFacadeImpl())
            FacadesObjectsFactory._initialized = True

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

    @staticmethod
    def get_wf_list_facade() -> WfListFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(WfListFacade)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_start_dag_facade() -> AirflowStartDagFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(AirflowStartDagFacade)  # type: ignore[return-value]

    @staticmethod
    def get_start_wf_facade() -> StartWfFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(StartWfFacade)  # type: ignore[return-value]
