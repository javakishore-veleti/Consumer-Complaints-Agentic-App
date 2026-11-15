"""The shared-secret check of the endpoints Airflow calls (D59). A singleton, like every class in api.

It is a FastAPI dependency. The API objects factory attaches it to a whole router when it includes the router, never
to single endpoints:

    app.include_router(SomeCallbackApi().router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())])

The secret is read from the settings on every call (so tests can change it) and is never logged or returned. With no
secret configured every call is refused: a missing setting never leaves an endpoint open.
"""

import hmac
import logging

from fastapi import HTTPException, Request, status

from app.core.common.config import get_settings
from app.core.common.singleton import SingletonMeta

CALLBACK_SECRET_HEADER = "X-Callback-Secret"

log = logging.getLogger(__name__)


class CallbackSecretAuth(metaclass=SingletonMeta):
    def __call__(self, request: Request) -> None:
        expected = get_settings().callback_secret
        if expected is None:
            log.warning("callback refused: CCA_CALLBACK_SECRET is not set, so every callback is refused")
            raise self._unauthorized()
        given = request.headers.get(CALLBACK_SECRET_HEADER, "")
        # Constant time, on bytes (compare_digest rejects str with non-ASCII characters). Starlette decodes the header
        # bytes as latin-1, so both sides are encoded as latin-1; a configured secret that latin-1 cannot encode can
        # never match (fail closed, no exception).
        try:
            expected_bytes = expected.encode("latin-1")
        except UnicodeEncodeError:
            expected_bytes = None
        if expected_bytes is None or not hmac.compare_digest(given.encode("latin-1"), expected_bytes):
            log.warning("callback refused: missing or wrong %s header", CALLBACK_SECRET_HEADER)
            raise self._unauthorized()

    @staticmethod
    def _unauthorized() -> HTTPException:
        return HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "missing or wrong callback secret",
            headers={"WWW-Authenticate": CALLBACK_SECRET_HEADER},
        )
