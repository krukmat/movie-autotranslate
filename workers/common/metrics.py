from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

stage_in_progress = Gauge("job_stage_in_progress", "Jobs running per stage", ["stage"])
stage_failures = Counter("job_stage_failures_total", "Stage failures", ["stage"])
stage_duration = Histogram(
    "job_stage_duration_seconds",
    "Stage durations",
    ["stage"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)


def report_stage_start(stage: str) -> None:
    stage_in_progress.labels(stage=stage).inc()


def report_stage_end(stage: str, duration_seconds: float) -> None:
    stage_in_progress.labels(stage=stage).dec()
    stage_duration.labels(stage=stage).observe(duration_seconds)


def report_stage_failure(stage: str) -> None:
    stage_failures.labels(stage=stage).inc()
*** End Patch
