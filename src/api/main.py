# src/api/main.py
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from src.models.schema import ProcessRequest, TaskStatus, TaskResult
from src.tasks.processing import run_ocr_processing
from src.tasks.celery_app import celery_app
from celery.result import AsyncResult
import redis
from src.configs.pipelines.settings import settings

app = FastAPI(
    title="Async AI Processing API",
    description="A demonstration of using FastAPI with Celery and Redis."
)

def log(msg):
    print(f"\n{'='*40}\n{msg}\n{'='*40}")

# New endpoint for OCR processing
@app.post("/api/v1/ocr/process", response_model=TaskStatus, status_code=202)
async def create_ocr_task(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        task = run_ocr_processing.delay(contents, file.content_type)
        log(f"[OCR QUEUED] Task ID: {task.id}")
        return TaskStatus(task_id=task.id, message="OCR task queued successfully.")
    except Exception as e:
        log(f"[OCR ERROR] Could not queue OCR task: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue OCR task.")
    
@app.get("/api/v1/ocr/results/{task_id}", status_code=200, response_model=TaskResult)
def get_task_result(task_id: str) -> TaskResult:
    task = AsyncResult(task_id, app=celery_app)
    # Fetch pending queue length
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
    queue_name = celery_app.conf.get('task_default_queue', 'celery')
    pending_count = redis_client.llen(queue_name)
    if not task.ready():
        log("[STATUS] Task is still pending or running.")
        return TaskResult(task_id=task_id, status=task.status, pending_tasks=pending_count)
    if task.successful():
        log("[SUCCESS] Task completed successfully.")
        return TaskResult(task_id=task_id, status=task.status, result=task.result, pending_tasks=pending_count)
    log(f"[FAILURE] Task failed. Error: {task.info}")
    return TaskResult(task_id=task_id, status=task.status, result={"error": str(task.info)}, pending_tasks=pending_count)