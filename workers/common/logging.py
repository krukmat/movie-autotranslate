from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from . import metrics

logger = logging.getLogger("workers")
_log_file_ctx: ContextVar[Optional[Path]] = ContextVar("job_log_file", default=None)


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def _append_to_job_log(payload: Dict[str, Any]) -> None:
    log_path = _log_file_ctx.get()
    if not log_path:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(_json_dumps(payload) + "\n")


def set_job_log_file(path: Optional[Path]) -> None:
    _log_file_ctx.set(path)


def log_event(
    *,
    job_id: str,
    asset_id: Optional[str],
    stage: str,
    event: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "jobId": job_id,
        "assetId": asset_id,
        "stage": stage,
        "event": event,
        "message": message,
        "logger": logger.name,
    }
    if extra:
        payload.update(extra)
    logger.info(_json_dumps(payload))
    _append_to_job_log(payload)


@dataclass
class StageTimer:
    job_id: str
    asset_id: Optional[str]
    stage: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.perf_counter)
    duration_ms: Optional[float] = None

    def end(self, status: str, message: str = "") -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.duration_ms = round(duration_ms, 2)
        log_event(
            job_id=self.job_id,
            asset_id=self.asset_id,
            stage=self.stage,
            event=status,
            message=message,
            extra={"durationMs": self.duration_ms, **self.metadata},
        )


@contextmanager
def stage_context(
    *,
    job_id: str,
    asset_id: Optional[str],
    stage: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Iterator[StageTimer]:
    timer = StageTimer(job_id=job_id, asset_id=asset_id, stage=stage, metadata=metadata or {})
    log_event(
        job_id=job_id,
        asset_id=asset_id,
        stage=stage,
        event="START",
        message="Stage started",
        extra=metadata,
    )
    metrics.report_stage_start(stage)
    try:
        yield timer
        elapsed = time.perf_counter() - timer.start_time
        metrics.report_stage_end(stage, elapsed)
        timer.end("SUCCESS", "Stage finished")
    except Exception as exc:
        metrics.report_stage_failure(stage)
        elapsed = time.perf_counter() - timer.start_time
        metrics.report_stage_end(stage, elapsed)
        timer.metadata.setdefault("error", str(exc))
        timer.end("FAILED", "Stage failed")
        raise


def configure_stdout_logging(level: int = logging.INFO) -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.setLevel(level)
    logger.addHandler(handler)
