#!/usr/bin/env bash
# Start / stop / status for every app under Portals/.
# Today: consumer-complaints-admin (ng serve on :4200). Add more portals here later.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ADMIN_DIR="$ROOT/Portals/consumer-complaints-admin"
ADMIN_PORT="${CCA_ADMIN_PORTAL_PORT:-4200}"

cmd="${1:-}"
case "$cmd" in
  start)
    # Foreground: first (only) portal. When a second portal exists, background
    # earlier ones and leave the last in the foreground, or use a process manager.
    echo "portals:all — starting consumer-complaints-admin on :$ADMIN_PORT"
    exec npm --prefix "$ADMIN_DIR" start
    ;;
  stop)
    if command -v lsof >/dev/null 2>&1; then
      pids="$(lsof -tiTCP:"$ADMIN_PORT" -sTCP:LISTEN 2>/dev/null || true)"
      if [[ -n "$pids" ]]; then
        echo "portals:all — stopping listeners on :$ADMIN_PORT ($pids)"
        # shellcheck disable=SC2086
        kill $pids 2>/dev/null || true
      else
        echo "portals:all — nothing listening on :$ADMIN_PORT"
      fi
    else
      echo "portals:all — install lsof to stop by port, or Ctrl+C the ng serve process" >&2
      exit 1
    fi
    ;;
  status)
    echo "portals:all — expected: consumer-complaints-admin (http://localhost:$ADMIN_PORT)"
    if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"$ADMIN_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "  admin: listening on :$ADMIN_PORT"
    else
      echo "  admin: not listening on :$ADMIN_PORT"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}" >&2
    exit 2
    ;;
esac
