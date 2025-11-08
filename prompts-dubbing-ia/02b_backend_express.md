# Backend Gateway Prompt (ExpressJS Option)

## Objective
Implement an optional **ExpressJS** gateway that fronts the FastAPI API for teams that are JS-first.

## Responsibilities
- Auth, rate limiting, request shaping.
- Multipart uploads (chunked) to S3/MinIO.
- Proxy `/jobs` and `/assets` to FastAPI.
- SSE or long-poll for progress updates.

## Routes
- `POST /api/upload/init`
- `POST /api/upload/complete`
- `POST /api/jobs/translate`
- `GET /api/jobs/:id`
- `GET /api/assets/:id`
- `GET /api/assets/:id/hls/master.m3u8`

## Implementation
- Use `multer` or direct signed URLs for large files.
- Central error handler with problem+json.
- Config via `.env` (links to FastAPI, MinIO, Redis).

## Deliverables
- `express-gw/src/index.ts`
- Basic supertest suite.
