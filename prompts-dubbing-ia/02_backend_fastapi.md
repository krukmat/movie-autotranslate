# Backend API Prompt (FastAPI)

## Objective
Implement a FastAPI service that exposes:
- Presigned upload initiation + completion.
- Job creation and status endpoints.
- Asset metadata CRUD.
- Public asset serving (proxy) or signed URLs.

## Endpoints (Design & Implement)
- `POST /v1/upload/init`: returns `{assetId, uploadUrl(s), partSize}`
- `POST /v1/upload/complete`: finalize multipart; persist `Asset` row
- `POST /v1/jobs/translate`: body `{ assetId, targetLangs: ["es"], presets: { default: "female_bright" } }` → returns `{ jobId }`
- `GET /v1/jobs/{jobId}`: status/progress
- `GET /v1/assets/{assetId}`: metadata + available outputs
- `GET /v1/assets/{assetId}/hls/master.m3u8`: redirect or signed URL
- `GET /healthz`

## Implementation Notes
- Use **Pydantic** models; validate languages in `{en, es, fr, de}`.
- Use Redis for job enqueue; each stage as a named task.
- Persist minimal state in SQLite/Postgres (configurable).
- Enforce max upload size per env var.
- Return friendly errors with `problem+json` schema.

## Acceptance Criteria
- Creating a job enqueues `ASR` stage and returns jobId.
- Polling `/jobs/{id}` shows stage-by-stage progress.
- On success, `/assets/{id}` lists master HLS URL and tracks.

## Deliverables
- `backend/app/main.py` FastAPI app
- `backend/app/routes/*.py` for endpoints
- `backend/app/models.py`, `schemas.py`
- `backend/app/queue.py` (Redis/Celery)
- Tests with `pytest` + `httpx`.
