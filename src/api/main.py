# src/api/main.py
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from src.models.schema import ProcessRequest, TaskStatus, TaskResult
from src.tasks.processing import run_ocr_processing
from src.tasks.celery_app import celery_app
from celery.result import AsyncResult
import redis
from src.configs.pipelines.settings import settings

logger = logging.getLogger(__name__)
redis_client = redis.Redis.from_url(settings.REDIS_URL)

app = FastAPI(
    title="Async AI Processing API",
    description="A demonstration of using FastAPI with Celery and Redis."
)

@app.post("/api/v1/ocr/process", response_model=TaskStatus, status_code=202)
async def create_ocr_task(
    file: UploadFile = File(...),
    extraction_schema: Optional[str] = Form(None)
):
    try:
        contents = await file.read()
        task = run_ocr_processing.delay(contents, file.content_type, extraction_schema)
        logger.info(f"[OCR QUEUED] Task ID: {task.id}")
        return TaskStatus(task_id=task.id, message="OCR task queued successfully.")
    except Exception as e:
        logger.error(f"[OCR ERROR] Could not queue OCR task: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue OCR task.")
    
@app.get("/api/v1/ocr/results/{task_id}", status_code=200, response_model=TaskResult)
def get_task_result(task_id: str) -> TaskResult:
    task = AsyncResult(task_id, app=celery_app)
    queue_name = celery_app.conf.get('task_default_queue', 'celery')
    pending_count = redis_client.llen(queue_name)
    if not task.ready():
        logger.info("[STATUS] Task is still pending or running.")
        return TaskResult(task_id=task_id, status=task.status, pending_tasks=pending_count)
    if task.successful():
        logger.info("[SUCCESS] Task completed successfully.")
        return TaskResult(task_id=task_id, status=task.status, result=task.result, pending_tasks=pending_count)
    logger.error(f"[FAILURE] Task failed. Error: {task.info}")
    return TaskResult(task_id=task_id, status=task.status, result={"error": str(task.info)}, pending_tasks=pending_count)