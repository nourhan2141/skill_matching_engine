import fitz
import asyncio
from app.services.ocr_service import extract_text_from_image
import logging

async def extract_cv_text_robust(file_bytes: bytes) -> str:
    """
    Reads bytes from a PDF and extracts text robustly using PyMuPDF and OCR.
    For short CVs (<= 3 pages), or if plain text extraction fails a quality check,
    it falls back to rendering pages as images and running them through the vision OCR.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    
    # If it's a typical CV length, default to OCR to preserve layout and catch complex designs
    if page_count <= 3:
        return await _extract_via_ocr(doc)
        
    # For longer documents, try plain text extraction first
    text = ""
    for page in doc:
        extracted = page.get_text()
        if extracted:
            text += extracted + "\n"
            
    text = text.strip()
    
    # Quality check: if text is too short compared to page count, fallback to OCR
    if len(text) < page_count * 100:
        logging.info("Plain text extraction failed quality check. Falling back to OCR.")
        return await _extract_via_ocr(doc)
        
    return text

async def _extract_via_ocr(doc: fitz.Document) -> str:
    """
    Renders each page of the document to a PNG and extracts text using OCR concurrently.
    """
    tasks = []
    for page in doc:
        # Render page to an image (pixmap)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR quality
        png_bytes = pix.tobytes("png")
        tasks.append(extract_text_from_image(png_bytes, "image/png"))
        
    # Run OCR concurrently for all pages
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_text = []
    for res in results:
        if isinstance(res, Exception):
            logging.error(f"OCR failed for a page: {res}")
            continue
        if res:
            final_text.append(res)
            
    return "\n".join(final_text).strip()
