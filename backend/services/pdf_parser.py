"""PDF text extraction service using pdfplumber.

Extracts raw text from PDF bank statements without assuming any fixed
column positions (format-agnostic, as required by Req 4.1).
"""

import pdfplumber


class PDFTextExtractionError(Exception):
    """Raised when text extraction from a PDF fails.

    This typically means the PDF is a scanned image (no embedded text)
    or the file is corrupt/not a valid PDF.
    """
    pass


def extract_text(pdf_file_path: str) -> str:
    """Extract raw text from all pages of a PDF using pdfplumber.

    DEPRECATED: Use extract_pages() for better handling of multi-page statements.
    
    Iterates over every page, collects the extracted text, and
    concatenates the results with newline separators. No assumptions
    are made about column positions or bank-specific layouts.

    Args:
        pdf_file_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text from all pages joined by newlines.

    Raises:
        PDFTextExtractionError: If pdfplumber raises any exception
            while opening or reading the file, or if the total
            extracted text is empty (e.g. scanned image PDF).
    """
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            page_texts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text)

        combined_text = "\n".join(page_texts)

    except PDFTextExtractionError:
        # Re-raise without wrapping so callers see the original subclass.
        raise
    except Exception as exc:
        raise PDFTextExtractionError(
            f"Failed to extract text from PDF '{pdf_file_path}': {exc}"
        ) from exc

    if not combined_text.strip():
        raise PDFTextExtractionError(
            "No extractable text found in PDF. "
            "The file may be a scanned image — please upload a text-based statement."
        )

    return combined_text


def extract_pages(pdf_file_path: str) -> list[str]:
    """Extract text from each page of a PDF as separate strings.

    This function returns one string per page, enabling page-by-page
    processing to avoid LLM output truncation on long documents.

    Args:
        pdf_file_path: Absolute or relative path to the PDF file.

    Returns:
        List of strings, one per page. Empty pages are excluded.

    Raises:
        PDFTextExtractionError: If pdfplumber raises any exception
            while opening or reading the file, or if no pages contain
            extractable text (e.g. scanned image PDF).
    """
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages.append(text)

    except PDFTextExtractionError:
        raise
    except Exception as exc:
        raise PDFTextExtractionError(
            f"Failed to extract pages from PDF '{pdf_file_path}': {exc}"
        ) from exc

    if not pages:
        raise PDFTextExtractionError(
            "No extractable text found in PDF. "
            "The file may be a scanned image — please upload a text-based statement."
        )

    return pages
