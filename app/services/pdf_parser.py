from pypdf import PdfReader
from io import BytesIO

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Reads bytes from a PDF and extracts all text.
    """
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()
