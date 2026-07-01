def test_returns_marked_pdf(client, pdf_bytes):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_rejects_empty_file(client):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty."


def test_rejects_wrong_content_type(client):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415


def test_rejects_malformed_pdf(client):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Pdf Error"


def test_rejects_zero_page_pdf(client, zero_page_pdf_bytes):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", zero_page_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF has no pages."


def test_rejects_encrypted_pdf(client, encrypted_pdf_bytes):
    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", encrypted_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF is encrypted."


def test_returns_500_when_marking_fails_unexpectedly(client, pdf_bytes, monkeypatch):
    async def boom(_doc):
        raise RuntimeError("simulated mark_pdf failure")

    monkeypatch.setattr("handlers.aruco_signature.mark_pdf", boom)

    response = client.post(
        "/aruco-signature",
        files={"file": ("contract.pdf", pdf_bytes(pages=1), "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to process PDF."
