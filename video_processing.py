import cv2 as cv
import numpy as np
from PySide6.QtCore import QThread, Signal
from moviepy import VideoFileClip
import os
import tempfile
import image_processing as image

class VideoProcessing(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, inputPath, outputPath, newWidth, newHeight, palette, maxColors):
        super().__init__()
        self.inputPath = inputPath
        self.outputPath = outputPath
        self.newWidth = newWidth
        self.newHeight = newHeight
        self.palette = palette
        self.maxColors = maxColors

    def run(self):
        try:
            cap = cv.VideoCapture(self.inputPath)
            fps = cap.get(cv.CAP_PROP_FPS)
            totalFrames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

            noSound = os.path.join(tempfile.gettempdir(), "noSound.mp4")
            fourcc = cv.VideoWriter.fourcc(*"mp4v")
            out = cv.VideoWriter(noSound, fourcc, fps, (width, height))

            frameCount = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                frame = image.downscale(frame, self.newWidth, self.newHeight)
                frame = image.colorProcessing(frame, self.palette, self.maxColors)
                frame = image.upscale(frame, width, height)
                frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
                out.write(frame)

                frameCount += 1
                # progress bar calculation
                # 20% is reserved for audio
                percentage = int(frameCount / totalFrames * 80)
                self.progress.emit(percentage)

            cap.release()
            out.release()

            self.progress.emit(85)
            originalClip = VideoFileClip(self.inputPath)
            processedClip = VideoFileClip(noSound)

            if originalClip.audio is not None:
                processedClip.audio = originalClip.audio
                processedClip.write_videofile(self.outputPath, codec="libx264", audio_codec="aac")
            else:
                import shutil
                shutil.copy(noSound, self.outputPath)

            originalClip.close()
            processedClip.close()
            os.remove(noSound)

            self.progress.emit(100)
            self.finished.emit(self.outputPath)
        except Exception as e:
            self.error.emit(str(e))

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

