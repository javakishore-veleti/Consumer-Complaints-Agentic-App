# consumer-complaints-admin

Angular **22** admin portal for Consumer Complaints (D65).

## Node

Requires Node `^22.22.3 || ^24.15.0 || >=26.0.0` (see `engines` in `package.json`). Example:

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22
```

## Install

```bash
npm install
```

Or from the repository root:

```bash
npm --prefix Portals/consumer-complaints-admin install
```

## Serve / build / test

From this directory:

```bash
npm start          # ng serve with proxy.conf.json
npm run build
npm test -- --watch=false
```

From the repository root:

```bash
npm run local:portal:admin:start
npm run local:portal:admin:build
npm run local:portal:admin:test
```

**One-command portal + API** (starts Middleware via `run_app.sh` if needed, then `ng serve`):

```bash
npm run local:portal:admin:with-api
```

Dev server defaults to http://localhost:4200/. Open **DataSets → Imports** (`/datasets/imports`) for live MIO list / start / refresh.

Full local E2E (Airflow callbacks → DB → refresh, SQLite first): `docs/local-admin-e2e-happy-path.md`. Automated smoke (no Airflow): from repo root `npm run local:e2e:happy-path:smoke`.

## API proxy

`proxy.conf.json` forwards `/api` to the Middleware at `http://127.0.0.1:8000` (path rewrite strips `/api`). App code uses `environment.apiBaseUrl` (`'/api'` in development). Imports calls `GET /mios/status`, `GET /workflows`, and `POST /workflows/{id}/start` through that proxy; HTTP failures show the Middleware FastAPI `detail` text (no invented ingest status).
