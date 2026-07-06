from pathlib import Path

import cv2

OUTPUT_PATH = Path(__file__).parent / "dictionary.yaml"

MARKER_COUNT = 5000
MARKER_BITS = 5

def main() -> None:
    aruco_dict = cv2.aruco.extendDictionary(MARKER_COUNT, MARKER_BITS)

    fs = cv2.FileStorage(str(OUTPUT_PATH), cv2.FILE_STORAGE_WRITE)
    aruco_dict.writeDictionary(fs)
    fs.release()

    print(f"Wrote {MARKER_COUNT} markers ({MARKER_BITS}x{MARKER_BITS} bits) to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
