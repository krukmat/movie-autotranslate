# Repository Guidelines

## Project Structure & Module Organization
- Layout: `backend/` (FastAPI API), `shared/` (SQLModel domain), `workers/` (ASR→mix pipeline), `web/` (React + Video.js), `mobile/` (React Native), `ops/` (compose + Makefile), `docs/` (OpenAPI/runbooks), `prompts-dubbing-ia/` (prompt pack). Media artifacts live in `/data/{raw|proc|pub}` or the matching MinIO buckets.

## Execution Flow & Prompt Usage
- Kick off with `15_master_orchestration.md`, then digest `00_overview.md` and `01_architecture.md` to align on scope and component boundaries.
- Stand up tooling via `10_devops_compose.md` and formalize contracts with `12_api_and_schemas.md`.
- Implement API surfaces from `02_backend_fastapi.md` (use `02b_backend_express.md` only if you need the JS gateway).
- Build the processing pipeline in order: `03_asr_whisper.md` → optional `06_diarization.md` → `04_mt_translation.md` → `05_tts_generation.md` → `07_audio_mix_and_hls.md`.
- Models: store Whisper checkpoints under `models/whisper/` and Piper voices under `models/piper/`; tweak via `ASR_MODEL_DIR` and `PIPER_MODEL_DIR`.
- Audio mix: `workers/mix/assemble.py` now emits voice/background stems and loudness-normalized outputs; flip `MIX_USE_DEMUCS=1` to enable Demucs separation when the CLI is installed.
- Observability: Prometheus metrics live at `api:8000/metrics` (control plane) and `worker:9101/metrics` (per-stage); JSONL logs per job are stored under `proc/{assetId}/logs/` with keys exposed as `logsKey`.
- Resume: see `docs/pipeline.md` for stage checkpoints and `resumeFrom` usage; `/v1/jobs/{id}` now surfaces `stageHistory` plus `logsKey`.
- Express gateway (optional): `express-gw/` proxies FastAPI endpoints for JS-first teams and adds rate limiting + SSE (`docs/express-gateway.md`).
- Layer in DX and resilience last: `11_observability.md`, `14_security_ethics.md`, `13_testing_ci.md`, then ship clients (`08_frontend_web.md`, `09_frontend_react_native.md`).

## Build, Test, and Development Commands
- `make up|down|logs|demo` in `ops/` stand up and exercise the whole stack.
- Backend: `uvicorn app.main:app --reload` for local dev, `pytest` for API/worker suites.
- Web: `npm install && npm run dev` (Vite/Next) and `npm run test`.
- Mobile: `yarn && npx expo start` (or React Native CLI) plus `yarn test`.

## Coding Style & Naming Conventions
- Python: format with `black` + `isort`, type-check with `mypy`, prefer snake_case for files/functions and PascalCase for Pydantic models.
- JavaScript/TypeScript: `eslint --fix` + `prettier`, camelCase for variables, PascalCase for React components, suffix hooks with `use*`.
- Config/env files: uppercase snake case (`LIBRETRANSLATE_URL`) and prefix service-specific keys (`WORKER_`, `API_`).

## Testing Guidelines
- Keep golden fixtures for ASR/TTS under `workers/tests/fixtures/`; verify duration drift ±0.5% and loudness –16 LUFS.
- Mark integration tests with `@pytest.mark.e2e` and run via `pytest -m e2e`; audio probes can leverage `ffmpeg -i` assertions.
- Frontend tests should stub API clients generated from `docs/openapi.yaml` to ensure schema drift is caught early.
- CI (GitHub Actions) must execute lint → type-check → unit → compose smoke test per `13_testing_ci.md`; expose Prometheus metrics at `/metrics` to satisfy `11_observability.md`.

## Commit & Pull Request Guidelines
- History is greenfield; adopt Conventional Commits (`feat:`, `fix:`, `chore:`) and keep scope limited to one logical change.
- Include prompt references (e.g., `Refs 05_tts_generation`) in PR descriptions so reviewers see the design source.
- PRs should note testing evidence (`pytest`, `npm test`, demo job result) and attach screenshots of HLS players when UI changes occur.
