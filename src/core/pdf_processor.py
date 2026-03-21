"""PDF rasterization helpers used by the OCR pipeline."""

import io
from typing import List
from PIL import Image
import pymupdf as fitz


class PDFProcessor:
    @staticmethod
    def is_pdf(file_content: bytes) -> bool:
        """Return True when the bytes start with the PDF magic header."""
        return file_content.startswith(b"%PDF")

    @staticmethod
    def pdf_to_images(pdf_bytes: bytes, zoom: float = 2.0) -> List[Image.Image]:
        """Render each PDF page into a Pillow image.

        Args:
            pdf_bytes: Raw PDF bytes.
            zoom: Render scale factor. Higher values produce larger images.

        Returns:
            One Pillow image per PDF page.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix)
                image_data = pixmap.tobytes("png")
                image = Image.open(io.BytesIO(image_data))
                images.append(image)
        finally:
            doc.close()
        return images
