import os
import logging
import pdfplumber
import docx2txt
from app.config.settings import settings

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """Extracts text from PDF, DOCX, or TXT file with OCR fallback for scanned PDFs."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    _, ext = os.path.splitext(file_path.lower())
    
    if ext == ".txt":
        return _read_txt(file_path)
    elif ext == ".docx":
        return _read_docx(file_path)
    elif ext == ".pdf":
        return _read_pdf_with_ocr_fallback(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _read_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_docx(file_path: str) -> str:
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        logger.error(f"Error reading DOCX file: {e}")
        raise


def _read_pdf_with_ocr_fallback(file_path: str) -> str:
    text = ""
    try:
        # 1. Attempt standard PDF text extraction
        with pdfplumber.open(file_path) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text).strip()
    except Exception as e:
        logger.error(f"Standard PDF extraction failed: {e}")

    # 2. Check if the PDF has very little text (likely scanned) and OCR is enabled
    if (not text or len(text) < 100) and settings.OCR_ENABLED:
        logger.info(f"PDF text content is empty or too small. Attempting OCR on: {file_path}...")
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF pages to images
            images = convert_from_path(file_path)
            ocr_pages = []
            for i, img in enumerate(images):
                logger.info(f"Running OCR on page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(img)
                if page_text:
                    ocr_pages.append(page_text)
            
            ocr_text = "\n".join(ocr_pages).strip()
            if ocr_text:
                logger.info("OCR text extraction completed successfully.")
                return ocr_text
        except Exception as ocr_err:
            logger.warning(
                f"OCR extraction failed: {ocr_err}. "
                "Ensure 'tesseract' and 'poppler' are installed and added to the system PATH. "
                "Returning any standard text found instead."
            )

    return text
