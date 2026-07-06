import cv2
from cv2.typing import MatLike

from aruco.dictionary import ARUCO_DICT


async def detect_markers(image: MatLike):  
    parameters = cv2.aruco.DetectorParameters()
    
    # Create the ArUco detector
    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, parameters)
    
    # Detect the markers
    corners, ids, rejected = detector.detectMarkers(image)

    if ids is None:
          return []
    return ids.flatten().tolist() 
