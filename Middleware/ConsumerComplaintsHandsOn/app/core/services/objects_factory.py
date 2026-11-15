"""The only module of the services package that may import from services/impl.

Static methods return the singleton, typed as the interface.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.services.airflow_start_dag_service import AirflowStartDagService
from app.core.services.airflow_upsert_secrets_service import AirflowUpsertSecretsService
from app.core.services.app_endpoint_list_service import AppEndpointListService
from app.core.services.mio_status_service import MioStatusService
from app.core.services.start_wf_service import StartWfService
from app.core.services.wf_exec_status_service import WfExecStatusService
from app.core.services.wf_list_service import WfListService
from app.core.services.workflow_engine import WorkflowEngine


class ServicesObjectsFactory:
    _initialized = False
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if ServicesObjectsFactory._initialized:
            return
        with ServicesObjectsFactory._lock:
            if ServicesObjectsFactory._initialized:
                return
            from app.core.services.impl.airflow_start_dag_service_impl import (
                AirflowStartDagServiceImpl,
            )
            from app.core.services.impl.airflow_upsert_secrets_service_impl import (
                AirflowUpsertSecretsServiceImpl,
            )
            from app.core.services.impl.apache_airflow_workflow_engine_impl import (
                ApacheAirflowWorkflowEngineImpl,
            )
            from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl
            from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl
            from app.core.services.impl.start_wf_service_impl import StartWfServiceImpl
            from app.core.services.impl.app_endpoint_list_service_impl import (
                AppEndpointListServiceImpl,
            )
            from app.core.services.impl.wf_list_service_impl import WfListServiceImpl

            bean_registry.register(MioStatusService, MioStatusServiceImpl())
            bean_registry.register(WfExecStatusService, WfExecStatusServiceImpl())
            bean_registry.register(AirflowUpsertSecretsService, AirflowUpsertSecretsServiceImpl())
            bean_registry.register(WfListService, WfListServiceImpl())
            bean_registry.register(AppEndpointListService, AppEndpointListServiceImpl())
            bean_registry.register(AirflowStartDagService, AirflowStartDagServiceImpl())
            bean_registry.register(WorkflowEngine, ApacheAirflowWorkflowEngineImpl())
            bean_registry.register(StartWfService, StartWfServiceImpl())
            ServicesObjectsFactory._initialized = True

    @staticmethod
    def get_mio_status_service() -> MioStatusService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(MioStatusService)  # type: ignore[return-value]

    @staticmethod
    def get_wf_exec_status_service() -> WfExecStatusService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(WfExecStatusService)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_upsert_secrets_service() -> AirflowUpsertSecretsService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(AirflowUpsertSecretsService)  # type: ignore[return-value]

    @staticmethod
    def get_wf_list_service() -> WfListService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(WfListService)  # type: ignore[return-value]

    @staticmethod
    def get_app_endpoint_list_service() -> AppEndpointListService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(AppEndpointListService)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_start_dag_service() -> AirflowStartDagService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(AirflowStartDagService)  # type: ignore[return-value]

    @staticmethod
    def get_start_wf_service() -> StartWfService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(StartWfService)  # type: ignore[return-value]

    @staticmethod
    def get_workflow_engines() -> list[WorkflowEngine]:
        ServicesObjectsFactory.init()
        return bean_registry.get_all(WorkflowEngine)  # type: ignore[return-value]
