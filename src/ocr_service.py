import io
from typing import Any, Dict, List, Optional
from paddlex import create_pipeline
from PIL import Image
import pymupdf as fitz
import os
import mimetypes
import time

class OCRService:
    def __init__(self, pipeline_config: str = "src/configs/pipelines/PP-StructureV3.yaml"):
        self.pipeline = create_pipeline(
            pipeline=pipeline_config,
            device="gpu",
            show_log=True
            )

    def _is_pdf(self, file_content: bytes) -> bool:
        return file_content.startswith(b'%PDF')

    def _is_image(self, mime_type: Optional[str]) -> bool:
        return bool(mime_type and mime_type.startswith('image/'))

    def _pdf_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                matrix = fitz.Matrix(2, 2)  # Increased zoom for higher quality
                pixmap = page.get_pixmap(matrix=matrix)
                image_data = pixmap.tobytes("png")
                image = Image.open(io.BytesIO(image_data))
                images.append(image)
        finally:
            doc.close()
        return images

    def _bytes_to_image(self, image_bytes: bytes) -> Image.Image:
        return Image.open(io.BytesIO(image_bytes))

    def _extract_ocr_results(self, paddle_result: Any, page_number: int = 1) -> List[Dict[str, Any]]:
        detections = []
        ocr_data = self._get_ocr_data(paddle_result)
        if not ocr_data:
            return detections
        texts = self._safe_get(ocr_data, 'rec_texts', [])
        scores = self._safe_get(ocr_data, 'rec_scores', [])
        boxes = self._safe_get(ocr_data, 'rec_boxes', [])
        for text, score, box in zip(texts, scores, boxes):
            normalized_box = self._normalize_box(box)
            detections.append({
                "text": str(text),
                "box": normalized_box,
                "confidence": float(score),
                "page_number": page_number
            })
        return detections

    def _get_ocr_data(self, paddle_result: Any) -> Optional[Dict]:
        ocr_keys = ['overall_ocr_res', 'rec_texts', 'ocr_res']
        for key in ocr_keys:
            if isinstance(paddle_result, dict) and key in paddle_result:
                return paddle_result[key]
            elif hasattr(paddle_result, key):
                return getattr(paddle_result, key)
        return None

    def _safe_get(self, data: Any, key: str, default: Any) -> Any:
        if isinstance(data, dict):
            return data.get(key, default)
        return getattr(data, key, default)

    def _normalize_box(self, box: Any) -> List[List[float]]:
        if len(box) == 4:
            x1, y1, x2, y2 = box
            return [
                [float(x1), float(y1)], [float(x2), float(y1)],
                [float(x2), float(y2)], [float(x1), float(y2)]
            ]
        elif len(box) == 8:
            return [[float(box[i]), float(box[i+1])] for i in range(0, 8, 2)]
        else:
            return [[float(point[0]), float(point[1])] for point in box]

    def process_file_content(self, file_content: bytes, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
        print("[DEBUG] Entered process_file_content")
        start_total = time.time()
        all_detections = []
        if self._is_pdf(file_content):
            print("[DEBUG] Detected PDF input")
            t_pdf2img = time.time()
            images = self._pdf_to_images(file_content)
            print(f"[DEBUG] PDF has {len(images)} pages. PDF to images took {time.time() - t_pdf2img:.2f} seconds")
            for page_num, image in enumerate(images, 1):
                start_page = time.time()
                t_save = time.time()
                # Save temp image and run pipeline
                detections = self._process_image_with_pipeline(image, page_num)
                t_pipeline = time.time()
                all_detections.extend(detections)
                print(f"[DEBUG] Page {page_num}: pipeline took {t_pipeline - t_save:.2f}s, total page {time.time() - start_page:.2f}s")
        elif self._is_image(mime_type):
            print("[DEBUG] Detected image input")
            t_imgload = time.time()
            image = self._bytes_to_image(file_content)
            print(f"[DEBUG] Image loaded in {time.time() - t_imgload:.2f} seconds")
            t_pipeline = time.time()
            all_detections = self._process_image_with_pipeline(image, 1)
            print(f"[DEBUG] pipeline took {time.time() - t_pipeline:.2f} seconds")
        else:
            print(f"[DEBUG] Unsupported file type: {mime_type}")
            raise ValueError(f"Unsupported file type: {mime_type}. Supported: PDF and image formats.")
        print(f"[DEBUG] Returning {len(all_detections)} detections. Total time: {time.time() - start_total:.2f} seconds")
        return all_detections

    def _process_image_with_pipeline(self, image: Image.Image, page_number: int = 1) -> List[Dict[str, Any]]:
        import tempfile
        temp_path = None
        t0 = time.time()
        try:
            t_save_start = time.time()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                image.save(temp_file.name, format='PNG')
                temp_path = temp_file.name
            t_save_end = time.time()
            print(f"[DEBUG] Saved temp image at {temp_path} (save took {t_save_end - t_save_start:.3f}s)")
            t_predict_start = time.time()
            result = self.pipeline.predict(input=temp_path)
            t_predict_end = time.time()
            print(f"[DEBUG] pipeline.predict result: {result} (predict took {t_predict_end - t_predict_start:.3f}s)")
            t_extract_start = time.time()
            result_list = list(result) if result else []
            if result_list:
                detections = self._extract_ocr_results(result_list[0], page_number)
            else:
                detections = []
            t_extract_end = time.time()
            print(f"[DEBUG] Extracted OCR results (extract took {t_extract_end - t_extract_start:.3f}s)")
            print(f"[DEBUG] Total _process_image_with_pipeline time: {time.time() - t0:.3f}s")
            return detections
        except Exception as e:
            print(f"[DEBUG] Exception in _process_image_with_pipeline: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def process_local_file(self, file_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        mime_type = mimetypes.guess_type(file_path)[0]
        with open(file_path, 'rb') as f:
            file_header = f.read(4)
        if self._is_pdf(file_header):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return self.process_file_content(file_content, mime_type)
        else:
            result = self.pipeline.predict(input=file_path)
            result_list = list(result) if result else []
            if result_list:
                return self._extract_ocr_results(result_list[0], 1)
            return []