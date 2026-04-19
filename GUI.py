import sys
import os
from pathlib import Path
from PySide6.QtCore import QSize, Slot

import image_processing as image
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, Qt, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QSpinBox, QMainWindow, \
    QHBoxLayout, QWidget, QFileDialog, QComboBox, QVBoxLayout
from PySide6.QtCore import QSettings


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixel Art Transformer")
        # noinspection PyTypeChecker
        self.resize(QGuiApplication.primaryScreen().availableSize()*3/5)
        # preview area
        self.preview = QLabel("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(QSize(400, 300))
        self.preview.setStyleSheet("border: 1px solid gray;")

        # palette dropdown
        self.paletteDropdown = QComboBox()
        self.paletteDropdown.addItem("EGA (16 colors)")
        self.paletteDropdown.addItem("VGA (256 colors)")
        self.paletteDropdown.addItem("Custom")
        self.paletteDropdown.currentIndexChanged.connect(self.updatePreview)

        # resolution slider
        self.resolutionSlider = QSlider(Qt.Orientation.Horizontal)
        self.resolutionSlider.setRange(1, 512)
        self.resolutionSlider.setValue(100)
        self.resolutionSlider.sliderReleased.connect(self.updatePreview)

        # resolution spinbox
        self.resolutionSpinBox = QSpinBox()
        self.resolutionSpinBox.setRange(1, 512)
        self.resolutionSpinBox.setValue(100)
        self.resolutionSpinBox.editingFinished.connect(self.updatePreview)

        # connecting the resolution controls
        self.resolutionSlider.valueChanged.connect(self.resolutionSpinBox.setValue)
        self.resolutionSpinBox.valueChanged.connect(self.resolutionSlider.setValue)

        # buttons
        uploadButton = QPushButton("Upload Image")
        uploadButton.clicked.connect(self.uploadImage)
        processButton = QPushButton("Update Preview")
        processButton.clicked.connect(self.updatePreview)

        # layout
        # buttons layed out horizontally
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(uploadButton)
        buttonLayout.addWidget(processButton)

        # resolution controls layed horizontally
        resolutionLayout = QHBoxLayout()
        resolutionLayout.addWidget(QLabel("Pixel Resolution (width): "))
        resolutionLayout.addWidget(self.resolutionSpinBox)
        resolutionLayout.addWidget(self.resolutionSlider)

        # all controls layed out vertically
        controlsLayout = QVBoxLayout()
        controlsLayout.addWidget(QLabel("Color Palette: "))
        controlsLayout.addWidget(self.paletteDropdown)
        controlsLayout.addSpacing(15)
        controlsLayout.addLayout(resolutionLayout)
        controlsLayout.addLayout(buttonLayout)
        controlsLayout.addStretch()

        # main layout
        MainLayout = QHBoxLayout()
        MainLayout.addWidget(self.preview, stretch=3)
        MainLayout.addLayout(controlsLayout, stretch=1)

        container = QWidget()
        container.setLayout(MainLayout)
        self.setCentralWidget(container)
        self.createMenuBar()
        self.currentImage = None

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        actionOpen = QAction("Open...", self)
        actionSave = QAction("Save...", self)
        actionSaveAs = QAction("Save as...", self)

        fileMenu.addAction(actionOpen)
        fileMenu.addAction(actionSave)
        fileMenu.addAction(actionSaveAs)

        actionSave.triggered.connect(self.saveImage)
        actionSave.setShortcut("Ctrl+S")
        actionSaveAs.triggered.connect(self.saveAsImage)
        actionSaveAs.setShortcut("Ctrl+Shift+S")
        actionOpen.triggered.connect(self.uploadImage)
        actionOpen.setShortcut("Ctrl+O")

        presetsMenu = menuBar.addMenu("&Presets")
        actionVGA = QAction("VGA (256 colors)", self)
        actionVGA.triggered.connect(lambda: self.paletteDropdown.setCurrentIndex(1))
        actionEGA = QAction("EGA (16 colors)", self)
        actionEGA.triggered.connect(lambda: self.paletteDropdown.setCurrentIndex(0))

        presetsMenu.addAction(actionVGA)
        presetsMenu.addAction(actionEGA)

    @Slot()
    def uploadImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", filter="Images (*.jpg *.jpeg, *.png *.bmp)")
        if fileName:
            self.currentImage = fileName
            pixmap = QPixmap(self.currentImage)
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    @Slot()
    def updatePreview(self):
        if not self.currentImage:
            print("No Image Selected")
            return
        targetResolution = self.resolutionSlider.value()
        targetPalette = self.paletteDropdown.currentIndex()
        img = image.readImage(self.currentImage)
        img = image.downscale(img, targetResolution, targetResolution, keepAspectRatio=True)
        match targetPalette:
            case 0:
                img = image.colorProcessing(img,palette=image.EGA_16_color_palette)
            case 1:
                img = image.colorProcessing(img, palette=image.VGA_256_color_palette)
        height, width, channels = img.shape
        result = image.upscale(img, height, width, keepAspectRatio=True)
        height, width, channels = result.shape
        bytesPerLine = channels * width

        QImg = QImage(result.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(QImg)
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    @Slot()
    def saveAsImage(self, setPreferences=False):
        if self.preview.pixmap().isNull():
            print("No Image Selected")
            return
        dir = str(Path(self.currentImage).stem) + "_pixelized"
        filePath, filter = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            dir,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;All Files (*.*)"
        )
        if filePath:
            self.preview.pixmap().save(filePath)
            # save default save directory and format
            if setPreferences:
                settings = QSettings("PixelArtTransformer", "Settings")

                saveDirectory = Path(filePath).parent
                settings.setValue("default_save_directory", saveDirectory)

                saveFormat = Path(filePath).suffix
                settings.setValue("default_save_format", saveFormat)


    @Slot()
    def saveImage(self):
        if not self.currentImage or self.preview.pixmap().isNull():
            print("No Image Selected")
            return
        # read preferences
        settings = QSettings("PixelArtTransformer", "Settings")
        defaultDirectory = settings.value("default_save_directory")
        defaultFormat = settings.value("default_save_format")

        if not defaultDirectory or not defaultFormat:
            self.saveAsImage(setPreferences=True)
            return

        oldFileName = Path(self.currentImage).stem

        newFileName = oldFileName + "_pixelized" + defaultFormat
        fullPath = str(Path(defaultDirectory) / newFileName)

        self.preview.pixmap().save(fullPath)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())