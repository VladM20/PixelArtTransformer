import cv2 as cv
import numpy as np

def getFirstValidFrame(videoPath):
    cap = cv.VideoCapture(videoPath)
    validFrame = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if np.mean(frame) > 10:
            validFrame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            break

    cap.release()
    return validFrame