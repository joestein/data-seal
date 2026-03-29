"""Celery application configuration."""

from celery import Celery

from dataseal.config import settings

celery_app = Celery(
    "dataseal",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "dataseal.tasks.emails.*": {"queue": "emails"},
        "dataseal.tasks.documents.*": {"queue": "documents"},
        "dataseal.tasks.webhooks.*": {"queue": "webhooks"},
        "dataseal.tasks.finalize.*": {"queue": "finalize"},
    },
    beat_schedule={
        "retry-pending-webhooks": {
            "task": "dataseal.tasks.webhooks.retry_pending_webhooks",
            "schedule": 30.0,
        },
    },
)

celery_app.autodiscover_tasks(
    ["dataseal.tasks.emails", "dataseal.tasks.documents", "dataseal.tasks.webhooks", "dataseal.tasks.finalize"]
)
