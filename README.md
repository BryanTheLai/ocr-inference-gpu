# OCR Inference GPU

Async OCR for PDFs and images. FastAPI accepts uploads. Celery processes them. Redis carries task state. PaddleOCR returns detections.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg) ![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)

## What it does

- Accepts PDF and image uploads.
- Queues OCR work without blocking the API.
- Returns text boxes, confidence scores, and page numbers.
- Optionally runs hybrid extraction with a JSON schema.

## Quick Start

### Requirements

- Docker and Docker Compose
- NVIDIA GPU for production OCR workloads
- Redis for task state and Celery backend

### Run

```bash
docker compose up --build
```

Open:

- [API docs](http://localhost:8000/docs)
- [OpenAPI schema](http://localhost:8000/openapi.json)

### Submit a file

```bash
curl -X POST http://localhost:8000/api/v1/ocr/process \
  -F "file=@document.pdf"
```

### Submit a schema

```bash
curl -X POST http://localhost:8000/api/v1/ocr/process \
  -F "file=@document.pdf" \
  -F 'extraction_schema={"type":"object","properties":{"invoice_number":{"type":"string"}}}'
```

### Poll results

```bash
curl http://localhost:8000/api/v1/ocr/results/<task_id>
```

## API Surface

- `POST /api/v1/ocr/process` queues OCR work.
- `GET /api/v1/ocr/results/{task_id}` returns task state and results.

See [docs/api_reference.md](docs/api_reference.md) for response shapes.

## Processing Flow

1. FastAPI reads the upload.
2. Celery stores the task.
3. The worker loads OCR once per process.
4. PDFs are rasterized page by page.
5. PaddleOCR returns detections.
6. Optional extraction maps structured values back to boxes.

## Configuration

- `REDIS_URL`: Redis connection string. Default: `redis://redis:6379/0`
- `GEMINI_API_KEY`: Required for LLM-backed extraction

## Documentation

- [Architecture explanation](docs/architecture_hybrid_extraction.md)
- [Schema submission guide](docs/how_to_extract_schema.md)
- [Implementation notes](docs/implementation_notes.md)
- [API reference](docs/api_reference.md)

## Project Layout

- `src/api/main.py`: FastAPI routes
- `src/tasks/processing.py`: Celery task orchestration
- `src/ocr_service.py`: OCR pipeline wrapper
- `src/extraction_service.py`: Hybrid OCR + LLM extraction
- `src/core/`: Shared adapters and helpers
