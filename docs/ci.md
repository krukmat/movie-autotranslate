# Continuous Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **backend_and_workers job**
   - Sets up Python 3.11, installs backend/workers requirements.
   - Executes `pytest` inside `backend/` and `workers/`.
2. **web job**
   - Sets up Node 18, runs `npm install`, then `npm test -- --runInBand` in `web/`.

Future additions (mobile tests, linting, container builds) can extend this workflow with more jobs or steps. Keep tests deterministic (no watch modes). To run locally:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r workers/requirements.txt
(cd backend && pytest)
(cd workers && pytest)
(cd web && npm install && npm test -- --runInBand)
```
