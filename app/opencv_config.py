import os

from limits import MAX_IMAGE_PIXELS

# OpenCV checks this limit before allocating decoded image buffers.
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(MAX_IMAGE_PIXELS)

import cv2
