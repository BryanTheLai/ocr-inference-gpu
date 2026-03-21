# src/tasks/processing.py
import logging
import json
from functools import lru_cache
from typing import Optional
from src.tasks.celery_app import celery_app
from src.ocr_service import OCRService
from src.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ocr_service():
    logger.info("Celery: Loading OCRService...")
    svc = OCRService()
    logger.info("Celery: OCRService loaded.")
    return svc


@lru_cache(maxsize=1)
def get_extraction_service():
    logger.info("Celery: Loading ExtractionService...")
    svc = ExtractionService()
    logger.info("Celery: ExtractionService loaded.")
    return svc


@celery_app.task(bind=True, rate_limit="20/m")
def run_ocr_processing(
    self, file_content: bytes, mime_type: str, extraction_schema: Optional[str] = None
):
    """
    Celery background task bridging the API to the compute-heavy AI models.

    Accepts raw bytes and delegates to `OCRService` for parsing layout. If a JSON
    `extraction_schema` is supplied, it further delegates to `ExtractionService` for LLM mapping.

    Args:
        self: Bound task instance injected by Celery.
        file_content: Raw bytes of the target file.
        mime_type: File's internet media type (e.g. application/pdf).
        extraction_schema: Optional stringified JSON schema to enforce on LLM outputs.

    Returns:
        A dictionary containing raw 'detections' and optionally 'extracted_data'.

    Raises:
        RuntimeError: If services fail to initialize or the OCR pipeline crashes.
        ValueError: If file parameters or formats are invalid.
    """
    try:
        ocr_svc = get_ocr_service()
        extr_svc = get_extraction_service()
    except (ImportError, RuntimeError) as e:
        logger.error(f"Celery: Service init failed: {e}")
        raise RuntimeError(f"Services unavailable: {e}")

    try:
        results = ocr_svc.process_file_content(file_content, mime_type)
    except ValueError as e:
        logger.error(f"OCR File validation failed: {e}")
        raise ValueError(f"Invalid file: {e}")
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise RuntimeError(f"OCR Pipeline failed: {e}")

    if extraction_schema:
        try:
            schema_dict = json.loads(extraction_schema)
            extracted_data = extr_svc.process_hybrid_extraction(results, schema_dict)
            return {"detections": results, "extracted_data": extracted_data}
        except json.JSONDecodeError as e:
            logger.error(f"JSON schema decode failed: {e}")
            return {
                "detections": results,
                "extracted_data": {"error": "Invalid JSON schema."},
            }
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                "detections": results,
                "extracted_data": {"error": f"Extraction error: {e}"},
            }

    return {"detections": results}
