#!/usr/bin/env bash
# Start / stop / status for every app under Portals/.
# Admin (:4200) + Intellect (:4201).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ADMIN_DIR="$ROOT/Portals/consumer-complaints-admin"
INTELLECT_DIR="$ROOT/Portals/consumer-complaints-intellect"
ADMIN_PORT="${CCA_ADMIN_PORTAL_PORT:-4200}"
INTELLECT_PORT="${CCA_INTELLECT_PORTAL_PORT:-4201}"

cca_try_nvm_use() {
  local nvmrc="$ROOT/.nvmrc"
  [ -f "$nvmrc" ] || nvmrc="$ADMIN_DIR/.nvmrc"
  [ -f "$nvmrc" ] || return 0
  # shellcheck disable=SC1090,SC1091
  if [ -z "${NVM_DIR:-}" ] && [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
  fi
  if [ -n "${NVM_DIR:-}" ] && [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
    nvm use --silent "$(cat "$nvmrc" | tr -d '[:space:]')" >/dev/null 2>&1 || nvm use "$(cat "$nvmrc" | tr -d '[:space:]')"
  fi
}

cca_require_node_22() {
  local ver major
  cca_try_nvm_use
  ver="$(node -v 2>/dev/null || true)"
  major="${ver#v}"
  major="${major%%.*}"
  if [[ -z "$major" || "$major" -lt 22 ]]; then
    echo "portals:all — Node.js 22+ required. Current: ${ver:-not found}" >&2
    exit 1
  fi
}

cca_npm_install() {
  echo "portals:all — npm install in Portals/consumer-complaints-admin"
  npm --prefix "$ADMIN_DIR" install
  echo "portals:all — npm install in Portals/consumer-complaints-intellect"
  npm --prefix "$INTELLECT_DIR" install
}

cca_stop_port() {
  local port="$1" label="$2"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      echo "portals:all — stopping $label on :$port ($pids)"
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
    else
      echo "portals:all — nothing listening on :$port ($label)"
    fi
  fi
}

cmd="${1:-}"
case "$cmd" in
  start)
    cca_require_node_22
    cca_npm_install
    echo "portals:all — starting intellect on :$INTELLECT_PORT (background)"
    npm --prefix "$INTELLECT_DIR" start &
    echo "portals:all — starting consumer-complaints-admin on :$ADMIN_PORT (node $(node -v))"
    exec npm --prefix "$ADMIN_DIR" start
    ;;
  stop)
    cca_stop_port "$ADMIN_PORT" "admin"
    cca_stop_port "$INTELLECT_PORT" "intellect"
    ;;
  status)
    echo "portals:all — expected: admin :$ADMIN_PORT, intellect :$INTELLECT_PORT"
    if command -v lsof >/dev/null 2>&1; then
      if lsof -tiTCP:"$ADMIN_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "  admin: listening on :$ADMIN_PORT"
      else
        echo "  admin: not listening on :$ADMIN_PORT"
      fi
      if lsof -tiTCP:"$INTELLECT_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "  intellect: listening on :$INTELLECT_PORT"
      else
        echo "  intellect: not listening on :$INTELLECT_PORT"
      fi
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}" >&2
    exit 2
    ;;
esac
