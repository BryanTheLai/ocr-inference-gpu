"""FastAPI entry point for OCR submission and task polling."""

import logging
from typing import Optional

from celery.result import AsyncResult
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from src.core.cache import redis_client
from src.models.schema import TaskResult, TaskStatus
from src.tasks.celery_app import celery_app
from src.tasks.processing import run_ocr_processing

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Async AI Processing API",
    description="A demonstration of using FastAPI with Celery and Redis.",
)


@app.post("/api/v1/ocr/process", response_model=TaskStatus, status_code=202)
async def create_ocr_task(
    file: UploadFile = File(...), extraction_schema: Optional[str] = Form(None)
):
    """Queue one OCR job and return the Celery task id.

    Args:
        file: Uploaded PDF or image file.
        extraction_schema: Optional JSON schema string for hybrid extraction.

    Returns:
        TaskStatus with the queued task id and confirmation message.
    """
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
    """Return the current Celery state and any stored result for one task.

    Args:
        task_id: Celery task id returned by the submission endpoint.

    Returns:
        TaskResult with status, result payload, and queue depth.
    """
    task = AsyncResult(task_id, app=celery_app)
    queue_name = celery_app.conf.get("task_default_queue", "celery")
    pending_count = redis_client.llen(queue_name)
    if not task.ready():
        logger.info("[STATUS] Task is still pending or running.")
        return TaskResult(
            task_id=task_id, status=task.status, pending_tasks=pending_count
        )
    if task.successful():
        logger.info("[SUCCESS] Task completed successfully.")
        return TaskResult(
            task_id=task_id,
            status=task.status,
            result=task.result,
            pending_tasks=pending_count,
        )
    logger.error(f"[FAILURE] Task failed. Error: {task.info}")
    return TaskResult(
        task_id=task_id,
        status=task.status,
        result={"error": str(task.info)},
        pending_tasks=pending_count,
    )
