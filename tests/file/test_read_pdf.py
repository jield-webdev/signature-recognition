import fitz
import pytest

import file.read_pdf as read_pdf_module
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


async def test_rejects_upload_larger_than_limit_before_read(
    upload_file_factory, pdf_bytes, monkeypatch
):
    monkeypatch.setattr(read_pdf_module, "MAX_UPLOAD_BYTES", 4, raising=False)
    file = upload_file_factory(pdf_bytes())

    with pytest.raises(ValueError, match="exceeds"):
        await read_pdf(file)


async def test_rejects_pdf_with_too_many_pages(
    upload_file_factory, pdf_bytes, monkeypatch
):
    monkeypatch.setattr(read_pdf_module, "MAX_PDF_PAGES", 1, raising=False)
    file = upload_file_factory(pdf_bytes(pages=2))

    with pytest.raises(ValueError, match="more than 1 page"):
        await read_pdf(file)


async def test_rejects_digitally_signed_pdf(upload_file_factory, monkeypatch):
    class SignedWidget:
        field_type = fitz.PDF_WIDGET_TYPE_SIGNATURE
        is_signed = True

    class SignedPage:
        def widgets(self):
            return iter([SignedWidget()])

    class SignedDocument:
        is_encrypted = False
        page_count = 1
        closed = False

        def __iter__(self):
            return iter([SignedPage()])

        def close(self):
            self.closed = True

    document = SignedDocument()
    monkeypatch.setattr(read_pdf_module.fitz, "open", lambda **_: document)
    file = upload_file_factory(b"%PDF-1.7")

    with pytest.raises(ValueError, match="digitally signed"):
        await read_pdf(file)

    assert document.closed is True
