# API & Schemas Prompt

## Objective
Define OpenAPI v3 spec and common schemas for assets, jobs, segments, and publishing.

## Artifacts
- `docs/openapi.yaml` with all endpoints (FastAPI can auto-gen; still write a hand-edited version).
- JSON Schemas:
  - `Asset`: { id, userId, srcLang?, targetLangs[], keys, createdAt }
  - `Job`: { id, assetId, stage, status, progress, startedAt, endedAt }
  - `Segment`: { idx, speakerId?, t0, t1, text_src, text_tgt?, wav_tgt_key? }
  - `VoicesMap`: { S0: {preset|cloneRef}, ... }

## Acceptance
- OpenAPI validated; clients generated for web/mobile.
