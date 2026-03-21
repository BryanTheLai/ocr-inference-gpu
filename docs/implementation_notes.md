# OCR Inference GPU Notes

## Request Path

`src/api/main.py` accepts the upload, reads the file once, and pushes the bytes into Celery.

The submission endpoint also accepts an optional `extraction_schema` form field. When present, the worker runs hybrid extraction after OCR.

## Worker Path

`src/tasks/processing.py` caches the OCR and extraction services with `lru_cache(maxsize=1)`. That keeps model loading lazy and local to each worker process.

The worker returns raw detections for every file. If schema extraction is requested, it adds an `extracted_data` payload.

## OCR Path

`src/ocr_service.py` normalizes PDFs and images into one pipeline.

- PDFs are rasterized page by page through `src/core/pdf_processor.py`.
- Images go directly into PaddleOCR.
- Each detection carries `text`, `box`, `confidence`, and `page_number`.

## Extraction Path

`src/extraction_service.py` sends serialized OCR text to `src/core/llm_client.py`.

The LLM returns JSON that is then grounded back to OCR boxes with fuzzy matching. That is why extracted values can carry bounding boxes and page numbers.

## Shared Adapters

- `src/core/cache.py` owns the Redis client.
- `src/core/pdf_processor.py` owns PDF rasterization.
- `src/core/llm_client.py` owns the LLM request.

## Current Behavior

- The API does not persist uploads.
- Results are polled through Celery task ids.
- Invalid JSON schemas are reported in the task result, not as an API crash.

## Verification

The test suite covers:

- task submission
- task polling
- OCR failure propagation
- current response shapes
