from fastapi import UploadFile
import fitz

from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InputTooLargeError,
    InvalidPdfError,
    SignedPdfError,
    UnsupportedContentTypeError,
)
from limits import MAX_PDF_PAGES, MAX_UPLOAD_BYTES


def _has_digital_signature(doc: fitz.Document) -> bool:
    for page in doc:
        for widget in page.widgets():
            if (
                widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE
                and widget.is_signed is True
            ):
                return True
    return False


async def read_pdf(file: UploadFile) -> fitz.Document:
    if file.size is not None and file.size <= 0:
        raise EmptyFileError("File is empty.")
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise InputTooLargeError(f"File exceeds {MAX_UPLOAD_BYTES} byte limit.")

    if file.content_type != "application/pdf":
        raise UnsupportedContentTypeError(
            f"Unsupported content type '{file.content_type}'. Expected 'application/pdf'."
        )

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise EmptyFileError("File is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise InputTooLargeError(f"File exceeds {MAX_UPLOAD_BYTES} byte limit.")

    try:
        doc = fitz.open(stream=contents, filetype="pdf")
    except (fitz.FileDataError, RuntimeError, ValueError) as error:
        raise InvalidPdfError("Invalid PDF file.") from error

    try:
        if doc.is_encrypted:
            raise EncryptedPdfError("PDF is encrypted.")
        if doc.page_count == 0:
            raise EmptyPdfError("PDF has no pages.")
        if doc.page_count > MAX_PDF_PAGES:
            raise InputTooLargeError(
                f"PDF has more than {MAX_PDF_PAGES} page(s)."
            )
        if _has_digital_signature(doc):
            raise SignedPdfError("PDF is digitally signed and cannot be modified.")
        return doc
    except Exception:
        doc.close()
        raise
