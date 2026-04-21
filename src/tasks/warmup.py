from src.tasks.processing import get_ocr_service


def main() -> None:
    print("Preloading OCR models into the shared PaddleX cache...")
    get_ocr_service()
    print("OCR warmup complete.")


if __name__ == "__main__":
    main()
