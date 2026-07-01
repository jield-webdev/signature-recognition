import cv2
import fitz

async def mark_pdf(file: fitz.Document) -> fitz.Document: 
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    page = file[0]
    W, H = page.rect.width, page.rect.height

    margin = 8 
    size = 8 

    positions = {
        0: (margin,            margin),             # top-left
        1: (W - margin - size, margin),             # top-right
        2: (W - margin - size, H - margin - size),  # bottom-right
        3: (margin,            H - margin - size),  # bottom-left
    }

    for marker_id, (x, y) in positions.items():
        img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 600)
        ok, buf = cv2.imencode(".png", img)
        rect = fitz.Rect(x, y, x + size, y + size)
        page.insert_image(rect, stream=buf.tobytes())

    return file 
