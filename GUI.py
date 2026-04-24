import sys

from pathlib import Path
from PySide6.QtCore import QSize, Slot, QSettings

import image_processing as image
import video_processing as video
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, Qt, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QSpinBox, QMainWindow, \
    QHBoxLayout, QWidget, QFileDialog, QComboBox, QVBoxLayout, QTabWidget, QMessageBox, QDialog, QLineEdit, \
    QDialogButtonBox, QProgressBar, QStyleFactory

MIN_RESOLUTION = 4
MAX_RESOLUTION = 512
MIN_COLORS = 2
MAX_COLORS = 32000
MAX_SLIDER_COLORS = 256
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi"}

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(QSize(500, 200))
        self.settings = QSettings("PixelArtTransformer", "Settings")

        mainLayout = QVBoxLayout(self)

        directoryLayout = QHBoxLayout()
        directoryLayout.addWidget(QLabel("Default save directory: "))
        self.directoryEdit = QLineEdit()
        self.directoryEdit.setText(str(self.settings.value("default_save_directory")))
        directoryLayout.addWidget(self.directoryEdit)

        browseButton = QPushButton("Browse...")
        browseButton.clicked.connect(self.browseDirectory)
        directoryLayout.addWidget(browseButton)

        formatLayout = QHBoxLayout()
        formatLayout.addWidget(QLabel("Default format: "))
        self.formatDropdown = QComboBox()
        self.formatDropdown.addItems(["png", "jpg", "jpeg", "bmp"])
        savedFormat = self.settings.value("default_save_format")
        if savedFormat is None:
            savedFormat = "png"
        self.formatDropdown.setCurrentText(savedFormat)
        formatLayout.addWidget(self.formatDropdown)
        formatLayout.addStretch()
        # noinspection PyTypeChecker
        ButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        ButtonBox.accepted.connect(self.saveSettings)
        ButtonBox.rejected.connect(self.reject)

        mainLayout.addLayout(directoryLayout)
        mainLayout.addLayout(formatLayout)
        mainLayout.addStretch()
        mainLayout.addWidget(ButtonBox)

    @Slot()
    def saveSettings(self):
        self.settings.setValue("default_save_directory", self.directoryEdit.text())
        self.settings.setValue("default_save_format", self.formatDropdown.currentText())
        self.accept()

    @Slot()
    def browseDirectory(self):
        options = QFileDialog.Option.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.directoryEdit.text(), options=options)
        if directory:
            self.directoryEdit.setText(directory)

# TODO create UI for video processing

# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
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
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)

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
        self.resolutionSpinBoxW.valueChanged.connect(self.syncResolutionControls)
        # resolution height spinbox
        self.resolutionSpinBoxH = QSpinBox()
        self.resolutionSpinBoxH.setRange(MIN_RESOLUTION, 10*MAX_RESOLUTION)
        self.resolutionSpinBoxH.setValue(100)
        self.resolutionSpinBoxH.valueChanged.connect(self.syncResolutionControls)

        resolutionLayout.addWidget(self.resolutionSpinBoxW)
        labelX = QLabel("X")
        labelX.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resolutionLayout.addWidget(labelX)
        resolutionLayout.addWidget(self.resolutionSpinBoxH)

        # locking button
        self.lockRatioButton = QPushButton("🔒")
        self.lockRatioButton.setCheckable(True)
        self.lockRatioButton.setChecked(True)
        self.lockRatioButton.setToolTip("Preserve Aspect Ratio")
        self.lockRatioButton.toggled.connect(self.setLockRatio)

        # restore original aspect ratio button
        self.restoreButton = QPushButton("Restore")
        self.restoreButton.setToolTip("Restore Original Image Resolution")
        self.restoreButton.clicked.connect(self.restoreImage)
        resolutionLayout.addWidget(self.lockRatioButton)
        resolutionLayout.addWidget(self.restoreButton)
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

        # Upload Video button
        uploadVideoButton =QPushButton("Upload Video")
        uploadVideoButton.clicked.connect(self.uploadVideo)

        # Update Preview button
        processButton = QPushButton("Update Preview")
        processButton.clicked.connect(self.updatePreview)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveAs)

        # buttons layed out horizontally
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(uploadButton)
        buttonLayout.addWidget(uploadVideoButton)
        buttonLayout.addWidget(processButton)
        buttonLayout.addWidget(saveButton)

        # all controls layed out vertically
        controlsLayout = QVBoxLayout()
        # original image info
        originalInfoLayout = QHBoxLayout()
        originalInfoLayout.addWidget(self.originalResolutionLabel)
        controlsLayout.addLayout(originalInfoLayout)

        controlsLayout.addWidget(QLabel("Color Palette: "))
        controlsLayout.addWidget(self.paletteDropdown)
        controlsLayout.addWidget(self.tabs)

        controlsLayout.addStretch()
        controlsLayout.addLayout(buttonLayout)
        controlsLayout.addSpacing(30)

        # main layout
        MainLayout = QHBoxLayout()
        previewLayout = QVBoxLayout()
        previewLayout.addWidget(self.preview)
        previewLayout.addWidget(self.progressBar)
        MainLayout.addLayout(previewLayout, stretch=3)
        MainLayout.addLayout(controlsLayout, stretch=1)

        container = QWidget()
        container.setLayout(MainLayout)
        self.setCentralWidget(container)
        self.createMenuBar()
        self.currentImage = None

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        actionOpen = QAction("&Open image...", self)
        actionOpenVideo = QAction("Open video...", self)
        actionSave = QAction("&Save...", self)
        actionSaveAs = QAction("Save &as...", self)

        fileMenu.addAction(actionOpen)
        fileMenu.addAction(actionOpenVideo)
        fileMenu.addAction(actionSave)
        fileMenu.addAction(actionSaveAs)

        actionSave.triggered.connect(self.save)
        actionSave.setShortcut("Ctrl+S")
        actionSaveAs.triggered.connect(self.saveAs)
        actionSaveAs.setShortcut("Ctrl+Shift+S")
        actionOpen.triggered.connect(self.uploadImage)
        actionOpen.setShortcut("Ctrl+O")
        actionOpenVideo.triggered.connect(self.uploadVideo)
        actionOpenVideo.setShortcut("Ctrl+Shift+O")

        presetsMenu = menuBar.addMenu("&Presets")
        actionVGA = QAction("VGA (256 colors)", self)
        actionVGA.triggered.connect(lambda: self.paletteDropdown.setCurrentIndex(1))
        actionEGA = QAction("EGA (16 colors)", self)
        actionEGA.triggered.connect(lambda: self.paletteDropdown.setCurrentIndex(0))

        presetsMenu.addAction(actionVGA)
        presetsMenu.addAction(actionEGA)

        preferencesMenu = menuBar.addMenu("&Preferences")
        preferencesAction = QAction("&Preferences...", self)
        preferencesAction.triggered.connect(self.openPreferences)
        preferencesMenu.addAction(preferencesAction)

    @Slot()
    def openPreferences(self):
        dialog = PreferencesDialog(self)
        dialog.exec()

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
        pixmap = self.QPixmapFromAny()
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.resolutionSpinBoxW.setValue(pixmap.width())
        self.resolutionSpinBoxH.setValue(pixmap.height())

    def QPixmapFromAny(self):
        extension = Path(self.currentImage).suffix.lower()

        if extension in VIDEO_EXTENSIONS:
            img = video.getFirstValidFrame(self.currentImage)
            if img is None:
                return

            height, width, channels = img.shape
            bytesPerLine = channels * width

            pixmap = QPixmap.fromImage(QImage(img.data, width, height, bytesPerLine, QImage.Format.Format_RGB888))
        else:
            pixmap = QPixmap(self.currentImage)

        return pixmap

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
            if self.lockRatioButton.isChecked():
                self.resolutionSpinBoxH.blockSignals(True)
                value = int(self.resolutionSpinBoxW.value() / self.aspectRatio)
                self.resolutionSpinBoxH.setValue(value)
                self.resolutionSpinBoxH.blockSignals(False)
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
            self.uploadPreview()

    @Slot()
    def uploadVideo(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", filter="Video Files (*.mkv *.avi *.mp4)")
        if fileName:
            self.currentImage = fileName
            self.uploadPreview()

    # sets UI preview image based on self.currentImage, which needs to be set before calling this
    def uploadPreview(self):
        pixmap = self.QPixmapFromAny()
        # set aspect ratio
        self.originalAspectRatio = pixmap.width() / pixmap.height()
        self.aspectRatio = self.originalAspectRatio
        # set preview image
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.noImage = False

        # set controls UI
        self.originalResolutionLabel.setText("Original Resolution: " + str(pixmap.width()) + "x" + str(pixmap.height()))
        self.lockRatioButton.blockSignals(True)
        self.lockRatioButton.setChecked(True)  # blocking the lock ratio button from calling setLockRatio and
        self.lockRatioButton.blockSignals(False)  # deleting the aspect ratio calculated above

        self.setLockRatio(True)

    def getParamsFromUI(self):
        targetResolutionWidth = 0
        targetResolutionHeight = 0
        targetPalette = str(self.paletteDropdown.currentText()).strip().lower()
        targetColors = 0
        tab = self.tabs.currentIndex()

        match targetPalette:
            case "ega (16 colors)":
                targetPalette = image.EGA_16_color_palette
            case "vga (256 colors)":
                targetPalette = image.VGA_256_color_palette
            case _:
                targetPalette = None
                targetColors = self.colorSlider.value()
        #print("getParams: " + str(targetPalette))

        match tab:
            case 0: # basic tab
                targetResolutionWidth = self.resolutionSlider.value()
                targetResolutionHeight = int(self.resolutionSlider.value() / self.aspectRatio)

            case 1: # advanced tab
                targetResolutionWidth = self.resolutionSpinBoxW.value()
                targetResolutionHeight = self.resolutionSpinBoxH.value()
                targetColors = self.colorSpinBox.value()

        return targetResolutionWidth, targetResolutionHeight, targetPalette, targetColors

    @Slot()
    def updatePreview(self):
        if self.noImage:
            #print("No Image Selected")
            return None
        targetResolutionWidth, targetResolutionHeight, targetPalette, targetColors = self.getParamsFromUI()
        fileType = Path(self.currentImage).suffix.lower()
        if fileType in VIDEO_EXTENSIONS:
            img = video.getFirstValidFrame(self.currentImage)
        else:
            img = image.readImage(self.currentImage)

        height, width, channels = img.shape
        img = image.downscale(img, targetResolutionWidth, targetResolutionHeight, keepAspectRatio=self.lockRatioButton.isChecked())
        img = image.colorProcessing(img,palette=targetPalette, maxColors=targetColors)
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
            #print("No Image Selected")
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
            #print("No Image Selected")
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
            clickedButton = self.fileExistsMsgBox(newFileName)

            if clickedButton == "unique":
                    counter = 1
                    while True:
                        testPath = Path(defaultDirectory) / (newFileName + "_" + str(counter) + "." + defaultFormat)
                        if not testPath.exists():
                            fullPath = testPath
                            break
                        counter += 1
            elif clickedButton == "cancel":
                return

        self.updatePreview().save(str(fullPath))

    def startVideoProcessing(self,outputPath):
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.toggleControls(False)

        targetResolutionWidth, targetResolutionHeight, targetPalette, targetColors = self.getParamsFromUI()

        self.worker = video.VideoProcessing(self.currentImage, outputPath, targetResolutionWidth, targetResolutionHeight, targetPalette, targetColors)
        self.worker.progress.connect(self.progressBar.setValue)
        self.worker.finished.connect(self.onVideoFinished)
        self.worker.error.connect(self.onVideoError)
        self.worker.start()

    @Slot()
    def saveAsVideo(self, setPreferences=False):
        if self.noImage:
            return
        dir = str(Path(self.currentImage).stem) + "_pixelized"
        filePath, filter = QFileDialog.getSaveFileName(
            self,
            "Save Video As",
            dir,
            "MP4 (*.mp4);;All Files (*.*)"
        )

        self.startVideoProcessing(filePath)

        if filePath:

            # save default save directory and format
            if setPreferences:
                settings = QSettings("PixelArtTransformer", "Settings")

                saveDirectory = Path(filePath).parent
                settings.setValue("default_save_directory", saveDirectory)

    @Slot()
    def saveVideo(self):
        if self.noImage:
            return
        # read preferences
        settings = QSettings("PixelArtTransformer", "Settings")
        defaultDirectory = settings.value("default_save_directory")
        defaultFormat = settings.value("default_save_format")

        if not defaultDirectory or not defaultFormat:
            self.saveAsVideo(setPreferences=True)
            return

        oldFileName = Path(self.currentImage).stem

        newFileNameNoExtension = oldFileName + "_pixelized"
        newFileName = newFileNameNoExtension + ".mp4"

        fullPath = Path(defaultDirectory) / newFileName
        if fullPath.exists():
            clickedButton = self.fileExistsMsgBox(newFileName)

            if clickedButton == "unique":
                    counter = 1
                    while True:
                        testPath = Path(defaultDirectory) / (newFileNameNoExtension + "_" + str(counter) + "." + "mp4")
                        if not testPath.exists():
                            fullPath = testPath
                            break
                        counter += 1
            elif clickedButton == "cancel":
                return

        self.startVideoProcessing(fullPath)

    def fileExistsMsgBox(self, newFileName):
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle("File Already Exists")
        msgBox.setText("There is already a file named " + newFileName + ". What do you want to do?")

        msgBox.addButton("Overwrite existing", QMessageBox.ButtonRole.DestructiveRole)
        uniqueButton = msgBox.addButton("Save with new name", QMessageBox.ButtonRole.AcceptRole)
        cancelButton = msgBox.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        msgBox.exec()
        clickedButton = msgBox.clickedButton()
        if clickedButton == uniqueButton:
            return "unique"
        elif clickedButton == cancelButton:
            return "cancel"
        else:
            return "overwrite"

    @Slot()
    def toggleControls(self, state):
        self.paletteDropdown.setEnabled(state)
        self.tabs.setEnabled(state)

    @Slot(str)
    def onVideoFinished(self, path):
        self.progressBar.setVisible(False)
        self.toggleControls(True)

        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.setWindowTitle("Video Processing")
        msgBox.setText("Video saved successfully. Full path: " + path)
        msgBox.exec()

    @Slot(str)
    def onVideoError(self, error):
        self.progressBar.setVisible(True)
        self.toggleControls(True)
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle("Video Processing Error")
        msgBox.setText("Error during video processing. Full message:\n\n" + error)
        msgBox.exec()

    def save(self):
        if self.noImage:
            return
        if Path(self.currentImage).suffix.lower() in VIDEO_EXTENSIONS:
            self.saveVideo()
        else:
            self.saveImage()

    @Slot()
    def saveAs(self):
        if self.noImage:
            return
        if Path(self.currentImage).suffix.lower() in VIDEO_EXTENSIONS:
            self.saveAsVideo()
        else:
            self.saveAsImage()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())