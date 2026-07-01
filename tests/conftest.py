import fitz
import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def pdf_bytes():
    """Factory for well-formed, unencrypted PDF bytes with the given page count."""

    def _make(pages: int = 1) -> bytes:
        doc = fitz.open()
        for _ in range(pages):
            doc.new_page()
        return doc.write()

    return _make


@pytest.fixture
def encrypted_pdf_bytes():
    """Factory for password-protected PDF bytes with the given page count."""

    def _make(pages: int = 1) -> bytes:
        doc = fitz.open()
        for _ in range(pages):
            doc.new_page()
        return doc.write(
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner",
            user_pw="user",
            permissions=0,
        )

    return _make


# pymupdf refuses to serialize a zero-page document ("cannot save with zero
# pages"), so a minimal empty-Pages-tree PDF is hand-crafted instead. fitz can
# still open this and reports page_count == 0.
@pytest.fixture
def zero_page_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [] /Count 0 >>endobj\n"
        b"trailer<< /Root 1 0 R >>\n"
        b"%%EOF"
    )


@pytest.fixture
def upload_file_factory():
    """Factory for a minimal UploadFile double exposing only what read_pdf/read_image use."""

    class FakeUploadFile:
        def __init__(self, content: bytes, content_type: str, size: int | None):
            self._content = content
            self.content_type = content_type
            self.size = size

        async def read(self) -> bytes:
            return self._content

    unset = object()

    def _make(content: bytes, content_type: str = "application/pdf", size=unset):
        resolved_size = len(content) if size is unset else size
        return FakeUploadFile(content, content_type, resolved_size)

    return _make
