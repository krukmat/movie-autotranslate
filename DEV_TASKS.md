# Development Task Plan

The following backlog items are scoped for engineering work (non-manual). Each block lists the goal, key subtasks, owners/interfaces, and acceptance criteria so they can be tracked in project tooling.

## 1. Observability & Structured Logging
- **Goal:** Provide actionable telemetry across API/worker stages.
- **Implementation:**
  - Introduce a logging helper (`workers/common/logging.py`) that emits JSON logs with `jobId`, `assetId`, `stage`, `event`.
  - Instrument `workers/pipeline/tasks.py` to log start/end of every stage, including durations.
  - Extend `/metrics` to export stage-level counters and histograms (processing time, failures) via Prometheus.
  - Update `backend/app/services/jobs.py` to persist `logsKey` pointing to MinIO for per-job log archives.
- **Acceptance:** Tail logs show structured entries; `/metrics` exposes per-stage stats validated by Prometheus lint; Job detail API returns `logsKey` for frontend use.

## 2. Stage-Oriented Pipeline & Resume Support
- **Goal:** Split the monolithic worker task into restartable stages and honor `resumeFrom`.
- **Implementation:**
  - Create discrete Celery tasks (`run_asr`, `run_mt`, `run_tts`, `run_mix`), each idempotent and writing progress markers.
  - Persist stage completion in DB plus artifact availability (e.g., `segments_src.json` key).
  - Enhance `/jobs/translate` to validate `resumeFrom`, enqueue only needed stages, and surface re-run info.
  - Add retry policies (Celery `autoretry_for`) with exponential backoff for transient failures.
- **Acceptance:** Cancelling mid-pipeline and reissuing the job with `resumeFrom` continues from the desired stage; retries show up in job history; unit tests cover failure/retry paths.

## 3. API & Schema Hardening
- **Goal:** Provide immutable contract docs and richer endpoint coverage.
- **Implementation:**
  - Generate `docs/openapi.yaml` via FastAPI + manual edits; version it and add npm script to regenerate clients.
  - Create `GET /v1/jobs` pagination, `DELETE /v1/jobs/{id}` (cancel), and `POST /v1/jobs/{id}/retry`.
  - Expand Pydantic schemas with nullable fields for logs, metrics, available outputs.
  - Add automated schema tests (compare JSON schema snapshots) to catch regressions.
- **Acceptance:** OpenAPI passes spectral lint; frontend/mobile regenerate typed clients successfully; new job management endpoints work with tests.

## 4. Web Experience Enhancements
- **Goal:** Empower users to configure jobs, monitor progress, and inspect outputs in the web app.
- **Implementation:**
  - Extend `UploadPage` with multi-language selection, preset pickers, and validations vs allowed languages.
  - Add a Job detail panel showing per-stage logs, metrics, and “Retry from stage” controls.
  - Surface available audio/subtitle tracks on `WatchPage`, allowing switching via Video.js APIs.
  - Adopt a shared design system (e.g., Chakra/Material) for consistent components.
- **Acceptance:** Users can launch multi-language jobs with custom presets, see detailed progress and logs, and switch tracks in the player; unit tests cover new components.

## 5. Mobile App Uplift
- **Goal:** Deliver feature parity with the web for upload/monitor/playback.
- **Implementation:**
  - Implement chunked upload using presigned URLs (React Native FS or expo-file-system).
  - Add job list filters, push/poll notifications for completion, and a retry button per job.
  - Enhance Player screen to choose audio/subtitle tracks (react-native-video track API).
  - Share API client/types with the web app via a workspace package or generated SDK.
- **Acceptance:** QA can upload, monitor, and play jobs entirely from the mobile app; jest/e2e tests validate flows.

## 6. Security & Access Controls
- **Goal:** Protect endpoints and assets before exposing externally.
- **Implementation:**
  - Introduce JWT or API-key auth middleware on FastAPI routes; store secrets via env.
  - Enforce per-user quotas (max upload size, concurrent jobs) and return descriptive errors.
  - Generate signed, short-lived URLs for HLS access (`storage.build_signed_url` updates).
  - Sanitize logs (PII scrubbing) and document policies under `docs/security/`.
- **Acceptance:** Unauthorized requests are rejected, quotas configurable via env, signed URLs expire as expected; security tests cover common abuse paths.

## 7. CI/CD Automation
- **Goal:** Prevent regressions and produce deployable images.
- **Implementation:**
  - Create `.github/workflows/ci.yml` running lint, type-check, test matrices for backend/workers/web/mobile.
  - Add a job that builds Docker images, runs `docker compose` smoke test (seed job), and uploads artifacts/logs.
  - Optionally integrate container scanning (Trivy) and codecov.
- **Acceptance:** CI passes on clean tree, failing tests block merges; generated images run the smoke job automatically.

## 8. Express Gateway Variant (Optional)
- **Goal:** Support JS-first teams via the `02b_backend_express` prompt.
- **Implementation:**
  - Scaffold `express-gw/` with NestJS or Express + TypeScript.
  - Implement auth, rate limiting, SSE progress updates, and request shaping.
  - Add integration tests with supertest and contract tests vs FastAPI.
- **Acceptance:** Gateway proxies all required routes, handles uploads via presigned URLs, and passes test suite; documentation updated with deployment steps.

## Tracking & Ownership
- Assign each task to a squad lead (e.g., Backend, ML, Frontend, Mobile, DevOps).
- Link tasks to GitHub issues or project management tickets for progress tracking.
- Update this file whenever scope changes; cross-reference MANUAL_TASKS.md for prerequisites.
