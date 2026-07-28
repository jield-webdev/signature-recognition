from fastapi import FastAPI
from starlette.testclient import TestClient

from request_size_limit import RequestSizeLimitMiddleware


def test_healthz(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_cors_allows_post(client):
    response = client.options(
        "/validate-image",
        headers={
            "Origin": "https://example.test",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_request_limit_rejects_oversized_content_length():
    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=4)

    @app.post("/")
    async def receive_body():
        return {"ok": True}

    response = TestClient(app).post("/", content=b"12345")

    assert response.status_code == 413
    assert response.json()["detail"] == "Request exceeds 4 byte limit."
