# How to Extract Structured Data

Use this guide when you need the worker to return schema-shaped fields in addition to raw OCR detections.

## 1. Define the schema

Send a normal JSON Schema object. Keep it small. Only ask for fields you need.

```json
{
  "type": "object",
  "properties": {
    "invoice_number": { "type": "string" },
    "total": { "type": "number" }
  },
  "required": ["invoice_number", "total"]
}
```

## 2. Submit the file and schema

Pass the schema as a form field named `extraction_schema`.

```python
import json
import requests

url = "http://127.0.0.1:8000/api/v1/ocr/process"
schema = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"}
    }
}

with open("invoice.pdf", "rb") as file_handle:
    response = requests.post(
        url,
        files={"file": ("invoice.pdf", file_handle, "application/pdf")},
        data={"extraction_schema": json.dumps(schema)},
    )

print(response.json())
```

## 3. Poll the task

Use the returned `task_id` with `GET /api/v1/ocr/results/{task_id}`.

The worker returns:

- `detections`: OCR output from PaddleOCR.
- `extracted_data`: structured output when schema extraction succeeds.

Example shape:

```json
{
  "task_id": "task_123",
  "status": "SUCCESS",
  "result": {
    "detections": [],
    "extracted_data": {
      "parsed_data": {
        "invoice_number": {
          "value": "INV-001",
          "bbox": [[120, 45], [200, 45], [200, 60], [120, 60]],
          "page_number": 1,
          "confidence": 0.98
        }
      }
    }
  }
}
```

If the schema is invalid JSON, the worker returns an `extracted_data.error` message instead of failing the whole OCR result.
