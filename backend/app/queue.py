from __future__ import annotations

from celery import Celery

from .core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "movie_autotranslate",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_default_queue = settings.broker_queue
celery_app.conf.result_expires = 3600


def enqueue_pipeline_job(job_external_id: str, resume_from: str | None = None) -> str:
    """Send the master pipeline task to Celery."""
    task = celery_app.send_task(
        "workers.pipeline.run_pipeline",
        kwargs={"job_id": job_external_id, "resume_from": resume_from},
        queue=settings.broker_queue,
    )
    return task.id
