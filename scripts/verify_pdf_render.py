import io
import os
import tempfile

import fitz
from PIL import Image


def pdf_page_to_image(file_path, page_number=0, zoom=2):
    doc = fitz.open(file_path)
    try:
        page = doc.load_page(page_number)
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        image_data = pixmap.tobytes("png")
        image = Image.open(io.BytesIO(image_data))
    finally:
        doc.close()
    return image


def main():
    pdf_path = None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        pdf_path = temp_file.name

    try:
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "hello")
        document.save(pdf_path)
        document.close()

        image = pdf_page_to_image(pdf_path)
        print({"width": image.size[0], "height": image.size[1]})
        assert image.size[0] > 0
        assert image.size[1] > 0
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)


if __name__ == "__main__":
    main()
