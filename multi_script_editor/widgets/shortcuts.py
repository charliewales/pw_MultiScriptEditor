import sys

from docs.constants import SHORTCUTS_TEXT
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtWidgets import QDialog, QHeaderView, QTableWidgetItem
from widgets import shortcuts_UIs


class shortcutsClass(QDialog, shortcuts_UIs.Ui_Dialog):
    def __init__(self, parent):
        super(shortcutsClass, self).__init__(parent)
        self.setupUi(self)
        if hasattr(parent, 'theme_font'):
            self.setStyleSheet(parent.styleSheet() + "\n* { font-family: '%s'; }" % parent.theme_font.family())
        if sys.version_info.major >= 3:
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            self.table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Action', 'Shortcut'])
        self.read()

    def read(self):
        self.label.hide()
        lines = SHORTCUTS_TEXT.strip().split('\n')
        for i, line in enumerate(lines):
            self.table.insertRow(self.table.rowCount())
            description, shortcut = line.split('>')
            item = QTableWidgetItem(description)
            self.table.setItem(i, 0, item)
            item.setFlags(Qt.ItemIsEnabled)
            item = QTableWidgetItem(shortcut.strip())
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, item)
