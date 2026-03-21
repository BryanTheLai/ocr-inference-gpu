# OCR Inference GPU Notes

## Architecture

The request path is simple:

```python
@app.post("/api/v1/ocr/process", response_model=TaskStatus, status_code=202)
async def create_ocr_task(file: UploadFile = File(...)):
    contents = await file.read()
    task = run_ocr_processing.delay(contents, file.content_type)
    return TaskStatus(task_id=task.id, message="OCR task queued successfully.")
```

The worker path stays lazy so the OCR model is loaded once per worker process:

```python
_ocr_service = None

def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
```

The OCR service normalizes PDF and image inputs into the same extraction path:

```python
if self._is_pdf(file_content):
    images = self._pdf_to_images(file_content)
    for page_num, image in enumerate(images, 1):
        detections = self._process_image_with_pipeline(image, page_num)
```

## Root Fix

The failure path in image processing was masking the original exception. The cleanup block now only removes the temp file:

```python
finally:
    if temp_path:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
```

## Notebook Fix

The notebook now imports `io` before using `io.BytesIO` in the page-rendering cell.

## Verification

Tests added in `tests/test_api_and_ocr.py` cover:

```python
assert response.status_code == 202
assert response.json() == {
    "task_id": "task-123",
    "status": "pending",
    "message": "OCR task queued successfully.",
}
```

```python
assert response.model_dump() == expected_body
```

```python
with pytest.raises(RuntimeError, match="pipeline failed"):
    service._process_image_with_pipeline(image, page_number=1)
```

Run result:

```text
5 passed
```