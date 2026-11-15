"""The callback secret check on its own (D59): the setting, the comparison, failing closed, and no secret in the logs."""

import logging

import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import Headers

from app.api.objects_factory import ApiObjectsFactory
from app.api.security import callback_secret_auth
from app.api.security.callback_secret_auth import CALLBACK_SECRET_HEADER
from app.core.common.config import get_settings

SECRET = "s3cret-value-for-tests"


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


@pytest.fixture
def no_secret(monkeypatch):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)


@pytest.fixture
def auth_log(caplog, monkeypatch):
    """Alembic's fileConfig, run by the migrating fixtures of other tests, disables loggers that already exist."""
    logger = logging.getLogger(callback_secret_auth.__name__)
    monkeypatch.setattr(logger, "disabled", False)
    caplog.set_level(logging.WARNING, logger=logger.name)
    return caplog


def _request(headers: Headers) -> Request:
    return Request({"type": "http", "headers": headers.raw})


def _refused(request: Request) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        ApiObjectsFactory.get_callback_secret_auth()(request)
    return caught.value


def test_the_setting_is_read_trimmed_and_blank_means_not_configured(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "  abc  \n")
    assert get_settings().callback_secret == "abc"
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert get_settings().callback_secret is None
    monkeypatch.delenv("CCA_CALLBACK_SECRET")
    assert get_settings().callback_secret is None


def test_the_settings_repr_never_shows_the_secret(secret):
    assert secret not in repr(get_settings())


def test_the_right_secret_passes(secret):
    assert ApiObjectsFactory.get_callback_secret_auth()(_request(Headers({CALLBACK_SECRET_HEADER: secret}))) is None


def test_the_header_name_is_case_insensitive(secret):
    assert ApiObjectsFactory.get_callback_secret_auth()(_request(Headers({"x-callback-secret": secret}))) is None


def test_a_missing_header_is_401_with_a_challenge(secret):
    error = _refused(_request(Headers({})))
    assert error.status_code == 401
    assert error.detail == "missing or wrong callback secret"
    assert error.headers == {"WWW-Authenticate": "X-Callback-Secret"}


@pytest.mark.parametrize("given", ["wrong", "", SECRET + "x", SECRET[:-1], SECRET.upper(), "é" + SECRET])
def test_a_wrong_secret_is_401(secret, given):
    assert _refused(_request(Headers({CALLBACK_SECRET_HEADER: given}))).status_code == 401


def test_without_a_configured_secret_everything_is_refused(no_secret):
    for headers in (Headers({}), Headers({CALLBACK_SECRET_HEADER: ""}), Headers({CALLBACK_SECRET_HEADER: "anything"})):
        assert _refused(_request(headers)).status_code == 401


def test_a_blank_configured_secret_does_not_accept_an_empty_header(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert _refused(_request(Headers({CALLBACK_SECRET_HEADER: ""}))).status_code == 401


def test_the_secret_is_read_on_every_call(monkeypatch):
    request = _request(Headers({CALLBACK_SECRET_HEADER: "first"}))
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "first")
    assert ApiObjectsFactory.get_callback_secret_auth()(request) is None
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "second")
    assert _refused(request).status_code == 401


def test_refusals_are_logged_without_any_secret(secret, auth_log):
    _refused(_request(Headers({CALLBACK_SECRET_HEADER: "a-guess-from-a-caller"})))
    assert "missing or wrong X-Callback-Secret header" in auth_log.text
    assert secret not in auth_log.text
    assert "a-guess-from-a-caller" not in auth_log.text


def test_a_missing_setting_is_logged(no_secret, auth_log):
    _refused(_request(Headers({CALLBACK_SECRET_HEADER: "a-guess-from-a-caller"})))
    assert "CCA_CALLBACK_SECRET is not set" in auth_log.text
    assert "a-guess-from-a-caller" not in auth_log.text
