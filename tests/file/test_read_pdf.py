import pytest

from file.errors import (
    EmptyFileError,
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    UnsupportedContentTypeError,
)
from file.read_pdf import read_pdf


async def test_returns_document_for_valid_pdf(upload_file_factory, pdf_bytes):
    file = upload_file_factory(pdf_bytes(pages=2))

    doc = await read_pdf(file)

    assert doc.page_count == 2


async def test_rejects_zero_size(upload_file_factory):
    file = upload_file_factory(b"", size=0)

    with pytest.raises(EmptyFileError):
        await read_pdf(file)


async def test_rejects_empty_contents_when_size_unknown(upload_file_factory):
    file = upload_file_factory(b"", size=None)

    with pytest.raises(EmptyFileError):
        await read_pdf(file)


async def test_rejects_wrong_content_type(upload_file_factory, pdf_bytes):
    file = upload_file_factory(pdf_bytes(), content_type="text/plain")

    with pytest.raises(UnsupportedContentTypeError):
        await read_pdf(file)


async def test_rejects_malformed_pdf_bytes(upload_file_factory):
    file = upload_file_factory(b"not a pdf")

    with pytest.raises(InvalidPdfError):
        await read_pdf(file)


async def test_rejects_zero_page_pdf(upload_file_factory, zero_page_pdf_bytes):
    file = upload_file_factory(zero_page_pdf_bytes)

    with pytest.raises(EmptyPdfError):
        await read_pdf(file)


async def test_rejects_encrypted_pdf(upload_file_factory, encrypted_pdf_bytes):
    file = upload_file_factory(encrypted_pdf_bytes())

    with pytest.raises(EncryptedPdfError):
        await read_pdf(file)
