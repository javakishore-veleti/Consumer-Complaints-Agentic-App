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


def test_report_execution_status_includes_volume_fields():
    captured = {}

    def opener(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def getcode(self):
                return 200

        return Resp()

    sc.report_execution_status(
        "exec-1",
        "completed",
        rows_loaded=100,
        batch_count=2,
        increment_marker="batch-2",
        api_base_url="http://api",
        callback_secret="s",
        urlopen=opener,
    )
    assert captured["body"]["status"] == "completed"
    assert captured["body"]["rows_loaded"] == 100
    assert captured["body"]["batch_count"] == 2
    assert captured["body"]["increment_marker"] == "batch-2"


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


class _TI:
    def __init__(self, task_id, state):
        self.task_id = task_id
        self.state = state


class _DagRunAirflow3:
    """Airflow 3-shaped DagRun: get_task_instances only (no get_task_instance)."""

    def __init__(self, tis):
        self._tis = list(tis)

    def get_task_instances(self, state=None):
        return list(self._tis)


class _DagRunAirflow2:
    def __init__(self, by_id):
        self._by_id = dict(by_id)

    def get_task_instance(self, task_id):
        return self._by_id.get(task_id)


def test_task_instance_for_airflow3_get_task_instances():
    work = _TI("filter_csv", "success")
    other = _TI("notify_finished", "running")
    ctx = {"dag_run": _DagRunAirflow3([work, other])}
    found = sc.task_instance_for(ctx, "filter_csv")
    assert found is work
    assert sc.upstream_succeeded(ctx, "filter_csv") is True
    assert sc.upstream_succeeded(ctx, "missing") is False


def test_task_instance_for_airflow2_get_task_instance():
    work = _TI("download", "failed")
    ctx = {"dag_run": _DagRunAirflow2({"download": work})}
    assert sc.task_instance_for(ctx, "download") is work
    assert sc.upstream_succeeded(ctx, "download") is False


def test_task_instance_for_missing_dag_run_returns_none():
    assert sc.task_instance_for({}, "x") is None
    assert sc.upstream_succeeded({}, "x") is False


def test_notify_execution_finished_reports_completed_on_success():
    calls = []

    def fake_report(execution_id, status, **kwargs):
        calls.append((execution_id, status, kwargs))

    work = _TI("filter_csv", "success")
    ctx = {
        "dag_run": _DagRunAirflow3([work]),
        "run_id": "manual__1",
        "params": {"execution_id": "exec-ok"},
    }
    sc.notify_execution_finished(
        ctx,
        "filter_csv",
        report=fake_report,
        completed_kwargs={"batch_count": 3},
    )
    assert len(calls) == 1
    assert calls[0][0] == "exec-ok"
    assert calls[0][1] == "completed"
    assert calls[0][2].get("batch_count") == 3
    assert calls[0][2].get("engine_run_id") == "manual__1"


def test_notify_execution_finished_reports_failed_without_get_task_instance():
    """Regression: must not AttributeError on Airflow 3 DagRun."""
    calls = []

    def fake_report(execution_id, status, **kwargs):
        calls.append((execution_id, status, kwargs))

    work = _TI("filter_csv", "failed")
    ctx = {
        "dag_run": _DagRunAirflow3([work]),
        "run_id": "manual__2",
        "dag_run_conf": {"execution_id": "exec-fail"},
    }
    # Also put conf on dag_run like real Airflow
    ctx["dag_run"].conf = {"execution_id": "exec-fail"}
    sc.notify_execution_finished(ctx, "filter_csv", report=fake_report)
    assert len(calls) == 1
    assert calls[0][1] == "failed"
    assert "filter_csv" in (calls[0][2].get("message") or "")


def test_notify_execution_finished_failed_when_upstream_missing():
    calls = []

    def fake_report(execution_id, status, **kwargs):
        calls.append((execution_id, status, kwargs))

    ctx = {
        "dag_run": _DagRunAirflow3([]),
        "params": {"execution_id": "exec-miss"},
        "run_id": "r",
    }
    sc.notify_execution_finished(ctx, "filter_csv", report=fake_report)
    assert calls[0][1] == "failed"


class _CurrentTI:
    def __init__(self, xcom_by_task):
        self._xcom_by_task = dict(xcom_by_task)

    def xcom_pull(self, task_ids=None, key="return_value", default=None):
        return self._xcom_by_task.get(task_ids, default)


def test_upstream_succeeded_xcom_fallback_when_state_none():
    """Airflow 3: TI present with state=None but work XCom return exists → success."""
    work = _TI("resolve_and_filter", None)
    ctx = {
        "dag_run": _DagRunAirflow3([work]),
        "ti": _CurrentTI({"resolve_and_filter": "part1:10"}),
    }
    assert sc.upstream_succeeded(ctx, "resolve_and_filter") is True


def test_notify_finished_completed_via_xcom_when_state_none():
    calls = []

    def fake_report(execution_id, status, **kwargs):
        calls.append((execution_id, status, kwargs))

    work = _TI("resolve_and_filter", None)
    ctx = {
        "dag_run": _DagRunAirflow3([work]),
        "ti": _CurrentTI({"resolve_and_filter": "a.zip:1"}),
        "params": {"execution_id": "exec-xcom"},
        "run_id": "manual__x",
    }
    sc.notify_execution_finished(ctx, "resolve_and_filter", report=fake_report)
    assert calls[0][1] == "completed"


def test_notify_finished_failed_when_state_none_and_no_xcom():
    calls = []

    def fake_report(execution_id, status, **kwargs):
        calls.append((execution_id, status, kwargs))

    work = _TI("resolve_and_filter", None)
    ctx = {
        "dag_run": _DagRunAirflow3([work]),
        "ti": _CurrentTI({}),
        "params": {"execution_id": "exec-noxcom"},
        "run_id": "r",
    }
    sc.notify_execution_finished(ctx, "resolve_and_filter", report=fake_report)
    assert calls[0][1] == "failed"
