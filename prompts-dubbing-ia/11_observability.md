# Observability & Logging Prompt

## Objective
Add minimum viable observability:
- Structured JSON logs (service, stage, jobId, assetId, msg, ts).
- Basic Prometheus-style counters/gauges (jobs by stage/status).
- Error events stored per job (first/last).

## Acceptance
- Tail logs show clear stage transitions.
- Export `/metrics` from API with basic counts.
