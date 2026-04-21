from types import SimpleNamespace

from fastapi.testclient import TestClient

import src.api.main as api_main


client = TestClient(api_main.app)


class DummyRedis:
    def __init__(self, pending_count: int) -> None:
        self.pending_count = pending_count

    def llen(self, _queue_name: str) -> int:
        return self.pending_count


def test_warmup_endpoint_queues_task(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main.warm_ocr_service,
        "delay",
        lambda: SimpleNamespace(id="warmup-task-id"),
    )

    response = client.post("/api/v1/ocr/warmup")

    assert response.status_code == 202
    assert response.json() == {
        "task_id": "warmup-task-id",
        "status": "pending",
        "message": "OCR warmup queued successfully.",
    }


def test_results_endpoint_returns_empty_result_while_pending(monkeypatch) -> None:
    class PendingTask:
        status = "STARTED"
        result = None
        info = None

        def ready(self) -> bool:
            return False

        def successful(self) -> bool:
            return False

    monkeypatch.setattr(api_main, "AsyncResult", lambda task_id, app=None: PendingTask())
    monkeypatch.setattr(api_main.redis.Redis, "from_url", lambda _url: DummyRedis(4))

    response = client.get("/api/v1/ocr/results/task-123")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-123",
        "status": "STARTED",
        "result": {},
        "pending_tasks": 4,
    }


def test_results_endpoint_normalizes_successful_none_payload(monkeypatch) -> None:
    class SuccessfulTask:
        status = "SUCCESS"
        result = None
        info = None

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

    monkeypatch.setattr(api_main, "AsyncResult", lambda task_id, app=None: SuccessfulTask())
    monkeypatch.setattr(api_main.redis.Redis, "from_url", lambda _url: DummyRedis(0))

    response = client.get("/api/v1/ocr/results/task-456")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-456",
        "status": "SUCCESS",
        "result": {},
        "pending_tasks": 0,
    }
