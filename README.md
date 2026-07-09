# Signature Recognition

FastAPI service for preparing PDF documents with marked signature boxes and validating, from a photo of the printed document, which boxes are signed.

## How it works

Each signature box on a printed document carries two kinds of symbols, with separate jobs:

- **Geometry — ArUco markers.** Two markers per box, on the box diagonal: one at the top-left, one at the bottom-right. Their detected corners (8 points) are used to build the perspective transform that rectifies the photo. Markers come from OpenCV's predefined `DICT_4X4_50` — the smallest standard dictionary, which maximizes cell size and Hamming distance between codes, i.e. detection robustness in handheld photos.
- **Identity — a DataMatrix code.** Printed to the right of the top-left marker, it encodes the box's numeric id. Identity never travels in the ArUco ids, so the id space is not limited by any marker dictionary, and a damaged code fails loudly (no decode) instead of silently reading as a wrong id, thanks to Reed-Solomon error correction.

### Marker scheme

- **Marker ids encode page slots, not identity.** Slot `n` on a page uses marker ids `(2n, 2n+1)`: the even id is always the top-left marker, the odd id the bottom-right. With 50 ids that allows up to 25 boxes per page. Slots restart on every page — detection only ever works on a photo of one page, so ids only need to be unique within a page — and are assigned to a page's requested boxes in request order.
- **Box ids are opaque.** Each box id maps to a string in the caller's database; this service never sees those strings. Valid ids are integers `1`–`999999` — 6 decimal digits keeps the DataMatrix at its smallest symbol sizes.
- **Print sizes.** ArUco markers and the DataMatrix are both stamped at 24 pt, separated by a 4 pt white gap so the marker border and the DataMatrix quiet zone don't touch. The smallest box a caller may request must fit the top-left marker, the gap, the DataMatrix, another gap and the bottom-right marker — 80 pt wide by 52 pt tall.

### Detection pipeline

The full pipeline — identity detection and ink analysis — is implemented.

1. **Detect markers** with `cv2.aruco.ArucoDetector` (subpixel corner refinement, since the corners feed homographies). A photo may contain several boxes; a box is processed only when **both** of its markers are detected — incomplete pairs are ignored entirely.
2. **Crop each box** independently: the box's own 8 marker corners define its homography, so one box's noise or a bent page never distorts another. The box's size isn't known in advance — it's recovered by rectifying the plane from the top-left marker alone and measuring where the bottom-right marker lands. The crop is returned perspective-free at 4 px per print point.
3. **Decode identity** per box: the DataMatrix is cropped at its known print offset from the top-left marker in the rectified plane and decoded with `zxing-cpp`. A decode failure is reported as `box_id: null` ("retake the photo"), never a guessed id.
4. **Ink analysis** per box: the marker and DataMatrix rectangles sit at fixed positions in the rectified crop, so they are masked out (with a small safety padding, since rectification isn't pixel-perfect). The paper brightness is estimated as the median of the remaining interior; pixels darker than that background by a fixed delta count as ink, and the box is `is_signed` when the ink ratio clears a tuned threshold. Being background-relative, the check tolerates exposure and paper-tone differences between photos.

## API

### `POST /mark-pdf`

Accepts a PDF document plus a list of box placements, and returns the same PDF with, for each placement, an ArUco marker pair on the box's diagonal and a DataMatrix encoding its id next to the top-left marker.

Request content type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | PDF file | Yes | Original PDF document. |
| `boxes` | JSON string | Yes | Non-empty JSON array of box placements (see below). |

Each entry in `boxes` describes one box in PDF points with a top-left origin:

| Field | Type | Description |
| --- | --- | --- |
| `box_id` | Integer (1–999999) | Box identifier assigned by the caller's registry. |
| `page` | Integer (≥ 0) | Zero-based page index to stamp. |
| `x`, `y` | Number (≥ 0) | Top-left corner of the box on the page. |
| `width` | Number (≥ 80) | Box width; must fit the marker/DataMatrix/marker row. |
| `height` | Number (≥ 52) | Box height; must fit the two stacked markers. |

Placements are validated before anything is stamped: the box must fit inside its page, the page must exist, and a single page may hold at most 25 boxes.

Successful response:

- PDF bytes with the markers and DataMatrix applied.

Example:

```bash
curl -X POST http://localhost:8000/mark-pdf \
  -F "file=@contract.pdf;type=application/pdf" \
  -F 'boxes=[{"box_id":12,"page":0,"x":72,"y":600,"width":250,"height":80}]' \
  --output contract-with-marks.pdf
```

### `POST /validate-image`

Accepts a photo of a printed, marked document and returns the boxes found in it, one entry per complete marker pair, ordered by slot. Each entry carries the box's rectified (perspective-removed) crop as a base64-encoded WebP and an `is_signed` flag from the ink analysis.

Request content type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | Image file | Yes | Photo of the printed document. |

Successful response:

```json
{
  "boxes": [
    { "box_id": 123, "image": "UklGR... (base64 WebP)", "is_signed": true },
    { "box_id": null, "image": "UklGR... (base64 WebP)", "is_signed": false }
  ]
}
```

- A box appears only when both of its markers were detected; boxes with a missing marker are ignored.
- A `box_id` of `null` means the box was found and cropped but its DataMatrix could not be decoded (blur, glare, damage) — ask the user to retake the photo.
- `is_signed` is `true` when ink is detected in the box interior; the marker and DataMatrix areas are excluded from the measurement, so the printed symbols never count as ink.

Example:

```bash
curl -X POST http://localhost:8000/validate-image \
  -F "file=@signed-page.jpg;type=image/jpeg"
```

## Error Responses

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid, empty, or unreadable input; malformed `boxes` JSON; box id out of range; a box that doesn't fit, targets a missing page, or overflows a page's 25-box capacity. |
| `415 Unsupported Media Type` | Uploaded file type is not supported. |
| `422 Unprocessable Entity` | A required form field (`file` or `boxes`) is missing. |
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
