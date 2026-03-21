import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import src.api.main as api_main
import src.ocr_service as ocr_service_module


def test_create_ocr_task_queues_uploaded_file(monkeypatch):
    captured = {}

    class FakeTask:
        id = "task-123"

    def fake_delay(file_content, mime_type, extraction_schema=None):
        captured["file_content"] = file_content
        captured["mime_type"] = mime_type
        captured["extraction_schema"] = extraction_schema
        return FakeTask()

    monkeypatch.setattr(api_main.run_ocr_processing, "delay", fake_delay)

    client = TestClient(api_main.app)
    response = client.post(
        "/api/v1/ocr/process",
        files={"file": ("document.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 202
    assert response.json() == {
        "task_id": "task-123",
        "status": "pending",
        "message": "OCR task queued successfully.",
    }
    assert captured["file_content"] == b"%PDF-1.4\n"
    assert captured["mime_type"] == "application/pdf"


@pytest.mark.parametrize(
    "status, ready, successful, result, info, expected_body",
    [
        (
            "STARTED",
            False,
            False,
            None,
            None,
            {
                "task_id": "task-abc",
                "status": "STARTED",
                "result": None,
                "pending_tasks": 7,
            },
        ),
        (
            "SUCCESS",
            True,
            True,
            {"detections": [{"text": "hello"}]},
            None,
            {
                "task_id": "task-abc",
                "status": "SUCCESS",
                "result": {"detections": [{"text": "hello"}]},
                "pending_tasks": 7,
            },
        ),
        (
            "FAILURE",
            True,
            False,
            None,
            RuntimeError("boom"),
            {
                "task_id": "task-abc",
                "status": "FAILURE",
                "result": {"error": "boom"},
                "pending_tasks": 7,
            },
        ),
    ],
)
def test_get_task_result_maps_celery_state(monkeypatch, status, ready, successful, result, info, expected_body):
    class FakeResult:
        def __init__(self):
            self.status = status
            self._ready = ready
            self._successful = successful
            self.result = result
            self.info = info

        def ready(self):
            return self._ready

        def successful(self):
            return self._successful

    class FakeRedis:
        def llen(self, queue_name):
            return 7

    monkeypatch.setattr(api_main, "AsyncResult", lambda task_id, app: FakeResult())
    monkeypatch.setattr(api_main, "redis_client", FakeRedis())

    response = api_main.get_task_result("task-abc")

    assert response.model_dump() == expected_body

def test_process_image_with_pipeline_handles_prediction_failure(monkeypatch):
    class FakePipeline:
        def predict(self, input):
            raise RuntimeError("pipeline failed")

    monkeypatch.setattr(ocr_service_module, "create_pipeline", lambda **kwargs: FakePipeline())

    service = ocr_service_module.OCRService(pipeline_config="ignored.yaml")
    image = Image.new("RGB", (8, 8), color="white")

    with pytest.raises(RuntimeError, match="pipeline failed"):
        service._process_image_with_pipeline(image, page_number=1)