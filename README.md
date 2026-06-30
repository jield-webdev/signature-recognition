# Signature Recognition

FastAPI service for preparing PDF documents with ArUco signature impressions and validating whether a signature exists in a specific position of a document image.

## API

The project exposes two REST endpoints.

### `POST /documents/aruco-signatures`

Accepts a PDF document and returns the same PDF with ArUco signature impressions applied.

Request content type: `multipart/form-data`

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | PDF file | Yes | Original PDF document. |

Successful response:

- PDF bytes with the new ArUco impressions.

Example:

```bash
curl -X POST http://localhost:8000/documents/aruco-signatures \
  -F "file=@contract.pdf;type=application/pdf" \
  --output contract-with-aruco.pdf
```

### `POST /signatures/verify`

Accepts an image and the position in the original PDF where a signature should exist. Returns whether a signature is present at that position.

Request content type: `multipart/form-data`

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | Image file | Yes | Image to inspect. |
| `x` | Number | Yes | Expected signature area X coordinate. |
| `y` | Number | Yes | Expected signature area Y coordinate. |
| `width` | Number | Yes | Expected signature area width. |
| `height` | Number | Yes | Expected signature area height. |

Coordinates are expressed in the same coordinate system used by the original PDF page.

Successful response:

- ```json
{
  "exists": true
}
```

Example:

```bash
curl -X POST http://localhost:8000/signatures/verify \
  -F "file=@signed-page.png;type=image/png" \
  -F "x=120" \
  -F "y=640" \
  -F "width=220" \
  -F "height=90"
```

## Error Responses

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid, empty, or unreadable input. |
| `415 Unsupported Media Type` | Uploaded file type is not supported. |
| `422 Unprocessable Entity` | Required form fields are missing or malformed. |
| `500 Internal Server Error` | Unexpected processing error. |

## Development

Requirements:

- Python `>=3.14`
- `uv`

Install dependencies:

```bash
uv sync
```

Run the API locally:

```bash
uv run fastapi dev app/main.py
```

Open the interactive API documentation at:

```text
http://localhost:8000/docs
```
