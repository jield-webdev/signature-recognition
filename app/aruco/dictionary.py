import cv2

# Marker ids only distinguish box slots on a page (identity travels in the
# DataMatrix), so the smallest predefined dictionary gives the best detection
# robustness: biggest cells, maximum distance between codes.
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
