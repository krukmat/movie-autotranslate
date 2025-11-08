# System Architecture Prompt (Architect Agent)

## Objective
Design a minimal, production-lean architecture for the AI Dubbing MVP with **FastAPI** + **Python workers** as default, and a thin **ExpressJS gateway** variant as an option.

## Key Decisions
- **Storage**: S3-compatible (MinIO locally). Media keys organized: `/raw/{assetId}/`, `/proc/{assetId}/`, `/pub/{assetId}/`.
- **Queue**: Redis + Celery/RQ (Python-first). Define job types and transitions.
- **Services**:
  - `api`: FastAPI (auth, upload pre-sign, job orchestration, status).
  - `worker`: Python (ASR/MT/TTS/audio ops).
  - `libretranslate`: self-host MT REST.
  - `minio`: object storage.
  - `nginx-hls`: serve HLS playlists + public assets.
  - `redis`: broker for jobs.
- **Optional**: `express-gw` (Node) in front of FastAPI if team is JS-first.

## Job Graph (State Machine)
`INGESTED -> ASR -> TRANSLATE -> TTS -> ALIGN/MIX -> PACKAGE -> PUBLISHED -> DONE`  
On failure: record `FAILED_STAGE`, allow `RESUME_FROM=stage`.

## Data Contracts (high-level)
- `Asset`: { id, userId, srcLang?, targetLangs[], storageKeys, durationSec? }
- `Job`: { id, assetId, stage, status, startedAt, endedAt, progress, logsKey }
- `Segments`: list of { idx, speakerId, t0, t1, text_src, text_tgt?, wav_tgt_key? }
- `VoicesMap`: { speakerId -> voicePreset or cloneRef }
- `PublishInfo`: HLS master URL, tracks, captions

## Non-Goals
- Lip-sync visual morphing (future).
- Human-in-the-loop editorial UI (future).

## Deliverables
- Component diagram (ASCII + Mermaid).
- Sequence diagram for a full run.
- Folder structure proposal.
- Clear interfaces between API and workers.
