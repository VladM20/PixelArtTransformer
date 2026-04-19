import sys

from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QLineEdit, QToolButton, QMainWindow, \
    QHBoxLayout, QWidget, QGraphicsView, QMenuBar
from PySide6.QtCore import Slot

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixel Art Transformer")
        # noinspection PyTypeChecker
        self.resize(QGuiApplication.primaryScreen().availableSize()*3/5)
        self.createMenuBar()

        preview = QLabel("Preview")
        uploadButton = QPushButton("Upload Image")
        startButton = QPushButton("Start")

        layout = QHBoxLayout()
        layout.addWidget(preview)
        layout.addWidget(uploadButton)
        layout.addWidget(startButton)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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

    def hello(self):
        print(f"You wrote {self.edit.text()}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())