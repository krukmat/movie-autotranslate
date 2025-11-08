# Project Overview — AI Dubbing Platform (X → Y Audio) — EN/ES/FR/DE

## Role
You are a senior Product/Tech Writer creating a crisp brief for downstream code-generation agents (Codex / Claude Code).

## Goal
Build an MVP where a user uploads a movie/video in language **X** and the system outputs the **same movie with AI-generated audio in language Y** (and optional translated subtitles). Zero manual intervention for basic flow. Support **English, Spanish, French, German**.

## Top-Level Requirements
- **Uploads**: Large-file uploads (chunked) to object storage (S3-compatible, e.g., MinIO).
- **Automatic pipeline**: ASR → (optional diarization) → MT → TTS → duration/timbre tuning → audio assembly → mux/packaging → delivery.
- **Audio Delivery**: MP4 with replaced audio **or** HLS with **alternate audio tracks** per language + VTT subtitles.
- **Voices**: Free/OSS stack by default (Piper); optional GPU-enhanced Coqui XTTS-v2.
- **Scalability**: Job queue, idempotent workers, resumable jobs, retry on transient errors.
- **Observability**: Structured logs; minimal metrics.
- **DX**: Docker Compose for local dev; Makefile targets.
- **Cost**: Zero license cost; infra only.

## Quality Bar (MVP)
- Accurate timestamps preserved; no noticeable drift across scenes.
- Loudness normalized around –16 LUFS; no clipping.
- Track-level language metadata and subtitle tracks present.
- Round-trip: Upload a 5–10 min clip ⇒ dubbed track in < reasonable time on CPU VM.

## Output of the Code-Gen Sessions
- Monorepo skeleton with: `backend/` (FastAPI default), `workers/` (Python ML), `web/` (Next.js or Vite+React), `mobile/` (React Native), `ops/` (compose, infra), `docs/` (runbooks).
- Working E2E demo with one-click `make up`.
