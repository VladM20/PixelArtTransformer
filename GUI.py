import sys

from PySide6.QtCore import QSize, Slot

import image_processing as image
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, Qt, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QSpinBox, QMainWindow, \
    QHBoxLayout, QWidget, QGraphicsView, QMenuBar, QFileDialog, QComboBox

from image_processing import VGA_256_color_palette


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixel Art Transformer")
        # noinspection PyTypeChecker
        self.resize(QGuiApplication.primaryScreen().availableSize()*3/5)
        self.createMenuBar()
        # preview area
        self.preview = QLabel("Preview")
        self.preview.setMinimumSize(QSize(400, 300))

        preset = QComboBox()
        preset.addItem("EGA")
        preset.addItem("VGA")
        preset.addItem("Custom")

        uploadButton = QPushButton("Upload Image")
        uploadButton.clicked.connect(self.uploadImage)
        startButton = QPushButton("Start")
        startButton.clicked.connect(self.processImage)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(uploadButton)
        buttonLayout.addWidget(startButton)

        layout = QHBoxLayout()
        layout.addWidget(self.preview, stretch=3)
        layout.addLayout(buttonLayout, stretch=1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.currentImage = None

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        actionNew = QAction("New...", self)
        actionOpen = QAction("Open...", self)
        actionSave = QAction("Save...", self)
        actionSaveAs = QAction("Save as...", self)

        fileMenu.addAction(actionNew)
        fileMenu.addAction(actionOpen)
        fileMenu.addAction(actionSave)
        fileMenu.addAction(actionSaveAs)

        presetsMenu = menuBar.addMenu("&Presets")
        actionVGA = QAction("VGA", self)
        actionEGA = QAction("EGA", self)

        presetsMenu.addAction(actionVGA)
        presetsMenu.addAction(actionEGA)

    @Slot()
    def uploadImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", filter="Images (*.jpg *.jpeg, *.png *.bmp)")
        if fileName:
            self.currentImage = fileName
            pixmap = QPixmap(self.currentImage)
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def processImage(self):
        if not self.currentImage:
            print("No Image Selected")
            return
        img = image.readImage(self.currentImage)
        result = image.colorProcessing(img,palette=VGA_256_color_palette)

        height, width, channels = img.shape
        bytesPerLine = channels * width

        QImg = QImage(result.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(QImg)
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())