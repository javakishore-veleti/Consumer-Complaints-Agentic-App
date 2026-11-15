#!/usr/bin/env bash
# Start / stop / status for every app under Portals/.
# Today: consumer-complaints-admin (ng serve on :4200). Add more portals here later.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ADMIN_DIR="$ROOT/Portals/consumer-complaints-admin"
ADMIN_PORT="${CCA_ADMIN_PORTAL_PORT:-4200}"

cca_try_nvm_use() {
  # Non-interactive shells (npm run) often keep nvm's default (20). Honor .nvmrc.
  local nvmrc="$ROOT/.nvmrc"
  [ -f "$nvmrc" ] || nvmrc="$ADMIN_DIR/.nvmrc"
  [ -f "$nvmrc" ] || return 0
  # shellcheck disable=SC1090,SC1091
  if [ -z "${NVM_DIR:-}" ] && [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
  fi
  if [ -n "${NVM_DIR:-}" ] && [ -s "$NVM_DIR/nvm.sh" ]; then
    # nvm is a shell function; sourcing is required in this bash process
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
    echo "portals:all — Node.js 22+ required (Angular admin). Current: ${ver:-not found}" >&2
    echo "  From the repo root:" >&2
    echo "    nvm use            # reads .nvmrc (22)" >&2
    echo "    npm run local:portals:all:start" >&2
    exit 1
  fi
}

cca_npm_install_admin() {
  # Always install so pulls (e.g. Tailwind / D80) never leave node_modules stale.
  echo "portals:all — npm install in Portals/consumer-complaints-admin"
  npm --prefix "$ADMIN_DIR" install
}

cmd="${1:-}"
case "$cmd" in
  start)
    cca_require_node_22
    cca_npm_install_admin
    # Foreground: first (only) portal. When a second portal exists, background
    # earlier ones and leave the last in the foreground, or use a process manager.
    echo "portals:all — starting consumer-complaints-admin on :$ADMIN_PORT (node $(node -v))"
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
