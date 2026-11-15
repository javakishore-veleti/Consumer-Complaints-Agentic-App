"""Unit tests for Middleware/Airflow-dags/ccaa/status_callback.py (D67)."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import status_callback as sc  # noqa: E402


def test_resolve_api_base_url_prefers_env():
    assert (
        sc.resolve_api_base_url(
            getenv=lambda k, default=None: "http://from-env:8000" if k == "CCA_API_URL" else default,
            get_variable=lambda k: "http://from-var:8000",
        )
        == "http://from-env:8000"
    )


def test_resolve_api_base_url_falls_back_to_variable():
    assert (
        sc.resolve_api_base_url(
            getenv=lambda k, default=None: default,
            get_variable=lambda k: "http://host.docker.internal:8000" if k == "CCA_API_URL" else "",
        )
        == "http://host.docker.internal:8000"
    )


def test_resolve_callback_secret_requires_value():
    with pytest.raises(ValueError, match="CCA_CALLBACK_SECRET"):
        sc.resolve_callback_secret(
            getenv=lambda k, default=None: "" if k == "CCA_CALLBACK_SECRET" else default,
            get_variable=lambda k: "",
        )


def _fake_urlopen(status: int, body: bytes = b"{}"):
    def opener(req, timeout=None):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return body

            def getcode(self):
                return status

        if status >= 400:
            raise urllib.error.HTTPError(
                req.full_url if hasattr(req, "full_url") else "http://x",
                status,
                "err",
                hdrs=None,
                fp=io.BytesIO(body),
            )
        return Resp()

    return opener


def test_report_execution_status_posts_started():
    captured = {}

    def opener(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["secret"] = req.headers.get("X-callback-secret") or req.headers.get("X-Callback-Secret")
        captured["body"] = json.loads(req.data.decode("utf-8"))
        class Resp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b"{}"
            def getcode(self):
                return 200
        return Resp()

    sc.report_execution_status(
        "exec-1",
        "started",
        engine_run_id="manual__2026-01-01",
        api_base_url="http://host.docker.internal:8000/",
        callback_secret="s3cret",
        urlopen=opener,
    )
    assert captured["url"] == (
        "http://host.docker.internal:8000/callbacks/workflow-executions/exec-1/status"
    )
    assert captured["method"] == "POST"
    assert captured["secret"] == "s3cret"
    assert captured["body"] == {"status": "started", "engine_run_id": "manual__2026-01-01"}


def test_report_treats_409_as_success():
    sc.report_execution_status(
        "exec-1",
        "completed",
        api_base_url="http://api",
        callback_secret="s",
        urlopen=_fake_urlopen(409),
    )


def test_report_raises_on_401():
    with pytest.raises(sc.CallbackHttpError) as ei:
        sc.report_execution_status(
            "exec-1",
            "failed",
            message="boom",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=_fake_urlopen(401),
        )
    assert ei.value.status_code == 401
    assert "s" not in str(ei.value)
    assert "s" not in repr(ei.value)


def test_report_raises_on_500_and_connection_error():
    with pytest.raises(sc.CallbackHttpError):
        sc.report_execution_status(
            "exec-1",
            "failed",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=_fake_urlopen(500),
        )

    def boom(req, timeout=None):
        raise urllib.error.URLError("down")

    with pytest.raises(urllib.error.URLError):
        sc.report_execution_status(
            "exec-1",
            "failed",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=boom,
        )


def test_report_rejects_blank_secret_before_http():
    called = False

    def opener(req, timeout=None):
        nonlocal called
        called = True
        raise AssertionError("must not call")

    with pytest.raises(ValueError, match="CCA_CALLBACK_SECRET"):
        sc.report_execution_status(
            "exec-1",
            "started",
            api_base_url="http://api",
            callback_secret="  ",
            urlopen=opener,
        )
    assert called is False
