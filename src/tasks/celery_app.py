from celery import Celery
from src.configs.pipelines.settings import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.tasks.processing"],
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

print("✅ Celery application configured.")
