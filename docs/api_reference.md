# API Reference

This document is a reference. It describes the current HTTP surface, request models, and response shapes.

## Endpoints

### `POST /api/v1/ocr/process`

Queues OCR processing for one uploaded file.

Request:

- Content type: `multipart/form-data`
- `file`: required upload. PDF or image.
- `extraction_schema`: optional JSON string. When present, the worker performs hybrid extraction after OCR.

Response: `202 Accepted`

```json
{
  "task_id": "string",
  "status": "pending",
  "message": "OCR task queued successfully."
}
```

### `GET /api/v1/ocr/results/{task_id}`

Returns the current Celery task state and any result payload.

Response: `200 OK`

```json
{
  "task_id": "string",
  "status": "PENDING",
  "result": null,
  "pending_tasks": 0
}
```

Success response:

```json
{
  "task_id": "string",
  "status": "SUCCESS",
  "result": {
    "detections": [
      {
        "text": "string",
        "box": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "confidence": 0.99,
        "page_number": 1
      }
    ],
    "extracted_data": {
      "parsed_data": {}
    }
  },
  "pending_tasks": 0
}
```

Failure response:

```json
{
  "task_id": "string",
  "status": "FAILURE",
  "result": {
    "error": "message"
  },
  "pending_tasks": 0
}
```

## Models

### `TaskStatus`

- `task_id`: Celery task id.
- `status`: Always `pending` on submission.
- `message`: Human-readable queue confirmation.

### `TaskResult`

- `task_id`: Celery task id.
- `status`: Celery state string.
- `result`: Task payload on success or failure details on error.
- `pending_tasks`: Queue depth sampled from Redis.

### `Detection`

Defined in `src/ocr_service.py`.

- `text`: Recognized text.
- `box`: Four-point polygon coordinates.
- `confidence`: OCR confidence score.
- `page_number`: 1-based page index.

## Environment Variables

- `REDIS_URL`: Broker and result backend URL.
- `GEMINI_API_KEY`: Used by the LLM client for schema extraction.

## Notes

- The API does not persist uploaded files.
- The worker owns OCR and extraction.
- Task polling is read-only. It does not mutate task state.
