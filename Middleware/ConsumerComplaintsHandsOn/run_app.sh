#!/usr/bin/env bash
# Run the HandsOn Middleware API locally.
#
#   run_app.sh start    migrate the operational database, then start the API in the background
#   run_app.sh stop     stop it
#   run_app.sh status   is it running? (exit code 0 = running, 3 = not running)
#
# If the migration fails, the API is not started.
#
# Environment (all optional):
#   API_HOST (127.0.0.1)   API_PORT (8000)   API_RELOAD=1 (auto-reload on code changes)
#   CCA_DATA_DIR           folder for the SQLite files, the PID file and the log (default: ./.data)
#   CCA_DB_URL             use another database (for example Postgres) instead of SQLite
#   CCA_CALLBACK_SECRET    shared secret of the endpoints Airflow calls (D59); without it they answer 401
# Every name set in ./.env (git-ignored; the names are in .env.example) is exported first.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f ./.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"
DATA_DIR="${CCA_DATA_DIR:-$PWD/.data}"
PID_FILE="$DATA_DIR/api.pid"
LOG_FILE="$DATA_DIR/api.log"
URL="http://$HOST:$PORT"

mkdir -p "$DATA_DIR"
export CCA_DATA_DIR="$DATA_DIR"

pid_alive() { [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; }
healthy()   { curl -fsS --max-time 2 "$URL/health" >/dev/null 2>&1; }

cmd_start() {
  if pid_alive; then
    echo "API already running (pid $(cat "$PID_FILE")) at $URL"
    return 0
  fi
  rm -f "$PID_FILE"
  if healthy; then
    echo "Something else already answers at $URL. Stop it or set API_PORT." >&2
    return 1
  fi

  echo "Installing dependencies (uv sync)..."
  uv sync --quiet

  echo "Migrating the database (alembic upgrade head)..."
  .venv/bin/alembic upgrade head

  local reload=()
  [[ "${API_RELOAD:-0}" == "1" ]] && reload=(--reload)
  echo "Starting the API at $URL (log: $LOG_FILE)"
  nohup .venv/bin/python -m uvicorn main:app --host "$HOST" --port "$PORT" ${reload[@]+"${reload[@]}"} \
    >"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  disown

  for _ in $(seq 1 30); do
    if healthy; then
      echo "API is up: $URL  (Swagger: $URL/docs)"
      return 0
    fi
    if ! pid_alive; then break; fi
    sleep 0.5
  done
  echo "API did not become healthy. Last log lines:" >&2
  tail -n 20 "$LOG_FILE" >&2 || true
  cmd_stop >/dev/null || true
  return 1
}

cmd_stop() {
  if ! pid_alive; then
    rm -f "$PID_FILE"
    echo "API is not running"
    return 0
  fi
  local pid; pid="$(cat "$PID_FILE")"
  echo "Stopping the API (pid $pid)..."
  pkill -TERM -P "$pid" 2>/dev/null || true   # the reloader's child, if any
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    pkill -KILL -P "$pid" 2>/dev/null || true
    kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  echo "Stopped"
}

cmd_status() {
  if pid_alive; then
    if healthy; then
      echo "API running (pid $(cat "$PID_FILE")) and healthy at $URL"
    else
      echo "API process running (pid $(cat "$PID_FILE")) but $URL/health does not answer; see $LOG_FILE"
    fi
    return 0
  fi
  rm -f "$PID_FILE"
  echo "API not running"
  return 3
}

case "${1:-}" in
  start)  cmd_start ;;
  stop)   cmd_stop ;;
  status) cmd_status ;;
  *) echo "usage: $0 {start|stop|status}" >&2; exit 2 ;;
esac
