from pathlib import Path

import cv2

DICTIONARY_PATH = Path(__file__).parent / "dictionary.yaml"


def _load_dictionary() -> cv2.aruco.Dictionary:
    fs = cv2.FileStorage(str(DICTIONARY_PATH), cv2.FILE_STORAGE_READ)
    try:
        aruco_dict = cv2.aruco.Dictionary()
        if not aruco_dict.readDictionary(fs.root()):
            raise RuntimeError(f"Failed to read ArUco dictionary from {DICTIONARY_PATH}")
        return aruco_dict
    finally:
        fs.release()


ARUCO_DICT = _load_dictionary()
