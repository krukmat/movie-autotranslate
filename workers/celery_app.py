from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_default_queue = settings.broker_queue
celery_app.autodiscover_tasks(["workers.pipeline"])
