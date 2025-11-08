# Security & Access Controls

## API Keys
- Configure comma-separated API keys via `API_KEYS`. Each request must send the key in `X-API-Key` (override with `API_KEY_HEADER`).
- Requests without keys run as `anonymous`, but by default all routers require a valid key; set `API_KEYS=""` during local dev to disable auth.
- Per-key rate limiting is enforced in-process (`RATE_LIMIT_PER_MINUTE`, default 120). Adjust according to deployment scale.
- Jobs store the hashed requester ID, so only the owner can retry or cancel their jobs.

## Quotas & Limits
- `MAX_ACTIVE_JOBS_PER_KEY` caps concurrent (PENDING/RUNNING) jobs per API key.
- Uploads are constrained by `MAX_UPLOAD_SIZE` and per-part `UPLOAD_PART_SIZE`.
- Signed MinIO URLs now honor `UPLOAD_URL_EXPIRY` (default 3600s) and `DOWNLOAD_URL_EXPIRY` (default 900s) for stronger access control.

## Secrets & Deployment
- Store secrets in `.env` or your orchestrator’s secret manager; `.gitignore` prevents accidental commits.
- Rotate API keys periodically and propagate via secure channels; the hashed ID persisted in the DB prevents leaking the raw key.
- Combine API-level auth with perimeter security (e.g., API Gateway, IP allowlists) for defense in depth.
