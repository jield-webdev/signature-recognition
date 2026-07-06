import cv2
import fitz

from aruco.dictionary import ARUCO_DICT


async def mark_pdf(file: fitz.Document) -> fitz.Document:
    page = file[0]
    W, H = page.rect.width, page.rect.height

    margin = 8
    size = 10  # 5x5 markers need slightly more print size than 4x4 to keep cells readable

    positions = {
        0: (margin,            margin),             # top-left
        1: (W - margin - size, margin),             # top-right
        2: (W - margin - size, H - margin - size),  # bottom-right
        3: (margin,            H - margin - size),  # bottom-left
    }

    for marker_id, (x, y) in positions.items():
        img = cv2.aruco.generateImageMarker(ARUCO_DICT, marker_id, 600)
        ok, buf = cv2.imencode(".png", img)
        rect = fitz.Rect(x, y, x + size, y + size)
        page.insert_image(rect, stream=buf.tobytes())

    return file 
