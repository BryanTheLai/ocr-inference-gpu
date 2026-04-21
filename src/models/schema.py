# src/models/schema.py
from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

class ProcessRequest(BaseModel):
    """The request model for initiating a processing task."""
    document_id: str
    processing_type: Literal["ocr", "summarize"]

class TaskStatus(BaseModel):
    """The response model for a task submission."""
    task_id: str
    status: str = "pending"
    message: str

class TaskResult(BaseModel):
    """The response model for checking the status and result of a task."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    # Number of tasks pending in the queue
    pending_tasks: Optional[int] = None