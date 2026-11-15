"""Builds the one FastAPI application for the whole project (one OpenAPI spec) and hands out the other singletons of
the api package (the callback secret check, D59; the status callback API, D60; the MIO status API, D61; and the
Airflow Variables upsert API, D42). The app is a singleton."""

import threading

from fastapi import Depends, FastAPI

from app.api.routers.airflow_upsert_secrets_api import AirflowUpsertSecretsApi
from app.api.routers.data_ingest_api import DataIngestApi
from app.api.routers.mio_status_api import MioStatusApi
from app.api.routers.wf_exec_callback_api import WfExecCallbackApi
from app.api.security.callback_secret_auth import CallbackSecretAuth
from app.core.common.bean_registry import bean_registry


class ApiObjectsFactory:
    _initialized = False
    _app: FastAPI | None = None
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if ApiObjectsFactory._initialized:
            return
        with ApiObjectsFactory._lock:
            if ApiObjectsFactory._initialized:
                return
            auth = CallbackSecretAuth()
            wf_api = WfExecCallbackApi()
            mio_api = MioStatusApi()
            upsert_api = AirflowUpsertSecretsApi()
            bean_registry.register(CallbackSecretAuth, auth)
            bean_registry.register(WfExecCallbackApi, wf_api)
            bean_registry.register(MioStatusApi, mio_api)
            bean_registry.register(AirflowUpsertSecretsApi, upsert_api)

            app = FastAPI(
                title="Consumer Complaints Hands-On API",
                version="0.1.0",
                description="Middleware API for the Consumer Complaints platform.",
            )
            app.include_router(DataIngestApi().router)
            # Portal endpoints stay open (no callback secret): the browser cannot keep a shared secret (D59, D61).
            app.include_router(mio_api.router)
            # Every router an engine calls is protected as a whole by the callback secret (D59).
            app.include_router(wf_api.router, dependencies=[Depends(auth)])
            app.include_router(upsert_api.router, dependencies=[Depends(auth)])

            @app.get("/health", tags=["health"])
            def health() -> dict[str, str]:
                return {"status": "ok"}

            bean_registry.register(FastAPI, app)
            ApiObjectsFactory._app = app
            ApiObjectsFactory._initialized = True

    @staticmethod
    def get_app() -> FastAPI:
        ApiObjectsFactory.init()
        return bean_registry.get_one(FastAPI)  # type: ignore[return-value]

    @staticmethod
    def get_callback_secret_auth() -> CallbackSecretAuth:
        ApiObjectsFactory.init()
        return bean_registry.get_one(CallbackSecretAuth)  # type: ignore[return-value]

    @staticmethod
    def get_wf_exec_callback_api() -> WfExecCallbackApi:
        ApiObjectsFactory.init()
        return bean_registry.get_one(WfExecCallbackApi)  # type: ignore[return-value]

    @staticmethod
    def get_mio_status_api() -> MioStatusApi:
        ApiObjectsFactory.init()
        return bean_registry.get_one(MioStatusApi)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_upsert_secrets_api() -> AirflowUpsertSecretsApi:
        ApiObjectsFactory.init()
        return bean_registry.get_one(AirflowUpsertSecretsApi)  # type: ignore[return-value]
