from fastapi import UploadFile
import fitz

from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    UnsupportedContentTypeError,
)


async def read_pdf(file: UploadFile) -> fitz.Document:
    if file.size is not None and file.size <= 0:
        raise EmptyFileError("File is empty.")

    if file.content_type != "application/pdf":
        raise UnsupportedContentTypeError(
            f"Unsupported content type '{file.content_type}'. Expected 'application/pdf'."
        )

    contents = await file.read()
    if not contents:
        raise EmptyFileError("File is empty.")

    try:
        doc = fitz.open(stream=contents, filetype="pdf")
    except fitz.FileDataError as error:
        raise InvalidPdfError("Invalid Pdf Error") from error

    if doc.is_encrypted:
        raise EncryptedPdfError("PDF is encrypted.")

    if doc.page_count == 0:
        raise EmptyPdfError("PDF has no pages.")

    return doc
