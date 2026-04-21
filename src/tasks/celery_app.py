# src/tasks/celery_app.py
from celery import Celery
from src.configs.pipelines.settings import settings

# Create the Celery application instance
# 'tasks' is the name of the main module where tasks are defined.
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL, # Backend to store task results
    include=["src.tasks.processing"] # List of modules to import when the worker starts
)

# Optional configuration for Celery
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600, # Expire results after 1 hour
)

print("✅ Celery application configured.")