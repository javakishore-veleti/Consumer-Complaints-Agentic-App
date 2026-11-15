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

Dev server defaults to http://localhost:4200/.

## API proxy

`proxy.conf.json` forwards `/api` to the Middleware at `http://127.0.0.1:8000` (path rewrite strips `/api`). App code uses `environment.apiBaseUrl` (`'/api'` in development). This scaffold does not call the API yet.
