from __future__ import annotations

try:  # pragma: no cover - optional dependency for local tests
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:  # pragma: no cover
    class _NoOpMetric:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def labels(self, **_: str) -> "_NoOpMetric":
            return self

        def inc(self, *_: float, **__: float) -> None:
            return None

        def dec(self, *_: float, **__: float) -> None:
            return None

        def observe(self, *_: float, **__: float) -> None:
            return None

        def set(self, *_: float, **__: float) -> None:
            return None

    class Counter(_NoOpMetric):
        pass

    class Gauge(_NoOpMetric):
        pass

    class Histogram(_NoOpMetric):
        pass

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
