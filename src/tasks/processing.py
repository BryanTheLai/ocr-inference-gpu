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

@celery_app.task(
    bind=True,
    rate_limit='20/m'
)
def run_ocr_processing(self, file_content: bytes, mime_type: str, extraction_schema: Optional[str] = None):
    try:
        ocr_svc = get_ocr_service()
        extr_svc = get_extraction_service()
    except Exception as e:
        logger.error(f"Celery: Service init failed: {e}")
        raise RuntimeError("Services unavailable")
    
    results = ocr_svc.process_file_content(file_content, mime_type)
    
    if extraction_schema:
        try:
            schema_dict = json.loads(extraction_schema)
            extracted_data = extr_svc.process_hybrid_extraction(results, schema_dict)
            return {"detections": results, "extracted_data": extracted_data}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"detections": results, "extracted_data": {"error": str(e)}}

    return {"detections": results}