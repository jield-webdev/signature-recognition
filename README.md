# Signature Recognition

FastAPI service for preparing PDF documents with marked signature boxes and validating, from a photo of the printed document, which boxes are signed.

## How it works

Each signature box on a printed document carries two kinds of symbols, with separate jobs:

- **Geometry — ArUco markers.** Two markers per box, on the box diagonal: one at the top-left, one at the bottom-right. Their detected corners (8 points) are used to build the perspective transform that rectifies the photo. Markers come from OpenCV's predefined `DICT_4X4_50` — the smallest standard dictionary, which maximizes cell size and Hamming distance between codes, i.e. detection robustness in handheld photos.
- **Identity — a DataMatrix code.** Printed to the right of the top-left marker, it encodes the box's numeric id. Identity never travels in the ArUco ids, so the id space is not limited by any marker dictionary, and a damaged code fails loudly (no decode) instead of silently reading as a wrong id, thanks to Reed-Solomon error correction.

### Marker scheme

- **Marker ids encode page slots, not identity.** Slot `n` on a page uses marker ids `(2n, 2n+1)`: the even id is always the top-left marker, the odd id the bottom-right. With 50 ids that allows up to 25 boxes per page. Currently the marking endpoint stamps a single box (slot 0, ids 0 and 1) spanning the whole page.
- **Box ids are opaque.** Each box id maps to a string in the caller's database; this service never sees those strings. Valid ids are integers `1`–`999999` — 6 decimal digits keeps the DataMatrix at its smallest symbol sizes.
- **Print sizes.** ArUco markers and the DataMatrix are both stamped at ~18 pt. A white gap separates the marker border from the DataMatrix quiet zone.

### Detection pipeline

Identity detection is implemented; ink analysis is planned.

1. **Detect markers** with `cv2.aruco.ArucoDetector`. A photo may contain several boxes; every even marker id marks the top-left corner of one.
2. **Decode identity** per box: the top-left marker's 4 detected corners define the local perspective of the page plane, so its neighborhood is rectified with that homography and the DataMatrix is cropped at its known print offset and decoded with `zxing-cpp`. A decode failure is reported as `box_id: null` ("retake the photo"), never a guessed id.
3. **Ink analysis** *(planned)*: rectify the full box from both diagonal markers' 8 corners, threshold the interior adaptively (excluding the marker and DataMatrix areas), and compare the ink ratio against a tuned threshold to decide `is_signed`.

## API

### `POST /mark-pdf`

Accepts a PDF document plus a box id, and returns the same PDF with the box's ArUco marker pair on the first page's diagonal and a DataMatrix encoding the id next to the top-left marker.

Request content type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | PDF file | Yes | Original PDF document. |
| `box_id` | Integer (1–999999) | Yes | Box identifier assigned by the caller's registry. |

Successful response:

- PDF bytes with the markers and DataMatrix applied.

Example:

```bash
curl -X POST http://localhost:8000/mark-pdf \
  -F "file=@contract.pdf;type=application/pdf" \
  -F "box_id=12" \
  --output contract-with-marks.pdf
```

### `POST /validate-image`

Accepts a photo of a printed, marked document and returns the boxes found in it, one entry per detected top-left marker, ordered by slot. `is_signed` will be added to each entry once ink analysis lands.

Request content type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | Image file | Yes | Photo of the printed document. |

Successful response:

```json
{
  "boxes": [
    { "box_id": 123 },
    { "box_id": null }
  ]
}
```

A `box_id` of `null` means the box's marker was found but its DataMatrix could not be decoded (blur, glare, damage) — ask the user to retake the photo.

Example:

```bash
curl -X POST http://localhost:8000/validate-image \
  -F "file=@signed-page.jpg;type=image/jpeg"
```

## Error Responses

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid, empty, or unreadable input; box id out of range. |
| `415 Unsupported Media Type` | Uploaded file type is not supported. |
| `422 Unprocessable Entity` | Required form fields are missing or malformed. |
| `500 Internal Server Error` | Unexpected processing error. |

## Testing

- **Unit tests:** the marking tests rasterize the stamped PDF page and verify the full loop — both ArUco markers detect and the DataMatrix decodes back to the original box id.
- **Real-world check:** print and photograph a sample batch to validate marker/DataMatrix print sizes against real phone photos.

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
