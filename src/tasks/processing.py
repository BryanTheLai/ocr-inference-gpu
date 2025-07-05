# src/tasks/processing.py
from src.tasks.celery_app import celery_app

# Switch to lazy singleton initialization so models load only once on first task run
from src.ocr_service import OCRService

_ocr_service = None
def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        print("🚀 Celery: Loading OCRService...")
        _ocr_service = OCRService()
        print("✅ Celery: OCRService loaded.")
    return _ocr_service

@celery_app.task(bind=True)
def run_ocr_processing(self, file_content: bytes, mime_type: str):
    try:
        svc = get_ocr_service()
    except Exception as e:
        print(f"❌ Celery: OCRService init failed: {e}")
        raise RuntimeError("OCR Service unavailable")
    # delegate to OCRService
    results = svc.process_file_content(file_content, mime_type)
    return {"detections": results}