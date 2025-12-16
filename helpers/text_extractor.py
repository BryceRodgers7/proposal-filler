"""
Text extractor for the Proposal Filler application.
Handles extracting text from proposals and other documents.
"""
import pdfplumber
import io
from docx import Document   

def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file."""
    with pdfplumber.open(file) as pdf:
        texts = [(page.extract_text() or "") for page in pdf.pages]
    return "\n\n".join(texts)


def extract_text_from_docx(file) -> str:
    """Extract text from a DOCX file."""
    data = file.read()
    file.seek(0)
    mem_file = io.BytesIO(data)
    doc = Document(mem_file)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(uploaded_file) -> str:
    """Extract text from an uploaded file (PDF, DOCX, or TXT)."""
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.type or ""
    file_name = uploaded_file.name.lower()

    # PDF
    if "pdf" in file_type or file_name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    # DOCX
    if (
        "word" in file_type
        or file_name.endswith(".docx")
        or file_name.endswith(".doc")
    ):
        return extract_text_from_docx(uploaded_file)

    # Fallback: assume text
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    return raw_bytes.decode("utf-8", errors="ignore")