# Movie AutoTranslate Documentation

This folder will host generated OpenAPI specs, runbooks, and operational checklists.

- `openapi.yaml` — canonical API definition exported from FastAPI once routes stabilize.
- `runbooks/` — on-call and recovery guidance for pipeline incidents.
- `playbooks/` — instructions for retraining or updating ASR/TTS models.

To regenerate the OpenAPI spec locally:

```bash
poetry run uvicorn app.main:app --reload
curl http://localhost:8000/v1/openapi.json > docs/openapi.json
```
