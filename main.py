from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import uvicorn
from ocr import OCRService
import traceback

app = FastAPI(
    title="PaddleOCR Service",
    description="A dedicated microservice for PP-StructureV3 processing."
)

try:
    print("🚀 Loading PP-StructureV3 model into memory via OCRService...")
    ocr_service = OCRService()
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Critical Error: Could not load PaddleOCR model. {e}")
    ocr_service = None

@app.post("/inference/process", tags=["OCR"])
async def process_image(file: UploadFile = File(...)) -> List[dict]:
    """
    Accepts an image or PDF file, processes it with PP-StructureV3,
    and returns the structured JSON output with bounding boxes.
    """
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR Service is not available due to model loading failure.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    mime_type = file.content_type
    try:
        result = ocr_service.process_file_content(file_bytes, mime_type)
        return result
    except Exception as e:
        print(f"Error during prediction: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred during OCR processing: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
