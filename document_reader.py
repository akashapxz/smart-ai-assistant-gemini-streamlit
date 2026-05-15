from PyPDF2 import PdfReader
from docx import Document
import io


def read_pdf(uploaded_file):
    """
    Extract text from a PDF file uploaded through Streamlit.
    """
    reader = PdfReader(uploaded_file)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text)


def read_docx(uploaded_file):
    """
    Extract text from a DOCX file uploaded through Streamlit.
    """
    document = Document(uploaded_file)
    text = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)

    return "\n".join(text)


def read_txt(uploaded_file):
    """
    Extract text from a plain text file uploaded through Streamlit.
    """
    return uploaded_file.read().decode("utf-8", errors="ignore")


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
        return ""