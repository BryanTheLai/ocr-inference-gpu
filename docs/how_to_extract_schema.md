# How to Extract Structured Data

This guide covers how to provide a custom JSON schema to extract specific fields when submitting a document for processing.

## 1. Define the Schema

Construct a standard JSON Schema detailing the required fields.

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

## 2. Submit the Request

Pass the schema as a `Form` parameter named `extraction_schema` alongside the file. 

```python
import json
import requests

url = "http://127.0.0.1:8000/api/v1/ocr/process"
schema = {
    "type": "object",
    "properties": {"invoice_number": {"type": "string"}}
}

files = {
    "file": ("invoice.pdf", open("invoice.pdf", "rb"), "application/pdf")
}
data = {
    "extraction_schema": json.dumps(schema)
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## 3. Retrieve Results

Poll the returned `task_id` at `GET /api/v1/ocr/results/{task_id}`.

The completed result will include `extracted_data`, mapping your schema properties to their values, page numbers, and bounding boxes.

```json
{
  "task_id": "task_123",
  "status": "SUCCESS",
  "result": {
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
