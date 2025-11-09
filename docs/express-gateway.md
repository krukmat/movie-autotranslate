# Express Gateway (Optional)

Located in `express-gw/`, this service fronts the FastAPI backend for teams that prefer Node/Express tooling.

## Features
- Proxies `/upload`, `/jobs`, `/assets` routes to the backend and forwards API keys automatically (`BACKEND_API_KEY`).
- Applies per-IP rate limiting (`GATEWAY_RATE_LIMIT_PER_MINUTE`) and exposes an SSE endpoint (`/api/jobs/:id/events`) for job progress.
- Written in TypeScript with Jest/Supertest tests.

## Usage
```bash
cd express-gw
npm install
npm run dev
```

Environment variables:
- `BACKEND_BASE_URL` (default `http://localhost:8000/v1`)
- `BACKEND_API_KEY` (required if the API enforces keys)
- `API_KEY_HEADER` (defaults `X-API-Key`)
- `PORT` (default `4000`)

Deploy the gateway alongside the backend when a JS-first interface or additional request shaping is needed.
