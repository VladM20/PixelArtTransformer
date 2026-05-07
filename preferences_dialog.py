import re

from PySide6.QtCore import QSize, QSettings, Slot
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, \
    QDialogButtonBox, QFileDialog, QGroupBox, QTableWidget, QHeaderView, QAbstractItemView, QInputDialog, QMessageBox, \
    QTableWidgetItem


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(QSize(600, 400))
        self.settings = QSettings("PixelArtTransformer", "Settings")

        self.localCustomPalettes = self.settings.value("custom_palettes")
        if not isinstance(self.localCustomPalettes, dict):
            self.localCustomPalettes = {}

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

        palettesGroup = QGroupBox("Custom Palettes")
        palettesLayout = QHBoxLayout(palettesGroup)

        self.paletteTable = QTableWidget(0, 2)
        self.paletteTable.setHorizontalHeaderLabels(["Name", "Colors"])
        self.paletteTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.paletteTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.paletteTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.paletteTable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.paletteTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.paletteTable.itemSelectionChanged.connect(self.onTableSelectionChanged)

        tableButtonLayout = QVBoxLayout()
        self.addButton = QPushButton("Add...")
        self.addButton.clicked.connect(self.addPalette)

        self.removeButton = QPushButton("Remove")
        self.removeButton.setEnabled(False)
        self.removeButton.clicked.connect(self.removePalette)

        self.removeAllButton = QPushButton("Remove All")
        self.removeAllButton.clicked.connect(self.removeAllPalettes)

        tableButtonLayout.addWidget(self.addButton)
        tableButtonLayout.addWidget(self.removeButton)
        tableButtonLayout.addStretch()
        tableButtonLayout.addWidget(self.removeAllButton)

        palettesLayout.addWidget(self.paletteTable)
        palettesLayout.addLayout(tableButtonLayout)

        # noinspection PyTypeChecker
        ButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        ButtonBox.accepted.connect(self.saveSettings)
        ButtonBox.rejected.connect(self.reject)

        mainLayout.addLayout(directoryLayout)
        mainLayout.addLayout(formatLayout)
        mainLayout.addWidget(palettesGroup)
        mainLayout.addStretch()
        mainLayout.addWidget(ButtonBox)

        self.refreshTable()

    @Slot()
    def saveSettings(self):
        self.settings.setValue("default_save_directory", self.directoryEdit.text())
        self.settings.setValue("default_save_format", self.formatDropdown.currentText())
        self.settings.setValue("custom_palettes", self.localCustomPalettes)
        self.accept()

    @Slot()
    def browseDirectory(self):
        options = QFileDialog.Option.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.directoryEdit.text(), options=options)
        if directory:
            self.directoryEdit.setText(directory)

    @Slot()
    def onTableSelectionChanged(self):
        if len(self.paletteTable.selectedItems()) != 0:
            self.removeButton.setEnabled(True)

    @Slot()
    def addPalette(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select Palette File", "",
                                                  "Palette Files (*.hex *.csv);;All Files (*.*)")

        if filePath:
            name, ok = QInputDialog.getText(self, "Palette Name", "Enter a name for this palette:")
            if ok and name.strip():
                name = name.strip()
                if name in self.localCustomPalettes:
                    QMessageBox.warning(self, "Error", "A palette with this name already exists.")
                    return

                try:
                    with  open(filePath, "r") as file:
                        content = file.read()

                        hex_colors = re.findall(r"#?(?:[A-Fa-f0-9]{3}){1,2}\b", content)

                        if hex_colors:
                            self.localCustomPalettes[name] = hex_colors
                            self.refreshTable()
                        else:
                            QMessageBox.warning(self, "Error", "No valid hex colors found in this file.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")

    @Slot()
    def removePalette(self):
        selectedItems = self.paletteTable.selectedItems()
        if not selectedItems:
            return

        row = selectedItems[0].row()
        paletteName = self.paletteTable.item(row, 0).text()

        if paletteName in self.localCustomPalettes:
            del self.localCustomPalettes[paletteName]
            self.refreshTable()

    @Slot()
    def removeAllPalettes(self):
        if not self.localCustomPalettes:
            return
        reply = QMessageBox.question(self, "Remove All", "Are you sure you want to remove all palettes? This action cannot be undone.",
                                     QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            self.localCustomPalettes.clear()
            self.refreshTable()

    def refreshTable(self):
        self.paletteTable.setRowCount(0)
        for name, colors in self.localCustomPalettes.items():
            row = self.paletteTable.rowCount()
            self.paletteTable.insertRow(row)
            self.paletteTable.setItem(row, 0, QTableWidgetItem(name))
            self.paletteTable.setItem(row, 1, QTableWidgetItem(str(len(colors))))