import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QLineEdit, QToolButton, QDialog, QMainWindow, \
    QVBoxLayout
from PySide6.QtCore import Slot

class MainWindow(QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Pixel Art Transformer")
        self.setWindowIcon(QIcon("icon.png"))
        #self.setStyleSheet("background-color: rgb(2, 25, 55);")
        self.edit = QLineEdit("Write text here")
        self.button = QPushButton("Click me")
        self.label = QLabel("Hello World")

        self.button.clicked.connect(self.hello)

        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def hello(self):
        print(f"You wrote {self.edit.text()}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()


    window.show()
    sys.exit(app.exec())