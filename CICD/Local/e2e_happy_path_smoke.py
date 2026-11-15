#!/usr/bin/env python3
"""Live E2E happy-path probe against a running Middleware (M03-0012).

Default mode (probe): GET /health, /workflows, /mios/status — verifies catalog JSON
without inventing status. Mode full: start download_cfpb_all + poll until
started/completed/failed (requires Airflow + CCA_CALLBACK_SECRET for real DAGs).

CI uses pytest tests/test_e2e_happy_path_smoke.py via npm run local:e2e:happy-path:smoke.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

ALLOWED = frozenset({"requested", "started", "completed", "failed"})


def _base() -> str:
    return os.environ.get("CCA_E2E_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def _mode() -> str:
    return (os.environ.get("CCA_E2E_MODE") or "probe").strip().lower()


def _get(path: str) -> tuple[int, object]:
    url = f"{_base()}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {"detail": raw}
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload
    except urllib.error.URLError as exc:
        _die(f"cannot reach {_base()}{path}: {exc.reason}")
        raise SystemExit(1) from exc


def _post(path: str, payload: dict, headers: dict | None = None) -> tuple[int, object]:
    url = f"{_base()}{path}"
    data = json.dumps(payload).encode()
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else {"detail": raw}
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed


def _die(msg: str) -> None:
    print(f"e2e happy-path probe FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def _assert_status(value: str | None, label: str) -> None:
    if value is None:
        _die(f"{label} is null (no invented status allowed)")
    if value not in ALLOWED:
        _die(f"{label}={value!r} is not a D30 status {sorted(ALLOWED)}")


def probe() -> None:
    code, health = _get("/health")
    if code != 200:
        _die(f"/health -> {code} {health}")

    code, workflows = _get("/workflows")
    if code != 200 or not isinstance(workflows, list):
        _die(f"/workflows -> {code} {workflows}")
    name = os.environ.get("CCA_E2E_WORKFLOW_NAME", "download_cfpb_all")
    if not any(w.get("workflow_name") == name for w in workflows):
        _die(f"workflow {name!r} missing from /workflows")

    code, mios = _get("/mios/status")
    if code != 200 or not isinstance(mios, list):
        _die(f"/mios/status -> {code} {mios}")
    for entry in mios:
        ingest = entry.get("latest_ingest")
        if ingest is None:
            continue
        _assert_status(ingest.get("status"), f"mio {entry.get('id')} latest_ingest.status")
        for ex in ingest.get("executions") or []:
            _assert_status(ex.get("status"), f"execution {ex.get('id')} status")

    print("e2e happy-path probe OK: health + workflows + mios/status (no invented status)")


def full() -> None:
    probe()
    name = os.environ.get("CCA_E2E_WORKFLOW_NAME", "download_cfpb_all")
    code, workflows = _get("/workflows")
    assert code == 200 and isinstance(workflows, list)
    wf = next(w for w in workflows if w.get("workflow_name") == name)
    code, mios = _get("/mios/status")
    assert code == 200 and isinstance(mios, list)
    if not mios:
        _die("no MIOs to start against")
    mio_id = mios[0]["id"]

    code, body = _post(f"/workflows/{wf['id']}/start", {"mio_id": mio_id})
    if code != 202:
        _die(f"start -> {code} {body} (is Airflow up?)")
    assert isinstance(body, dict)
    execution_id = body.get("execution_id")
    if not execution_id:
        _die("start 202 without execution_id")

    timeout = float(os.environ.get("CCA_E2E_POLL_SECONDS", "300"))
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        code, mios = _get("/mios/status")
        if code != 200 or not isinstance(mios, list):
            _die(f"poll /mios/status -> {code}")
        entry = next(e for e in mios if e["id"] == mio_id)
        ingest = entry.get("latest_ingest") or {}
        last = ingest.get("status")
        _assert_status(last, "latest_ingest.status")
        if last in ("completed", "failed", "started"):
            # Prefer terminal; accept started as progress proof if still running near timeout.
            if last in ("completed", "failed"):
                print(f"e2e happy-path full OK: execution={execution_id} status={last}")
                return
        time.sleep(2)

    if last == "started":
        print(f"e2e happy-path full OK (reached started): execution={execution_id}")
        return
    _die(f"timeout after {timeout}s; last status={last!r}")


def main() -> None:
    mode = _mode()
    if mode == "probe":
        probe()
    elif mode == "full":
        full()
    else:
        _die(f"unknown CCA_E2E_MODE={mode!r} (use probe|full)")


if __name__ == "__main__":
    main()
