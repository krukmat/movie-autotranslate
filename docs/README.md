# Movie AutoTranslate Documentation

This folder will host generated OpenAPI specs, runbooks, and operational checklists.

- `openapi.yaml` — canonical API definition exported from FastAPI (run `python scripts/generate_openapi.py`).
- `ci.md` — CI pipeline overview (GitHub Actions jobs and local equivalents).
- `frontend.md` — notes on multi-language uploads, job view, and playback UI.
- `mobile.md` — Expo app workflow (upload, jobs, playback).
- `express-gateway.md` — guidance for the optional Express gateway.
- `runbooks/` — on-call and recovery guidance for pipeline incidents.
- `playbooks/` — instructions for retraining or updating ASR/TTS models.

To regenerate the OpenAPI spec locally:

```bash
python scripts/generate_openapi.py
```
