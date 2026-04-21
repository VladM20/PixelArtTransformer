import sys

from pathlib import Path
from PySide6.QtCore import QSize, Slot

import image_processing as image
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, Qt, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QSpinBox, QMainWindow, \
    QHBoxLayout, QWidget, QFileDialog, QComboBox, QVBoxLayout, QTabWidget, QMessageBox
from PySide6.QtCore import QSettings

MIN_RESOLUTION = 4
MAX_RESOLUTION = 512
MIN_COLORS = 2
MAX_COLORS = 32000
MAX_SLIDER_COLORS = 256

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
        self.paletteDropdown.currentIndexChanged.connect(self.showColorControls)

        # RESOLUTION SETTINGS
        self.aspectRatio = 1.0
        self.originalAspectRatio = 1.0
        self.originalWidth = 300

        self.originalResolutionLabel = QLabel("Original Image Resolution: ")
        self.originalResolutionLabel.setStyleSheet("color: gray; font-size: 11px;")
        self.originalColorLabel = QLabel()
        self.originalColorLabel.setStyleSheet("color: gray; font-size: 11px;")

        # TAB SETTINGS
        self.tabs = QTabWidget()

        # BASIC TAB
        basicTab = QWidget()
        basicLayout = QVBoxLayout(basicTab)
        # resolution
        basicLayout.addWidget(QLabel("Quality: "))
        self.resolutionSlider = QSlider(Qt.Orientation.Horizontal)
        self.resolutionSlider.setRange(MIN_RESOLUTION, MAX_RESOLUTION)
        self.resolutionSlider.setValue(100)
        self.resolutionSlider.sliderReleased.connect(self.syncResolutionControls)
        basicLayout.addWidget(self.resolutionSlider)
        # colors
        self.basicColorWidget = QWidget()
        basicColorLayout = QVBoxLayout(self.basicColorWidget)
        basicColorLayout.addWidget(QLabel("Number of colors: "))
        self.colorSlider = QSlider(Qt.Orientation.Horizontal)
        self.colorSlider.setRange(MIN_COLORS, MAX_SLIDER_COLORS)
        self.colorSlider.setValue(16)
        self.colorSlider.sliderReleased.connect(self.syncColorControls)
        basicColorLayout.addWidget(self.colorSlider)

        self.basicColorWidget.setEnabled(False)
        basicLayout.addWidget(self.basicColorWidget)
        basicLayout.addStretch()

        # ADVANCED TAB
        advancedTab = QWidget()
        advancedLayout = QVBoxLayout(advancedTab)
        # resolution
        advancedLayout.addWidget(QLabel("Resolution: "))
        resolutionLayout = QHBoxLayout()
        # resolution width spinbox
        self.resolutionSpinBoxW = QSpinBox()
        self.resolutionSpinBoxW.setRange(MIN_RESOLUTION, 10*MAX_RESOLUTION)
        self.resolutionSpinBoxW.setValue(100)
        self.resolutionSpinBoxW.editingFinished.connect(self.syncResolutionControls)
        # resolution height spinbox
        self.resolutionSpinBoxH = QSpinBox()
        self.resolutionSpinBoxH.setRange(MIN_RESOLUTION, 10*MAX_RESOLUTION)
        self.resolutionSpinBoxH.setValue(100)
        self.resolutionSpinBoxH.editingFinished.connect(self.syncResolutionControls)

        resolutionLayout.addWidget(self.resolutionSpinBoxW)
        labelX = QLabel("X")
        labelX.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resolutionLayout.addWidget(labelX)
        resolutionLayout.addWidget(self.resolutionSpinBoxH)
        advancedLayout.addLayout(resolutionLayout)
        # color
        self.advancedColorWidget = QWidget()
        advancedColorLayout = QVBoxLayout(self.advancedColorWidget)
        self.colorSpinBox = QSpinBox()
        self.colorSpinBox.setRange(MIN_COLORS, MAX_COLORS)
        self.colorSpinBox.setValue(16)
        self.colorSpinBox.editingFinished.connect(self.syncColorControls)
        advancedColorLayout.addWidget(self.colorSpinBox)

        self.advancedColorWidget.setEnabled(False)
        advancedLayout.addWidget(self.advancedColorWidget)
        advancedLayout.addStretch()

        self.tabs.addTab(basicTab, "Basic")
        self.tabs.addTab(advancedTab, "Advanced")

        # buttons
        # Upload Image button
        uploadButton = QPushButton("Upload Image")
        uploadButton.clicked.connect(self.uploadImage)

        # Update Preview button
        processButton = QPushButton("Update Preview")
        processButton.clicked.connect(self.updatePreview)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveAsImage)

        # locking button
        self.lockRatioButton = QPushButton("Lock Ratio")
        self.lockRatioButton.setCheckable(True)
        self.lockRatioButton.setChecked(True)
        self.lockRatioButton.setToolTip("Preserve Aspect Ratio")
        self.lockRatioButton.toggled.connect(self.setLockRatio)

        # restore original aspect ratio button
        self.restoreButton = QPushButton("Restore")
        self.restoreButton.setToolTip("Restore Original Image Resolution")
        self.restoreButton.clicked.connect(self.restoreImage)

        # buttons layed out horizontally
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(uploadButton)
        buttonLayout.addWidget(processButton)
        buttonLayout.addWidget(saveButton)

        # all controls layed out vertically
        controlsLayout = QVBoxLayout()
        # original image info
        originalInfoLayout = QHBoxLayout()
        originalInfoLayout.addWidget(self.originalResolutionLabel)
        originalInfoLayout.addWidget(self.originalColorLabel)
        controlsLayout.addLayout(originalInfoLayout)

        controlsLayout.addWidget(QLabel("Color Palette: "))
        controlsLayout.addWidget(self.paletteDropdown)
        controlsLayout.addWidget(self.tabs)

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

    @Slot(int)
    def showColorControls(self):
        isCustom = (self.paletteDropdown.currentIndex() == 2)
        self.basicColorWidget.setEnabled(isCustom)
        self.advancedColorWidget.setEnabled(isCustom)
        self.updatePreview()

    @Slot()
    def restoreImage(self):
        if self.noImage:
            return
        pixmap = QPixmap(self.currentImage)
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.resolutionSpinBoxW.setValue(pixmap.width())
        self.resolutionSpinBoxH.setValue(pixmap.height())

    @Slot(int)
    def syncColorControls(self):
        if self.sender() == self.colorSlider:
            self.colorSpinBox.blockSignals(True)
            self.colorSpinBox.setValue(self.colorSlider.value())
            self.colorSpinBox.blockSignals(False)
        if self.sender() == self.colorSpinBox:
            self.colorSlider.blockSignals(True)
            value = min(MAX_SLIDER_COLORS, self.colorSpinBox.value())
            self.colorSlider.setValue(value)
            self.colorSlider.blockSignals(False)
        self.updatePreview()

    @Slot(int)
    def syncResolutionControls(self):
        if self.sender() == self.resolutionSlider:
            self.resolutionSpinBoxW.blockSignals(True)
            self.resolutionSpinBoxW.setValue(self.resolutionSlider.value())
            self.resolutionSpinBoxW.blockSignals(False)

            self.resolutionSpinBoxH.blockSignals(True)
            self.resolutionSpinBoxH.setValue(int(self.resolutionSlider.value() / self.aspectRatio))
            self.resolutionSpinBoxH.blockSignals(False)
        if self.sender() == self.resolutionSpinBoxW:
            self.resolutionSlider.blockSignals(True)
            value = max(MAX_RESOLUTION, self.resolutionSpinBoxW.value())
            self.resolutionSlider.setValue(value)
            self.resolutionSlider.blockSignals(False)
        self.updatePreview()


    @Slot(bool)
    def setLockRatio(self, isLocked):
        self.resolutionSpinBoxH.setEnabled(not isLocked)

        if isLocked and self.sender() == self.lockRatioButton:
            height = self.resolutionSpinBoxH.value()
            if height >= MIN_RESOLUTION:
                self.aspectRatio = self.resolutionSpinBoxW.value() / height

    @Slot()
    def uploadImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", filter="Images (*.jpg *.jpeg, *.png *.bmp)")
        if fileName:
            self.currentImage = fileName
            pixmap = QPixmap(self.currentImage)
            # set aspect ratio
            self.originalAspectRatio = pixmap.width() / pixmap.height()
            self.aspectRatio = self.originalAspectRatio
            # set preview image
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
            self.noImage = False

            # set controls UI
            self.originalResolutionLabel.setText("Original Resolution: " + str(pixmap.width()) + "x" + str(pixmap.height()))
            self.originalColorLabel.setText(str(pixmap.depth()) + "-bit color depth")
            self.lockRatioButton.blockSignals(True)
            self.lockRatioButton.setChecked(True)       # blocking the lock ratio button from calling setLockRatio and
            self.lockRatioButton.blockSignals(False)    # deleting the aspect ratio calculated above

            self.setLockRatio(True)

    @Slot()
    def updatePreview(self):
        if self.noImage:
            print("No Image Selected")
            return None
        targetResolutionWidth = 0
        targetResolutionHeight = 0
        targetPalette = self.paletteDropdown.currentIndex()
        targetColors = 0
        tab = self.tabs.currentIndex()
        match tab:
            case 0: # basic tab
                targetResolutionWidth = self.resolutionSlider.value()
                targetColors = self.colorSlider.value()
            case 1: # advanced tab
                targetResolutionWidth = self.resolutionSpinBoxW.value()
                targetResolutionHeight = self.resolutionSpinBoxH.value()
                targetColors = self.colorSpinBox.value()

        img = image.readImage(self.currentImage)
        height, width, channels = img.shape
        img = image.downscale(img, targetResolutionWidth, targetResolutionHeight, keepAspectRatio=self.lockRatioButton.isChecked())
        match targetPalette:
            case 0:
                img = image.colorProcessing(img,palette=image.EGA_16_color_palette, maxColors=None)
            case 1:
                img = image.colorProcessing(img, palette=image.VGA_256_color_palette, maxColors=None)
            case 2:
                img = image.colorProcessing(img, palette=None, maxColors=targetColors)

        result = image.upscale(img, width, height, keepAspectRatio=self.lockRatioButton.isChecked())
        height, width, channels = result.shape
        bytesPerLine = channels * width

        QImg = QImage(result.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(QImg)
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
        return QImg

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
            self.updatePreview().save(str(filePath))
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
        fullPath = Path(defaultDirectory) / newFileName

        if fullPath.exists():
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Icon.Warning)
            msgBox.setWindowTitle("File Already Exists")
            msgBox.setText("There is already a file named " + newFileName + ". What do you want to do?")

            overwriteButton = msgBox.addButton("Overwrite existing", QMessageBox.ButtonRole.DestructiveRole)
            uniqueButton = msgBox.addButton("Save with new name", QMessageBox.ButtonRole.AcceptRole)
            cancelButton = msgBox.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

            msgBox.exec()
            clickedButton = msgBox.clickedButton()

            if clickedButton == uniqueButton:
                    counter = 1
                    while True:
                        testPath = Path(defaultDirectory) / (newFileName + "_" + str(counter) + defaultFormat)
                        if not testPath.exists():
                            fullPath = testPath
                            break
                        counter += 1
            elif clickedButton == cancelButton:
                return

        self.updatePreview().save(str(fullPath))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())