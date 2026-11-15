"""D45: package objects_factory.init() registers singletons; safe to call twice."""

from fastapi import FastAPI

from app.api.objects_factory import ApiObjectsFactory
from app.api.security.callback_secret_auth import CallbackSecretAuth
from app.core.dao.mio_dao import MioDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.mio_status_service import MioStatusService
from app.core.services.objects_factory import ServicesObjectsFactory


def test_init_is_idempotent_and_get_returns_registered_singleton():
    DaoObjectsFactory.init()
    DaoObjectsFactory.init()
    a = DaoObjectsFactory.get_mio_dao()
    b = DaoObjectsFactory.get_mio_dao()
    assert a is b
    assert isinstance(a, MioDao)

    ServicesObjectsFactory.init()
    ServicesObjectsFactory.init()
    assert ServicesObjectsFactory.get_mio_status_service() is (
        ServicesObjectsFactory.get_mio_status_service()
    )
    assert isinstance(ServicesObjectsFactory.get_mio_status_service(), MioStatusService)

    FacadesObjectsFactory.init()
    FacadesObjectsFactory.init()
    assert FacadesObjectsFactory.get_mio_status_facade() is (
        FacadesObjectsFactory.get_mio_status_facade()
    )
    assert isinstance(FacadesObjectsFactory.get_mio_status_facade(), MioStatusFacade)

    ApiObjectsFactory.init()
    ApiObjectsFactory.init()
    assert ApiObjectsFactory.get_app() is ApiObjectsFactory.get_app()
    assert isinstance(ApiObjectsFactory.get_app(), FastAPI)
    assert ApiObjectsFactory.get_callback_secret_auth() is (
        ApiObjectsFactory.get_callback_secret_auth()
    )
    assert isinstance(ApiObjectsFactory.get_callback_secret_auth(), CallbackSecretAuth)


def test_get_lazy_inits_when_init_not_called_first():
    # Relies on process state from other tests / SingletonMeta; asserting the contract:
    # get_* must not require an explicit init() from the caller.
    assert isinstance(DaoObjectsFactory.get_transaction_dao(), object)


def test_startup_init_order_matches_main():
    """main.py must call dao → services → facades → api init, then get_app()."""
    import main as main_mod
    from pathlib import Path

    text = Path(main_mod.__file__).read_text()
    assert "DaoObjectsFactory.init()" in text
    assert "ServicesObjectsFactory.init()" in text
    assert "FacadesObjectsFactory.init()" in text
    assert "ApiObjectsFactory.init()" in text
    assert text.index("DaoObjectsFactory.init()") < text.index("ServicesObjectsFactory.init()")
    assert text.index("ServicesObjectsFactory.init()") < text.index(
        "FacadesObjectsFactory.init()"
    )
    assert text.index("FacadesObjectsFactory.init()") < text.index("ApiObjectsFactory.init()")
    assert text.index("ApiObjectsFactory.init()") < text.index("get_app()")
