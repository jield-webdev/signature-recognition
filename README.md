# Signature Recognition

FastAPI service for preparing PDF documents with ArUco-delimited signature boxes and validating, from a photo of the printed document, which boxes are signed.

## How it works

### Marker scheme

- **Dictionary:** a custom ArUco dictionary (5x5 bits, 5000 markers) generated once by `app/aruco/generate_dictionary.py` and committed to the repo as `app/aruco/dictionary.yaml` (see [Generating the dictionary](#generating-the-dictionary)). Both the marking and the detection side load this same file — it is the single source of truth. The dictionary is never regenerated at runtime.
- **Box encoding:** each signature box is identified by a numeric `box_id` (0–1249) and delimited by 4 markers, one per corner. The ArUco marker ID encodes both the box and the corner:

  ```text
  marker_id = 4 * box_id + corner        corner: 0=TL, 1=TR, 2=BR, 3=BL
  ```

  Because every corner has a distinct ID, detection knows exactly which corner a marker belongs to even when some markers are occluded.
- **Box IDs are opaque.** This service never sees the strings/labels associated with boxes. The caller owns a registry that assigns each label a free `box_id` (assignment, not hashing — hashing arbitrary strings into a small ID space collides) and maps IDs back to labels when reading validation results.
- **Print size:** markers are stamped at ~10 pt. 5x5 markers need slightly more resolution than 4x4; ~10 pt keeps them reliably decodable in handheld phone photos.

### Detection pipeline (`/validate-image`)

1. **Load dictionary** from the committed YAML at startup.
2. **Detect markers** with `cv2.aruco.ArucoDetector`. `minMarkerPerimeterRate` is lowered (~0.01) because the markers are small relative to a full-page photo.
3. **Group into boxes** via `divmod(marker_id, 4)`. A box is complete when all 4 corner roles are present. A duplicated marker ID (false decode) or fewer than 4 markers ⇒ the box is reported with `signed: null` instead of guessing.
4. **Rectify the region:** markers are printed axis-aligned, so each marker's *inner* corner (the one pointing into the box) is known from its role. The perspective transform built from the 4 inner corners yields a rectified ROI containing only the paper between the markers.
5. **Ink analysis:** grayscale → adaptive threshold (local contrast, so shadows across the page don't read as ink) → 3×3 morphological opening (removes sensor speckle) → ink ratio = fraction of dark pixels. `signed = ink_ratio > threshold` (~0.004, tuned against faint pencil signatures, the worst case).

## API

The project exposes two REST endpoints.

### `POST /aruco-signature`

Accepts a PDF document plus the signature boxes to stamp, and returns the same PDF with 4 ArUco markers around each box.

Request content type: `multipart/form-data`

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | PDF file | Yes | Original PDF document. |
| `boxes` | JSON string | Yes | Array of boxes to stamp, see below. |

Each element of `boxes`:

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `box_id` | Integer (0–1249) | Yes | Box identifier assigned by the caller's registry. |
| `x`, `y` | Number | Yes | Top-left corner of the signature area, in PDF points. |
| `width`, `height` | Number | Yes | Size of the signature area, in PDF points. |
| `page` | Integer | No | Page index, defaults to `0`. |

Successful response:

- PDF bytes with the ArUco markers applied.

Example:

```bash
curl -X POST http://localhost:8000/aruco-signature \
  -F "file=@contract.pdf;type=application/pdf" \
  -F 'boxes=[{"box_id": 12, "x": 120, "y": 640, "width": 220, "height": 90}]' \
  --output contract-with-aruco.pdf
```

### `POST /validate-image`

Accepts a photo of a printed, marked document. Detects every signature box present in the image and reports whether each one is signed. No coordinates are needed — the markers themselves locate the boxes.

Request content type: `multipart/form-data`

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | Image file | Yes | Photo of the printed document. |

Successful response:

```json
{
  "boxes": [
    {"box_id": 12, "signed": true,  "markers_found": 4, "ink_ratio": 0.031},
    {"box_id": 40, "signed": null,  "markers_found": 2, "ink_ratio": null}
  ]
}
```

| Key | Description |
| --- | --- |
| `box_id` | Box identifier; the caller maps it back to its label via its registry. |
| `signed` | `true`/`false`, or `null` when the box could not be evaluated (incomplete or ambiguous markers). |
| `markers_found` | Number of the box's 4 corner markers detected (a duplicate decode also makes the box ambiguous). |
| `ink_ratio` | Fraction of ink pixels in the rectified box; useful for logging borderline cases. `null` when the box could not be evaluated. |

Example:

```bash
curl -X POST http://localhost:8000/validate-image \
  -F "file=@signed-page.jpg;type=image/jpeg"
```

## Error Responses

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid, empty, or unreadable input. |
| `415 Unsupported Media Type` | Uploaded file type is not supported. |
| `422 Unprocessable Entity` | Required form fields are missing or malformed. |
| `500 Internal Server Error` | Unexpected processing error. |

## Testing

- **Unit tests:** synthetic images — markers rendered from the custom dictionary onto a white canvas (optionally warped/shaded), with drawn strokes for the "signed" cases.
- **Real-world check:** print and photograph a fresh sample batch once `/aruco-signature` stamps the new markers.

## Development

Requirements:

- Python `>=3.14`
- `uv`

Install dependencies:

```bash
uv sync
```

### Generating the dictionary

The custom ArUco dictionary is a **one-time setup step**:

```bash
uv run python app/aruco/generate_dictionary.py
```

This writes `app/aruco/dictionary.yaml` (5000 markers, 5x5 bits). Notes:

- It is slow — `extendDictionary` searches for well-separated marker patterns and can run at full CPU for several minutes.
- Run it **once** and commit `dictionary.yaml`. Never regenerate it: a different dictionary would stop decoding every document already printed with the old one. Nothing at runtime should call `extendDictionary`.
- Consumers load the committed file instead of generating anything:

  ```python
  fs = cv2.FileStorage(str(DICT_PATH), cv2.FILE_STORAGE_READ)
  aruco_dict = cv2.aruco.Dictionary()
  aruco_dict.readDictionary(fs.root())
  fs.release()
  ```

Run the API locally:

```bash
uv run fastapi dev app/main.py
```

Open the interactive API documentation at:

```text
http://localhost:8000/docs
```
