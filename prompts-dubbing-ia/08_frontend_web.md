# Web Frontend Prompt (React + Video.js)

## Objective
Build a minimal web app to: upload, launch translation, track progress, and play HLS with audio/subtitle selectors.

## Features
- Auth stub.
- Uploader with chunked or presigned PUT.
- Job start: choose target languages + preset(s).
- Status page: stage-by-stage progress.
- Player page: Video.js rendering HLS master; audio-track & captions selector.

## Deliverables
- `web/` React (Vite or Next) app with:
  - pages: `/upload`, `/jobs/[id]`, `/watch/[assetId]`
  - components: `HlsPlayer` (Video.js), `JobProgress`
  - API client typed from OpenAPI.

## Acceptance
- Upload → job → watch flow works locally with compose.
