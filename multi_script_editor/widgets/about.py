import os

import icons
from docs.constants import TESTED_TEXT
from vendor.Qt.QtCore import QSize, Qt
from vendor.Qt.QtGui import QIcon, QPixmap
from vendor.Qt.QtWidgets import QDialog
from widgets import about_UIs


class aboutClass(QDialog, about_UIs.Ui_Dialog):
    def __init__(self, parent):
        super(aboutClass, self).__init__(parent)
        self.setupUi(self)
        if hasattr(parent, 'theme_font'):
            self.setStyleSheet(parent.styleSheet() + "\n* { font-family: '%s'; }" % parent.theme_font.family())
        self.title_lb.setText(self.title_lb.text()+str(("\n".join([d.strip() for d in parent.ver.split("·")]))))
        self.text_link_lb.setText(text)
        self.icon_lb.setPixmap(QPixmap(icons.icons['pw']).scaled(60,60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.donate_btn.setMinimumHeight(35)
        self.donate_btn.setIconSize(QSize(24,24))
        self.donate_btn.setIcon(QIcon(icons.icons['donate']))
        self.donate_btn.clicked.connect(lambda :parent.openLink('donate'))
        # self.donate_btn.hide()
        self.textBrowser.setPlainText(TESTED_TEXT)


text = '''Paul Winex 2018
Any question or bug report: paulwinex@gmail.com

Carlos Rico Adega 2026 (Python 3, PySide2/6)
Any question or bug report: carlos.rico.3d@gmail.com
'''