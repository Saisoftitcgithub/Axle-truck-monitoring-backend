import cv2
from core.config import settings

def trigger_camera():
    cap = cv2.VideoCapture(settings.VIDEO_PATH)

    if not cap.isOpened():
        raise Exception("Video not opened")

    return cap