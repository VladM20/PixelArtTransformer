import sys

from pathlib import Path
from PySide6.QtCore import QSize, Slot

import image_processing as image
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, Qt, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QSpinBox, QMainWindow, \
    QHBoxLayout, QWidget, QFileDialog, QComboBox, QVBoxLayout
from PySide6.QtCore import QSettings

MIN_RESOLUTION = 2
MAX_RESOLUTION = 512

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixel Art Transformer")
        # noinspection PyTypeChecker
        self.resize(QGuiApplication.primaryScreen().availableSize()*3/5)
        
        # preview area
        self.preview = QLabel("<b>No image loaded</b>")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(QSize(400, 300))
        self.preview.setStyleSheet("border: 1px solid gray;")
        self.preview.setPixmap(QPixmap("noimage_nobackground.png"))
        self.noImage = True

        # COLOR SETTINGS
        # palette dropdown
        self.paletteDropdown = QComboBox()
        self.paletteDropdown.addItem("EGA (16 colors)")
        self.paletteDropdown.addItem("VGA (256 colors)")
        self.paletteDropdown.addItem("Custom")
        self.paletteDropdown.currentIndexChanged.connect(self.updatePreview)

        # RESOLUTION SETTINGS
        self.aspectRatio = 1.0
        self.originalAspectRatio = 1.0
        self.originalWidth = 300

        self.originalResolutionLabel = QLabel("Original Image Resolution: ")
        self.originalResolutionLabel.setStyleSheet("color: gray; font-size: 11px;")

        # resolution width slider
        self.resolutionSliderW = QSlider(Qt.Orientation.Horizontal)
        self.resolutionSliderW.setRange(MIN_RESOLUTION, MAX_RESOLUTION)
        self.resolutionSliderW.setValue(100)
        self.resolutionSliderW.sliderReleased.connect(self.updatePreview)

        # resolution height slider
        self.resolutionSliderH = QSlider(Qt.Orientation.Horizontal)
        self.resolutionSliderH.setRange(MIN_RESOLUTION, MAX_RESOLUTION)
        self.resolutionSliderH.setValue(100)
        self.resolutionSliderH.sliderReleased.connect(self.updatePreview)

        labelX = QLabel("X")
        labelX.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # resolution width spinbox
        self.resolutionSpinBoxW = QSpinBox()
        self.resolutionSpinBoxW.setRange(MIN_RESOLUTION, MAX_RESOLUTION)
        self.resolutionSpinBoxW.setValue(100)
        self.resolutionSpinBoxW.editingFinished.connect(self.updatePreview)

        # resolution height spinbox
        self.resolutionSpinBoxH = QSpinBox()
        self.resolutionSpinBoxH.setRange(MIN_RESOLUTION, MAX_RESOLUTION)
        self.resolutionSpinBoxH.setValue(100)
        self.resolutionSpinBoxH.editingFinished.connect(self.updatePreview)

        # locking button
        self.lockRatioButton = QPushButton("Lock Ratio")
        self.lockRatioButton.setCheckable(True)
        self.lockRatioButton.setToolTip("Preserve Aspect Ratio")
        self.lockRatioButton.toggled.connect(self.setLockRatio)

        # restore original aspect ratio button
        self.restoreButton = QPushButton("Restore")
        self.restoreButton.setToolTip("Restore Original Image Resolution")
        self.restoreButton.clicked.connect(self.restoreImage)

        # connecting the resolution controls
        self.resolutionSliderW.valueChanged.connect(self.resolutionSpinBoxW.setValue)
        self.resolutionSpinBoxW.valueChanged.connect(self.resolutionSliderW.setValue)
        self.resolutionSliderH.valueChanged.connect(self.resolutionSpinBoxH.setValue)
        self.resolutionSpinBoxH.valueChanged.connect(self.resolutionSliderH.setValue)

        self.resolutionSliderW.valueChanged.connect(self.syncWidth)

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
        resolutionLayout = QVBoxLayout()
        resolutionLayout.addWidget(QLabel("Input Resolution: "))

        spinboxesLayout = QHBoxLayout()
        spinboxesLayout.addWidget(self.resolutionSpinBoxW)
        spinboxesLayout.addWidget(labelX)
        spinboxesLayout.addWidget(self.resolutionSpinBoxH)
        spinboxesLayout.addWidget(self.lockRatioButton)
        spinboxesLayout.addWidget(self.restoreButton)
        resolutionLayout.addLayout(spinboxesLayout)

        resolutionLayout.addWidget(self.resolutionSliderW)
        resolutionLayout.addWidget(self.resolutionSliderH)

        # all controls layed out vertically
        controlsLayout = QVBoxLayout()
        controlsLayout.addSpacing(15)
        controlsLayout.addWidget(self.originalResolutionLabel)
        controlsLayout.addLayout(resolutionLayout)
        controlsLayout.addWidget(QLabel("Color Palette: "))
        controlsLayout.addWidget(self.paletteDropdown)
        controlsLayout.addStretch()
        controlsLayout.addLayout(buttonLayout)
        controlsLayout.addSpacing(30)

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
        actionOpen = QAction("&Open...", self)
        actionSave = QAction("&Save...", self)
        actionSaveAs = QAction("Save &as...", self)

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
    def restoreImage(self):
        if self.noImage:
            return

        self.preview.setPixmap(QPixmap(self.currentImage).scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    @Slot(int)
    def syncWidth(self, width):
        self.resolutionSliderW.setValue(width)
        self.resolutionSpinBoxW.setValue(width)

        if self.lockRatioButton.isChecked():
            newHeight = int(width / self.aspectRatio)
            newHeight = max(MIN_RESOLUTION, min(newHeight, MAX_RESOLUTION))
            self.resolutionSliderH.setValue(newHeight)

    @Slot(bool)
    def setLockRatio(self, isLocked):
        self.resolutionSliderH.setEnabled(not isLocked)
        self.resolutionSpinBoxH.setEnabled(not isLocked)

        if isLocked:
            height = self.resolutionSpinBoxH.value()
            if height >= MIN_RESOLUTION:
                self.aspectRatio = self.resolutionSpinBoxW.value() / height

        self.lockRatioButton.setChecked(isLocked)

    @Slot()
    def uploadImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", filter="Images (*.jpg *.jpeg, *.png *.bmp)")
        if fileName:
            self.currentImage = fileName
            pixmap = QPixmap(self.currentImage)
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
            self.noImage = False
            self.originalAspectRatio = self.preview.pixmap().width() / self.preview.pixmap().height()
            self.setLockRatio(True)
            self.originalWidth = self.preview.width()
            self.originalResolutionLabel.setText("Original Resolution: " + str(self.preview.pixmap().width()) + "x" + str(self.preview.pixmap().height()))

    @Slot()
    def updatePreview(self):
        if self.noImage:
            print("No Image Selected")
            return
        targetResolution = self.resolutionSliderW.value()
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
        if self.noImage:
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
        if self.noImage:
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