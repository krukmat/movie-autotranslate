# Observability Guide

## Metrics
- **API (`/metrics`)**: exposes Prometheus counters (`jobs_total`), gauges (`jobs_running`, `jobs_stage_active`) derived from the relational state. Scrape `http://api:8000/metrics` in Compose for a control-plane view.
- **Worker metrics**: Celery worker now runs a Prometheus HTTP server on `METRICS_PORT` (default `9101`). It includes per-stage gauges (`job_stage_in_progress`), failure counters, and histograms (`job_stage_duration_seconds`). Point Prometheus at `http://worker:9101` to capture runtime behavior.
- Configure alert rules around spike in `job_stage_failures_total` or sustained increases in `job_stage_duration_seconds` buckets.

## Structured Logging
- Every stage emits JSON logs (`jobId`, `assetId`, `stage`, `event`, `message`, `durationMs`). Logs are written to stdout (captured by Docker) and also appended to per-job files under `data/proc/<assetId>/logs/<jobId>.jsonl`.
- After each job (success or failure) logs are uploaded to MinIO (`proc` bucket) and the API surfaces `logsKey` so clients can fetch them.
- Tail logs locally via `docker compose logs worker | jq -R 'fromjson?'` to filter by job ID.

## Dashboarding Tips
- Import both metric endpoints into Prometheus; use Grafana panels for stage throughput, failure rate, and duration percentiles.
- Combine MinIO-hosted JSONL logs with a lightweight log shipper (Fluent Bit, Vector) if you need centralized search.
- For local debugging, open the log JSONL directly; each line is a self-contained event.
