from vendor.Qt.QtCore import * 
from vendor.Qt.QtWidgets import * 
from vendor.Qt.QtGui import * 
import icons
from widgets import about_UIs
import os

class aboutClass(QDialog, about_UIs.Ui_Dialog):
    def __init__(self, parent):
        super(aboutClass, self).__init__(parent)
        self.setupUi(self)
        self.title_lb.setText(self.title_lb.text()+str(parent.ver))
        self.text_link_lb.setText(text)
        self.icon_lb.setPixmap(QPixmap(icons.icons['pw']).scaled(60,60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.donate_btn.setMinimumHeight(35)
        self.donate_btn.setIconSize(QSize(24,24))
        self.donate_btn.setIcon(QIcon(icons.icons['donate']))
        self.donate_btn.clicked.connect(lambda :parent.openLink('donate'))
        self.donate_btn.hide()
        testedFile = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tested.txt')
        if os.path.exists(testedFile):
            outText = open(testedFile).read()
            self.textBrowser.setPlainText(outText)


text = '''Paul Winex 2018
Any question or bug report: paulwinex@gmail.com

Carlos Rico Adega 2023 (v4.1.3, Python 2&3)
Any question or bug report: carlos.rico.3d@gmail.com
'''