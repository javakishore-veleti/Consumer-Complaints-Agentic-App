"""The only module of the services package that may import from services/impl.

Static methods return the singleton, typed as the interface.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.services.airflow_upsert_secrets_service import AirflowUpsertSecretsService
from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.mio_status_service import MioStatusService
from app.core.services.wf_exec_status_service import WfExecStatusService
from app.core.services.wf_list_service import WfListService


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
            from app.core.services.impl.airflow_upsert_secrets_service_impl import (
                AirflowUpsertSecretsServiceImpl,
            )
            from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl
            from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl
            from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl
            from app.core.services.impl.wf_list_service_impl import WfListServiceImpl

            bean_registry.register(DatasetStatusService, DatasetStatusServiceImpl())
            bean_registry.register(MioStatusService, MioStatusServiceImpl())
            bean_registry.register(WfExecStatusService, WfExecStatusServiceImpl())
            bean_registry.register(AirflowUpsertSecretsService, AirflowUpsertSecretsServiceImpl())
            bean_registry.register(WfListService, WfListServiceImpl())
            ServicesObjectsFactory._initialized = True

    @staticmethod
    def get_dataset_status_service() -> DatasetStatusService:
        ServicesObjectsFactory.init()
        return bean_registry.get_one(DatasetStatusService)  # type: ignore[return-value]

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
