"""
Document reader module with error handling.
Supports PDF, DOCX, and TXT file extraction.
"""

from PyPDF2 import PdfReader
from docx import Document


def read_pdf(uploaded_file):
    """Extract text from a PDF file uploaded through Streamlit."""
    try:
        reader = PdfReader(uploaded_file)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"


def read_docx(uploaded_file):
    """Extract text from a DOCX file uploaded through Streamlit."""
    try:
        document = Document(uploaded_file)
        text = []
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        return f"[Error reading DOCX: {str(e)}]"


def read_txt(uploaded_file):
    """Extract text from a plain text file uploaded through Streamlit."""
    try:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[Error reading TXT: {str(e)}]"


def extract_text(uploaded_file):
    """
    Detect file type and route to the appropriate reader.
    Supports PDF, DOCX, and TXT.
    """
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    elif file_name.endswith(".docx"):
        return read_docx(uploaded_file)
    elif file_name.endswith(".txt"):
        return read_txt(uploaded_file)
    else:
        return "[Unsupported file format. Please upload PDF, DOCX, or TXT.]"