import io
from typing import List
from PIL import Image
import pymupdf as fitz


class PDFProcessor:
    """
    Utility class for handling PDF operations.

    Provides methods to detect PDF files and rasterize their pages into image formats
    suitable for downstream OCR processing.
    """

    @staticmethod
    def is_pdf(file_content: bytes) -> bool:
        """
        Checks if the provided byte content represents a PDF file.

        Args:
            file_content: The raw bytes of the file to check.

        Returns:
            True if the magic number indicates a PDF (starts with '%PDF'), False otherwise.
        """
        return file_content.startswith(b"%PDF")

    @staticmethod
    def pdf_to_images(pdf_bytes: bytes, zoom: float = 2.0) -> List[Image.Image]:
        """
        Rasterizes a PDF document into a list of PIL Images.

        Args:
            pdf_bytes: The raw byte content of the PDF document.
            zoom: Resolution multiplier for rasterization. Higher values increase
                  output image dimensions and quality but consume more memory. Default: 2.0.

        Returns:
            A list of PIL.Image objects, one for each page in the PDF.
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
