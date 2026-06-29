from vendor.Qt.QtCore import QTimer, Qt, Signal
from vendor.Qt.QtWidgets import QWidget
from widgets import findWidget_UIs as ui

class findWidgetClass(QWidget, ui.Ui_findReplace):
    searchSignal = Signal(str, bool)
    replaceSignal = Signal(list, bool)
    replaceAllSignal = Signal(list, bool)
    def __init__(self, parent):
        super(findWidgetClass, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Tool)
        center = parent.parent().mapToGlobal(parent.geometry().center())
        myGeo = self.geometry()
        myGeo.moveCenter(center)
        self.setGeometry(myGeo)
        self.find_le.setFocus()
        #connect
        self.find_btn.clicked.connect(self.search)
        self.find_le.returnPressed.connect(self.search)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_le.returnPressed.connect(self.replace)
        self.replaceAll_btn.clicked.connect(self.replaceAll)
        
        from vendor.Qt.QtWidgets import QCheckBox
        self.case_cb = QCheckBox("Case Sensitive", self)
        self.gridLayout.addWidget(self.case_cb, 2, 0, 1, 1)
    def setReplaceEnabled(self, state):
        self.replace_le.setEnabled(state)
        self.replace_btn.setEnabled(state)
        self.replaceAll_btn.setEnabled(state)

    def search(self):
        self.searchSignal.emit(self.find_le.text(), self.case_cb.isChecked())
        QTimer.singleShot(10, self.find_le.setFocus)

    def replace(self):
        find = self.find_le.text()
        rep = self.replace_le.text()
        self.replaceSignal.emit([find, rep], self.case_cb.isChecked())
        QTimer.singleShot(10, self.replace_le.setFocus)

    def replaceAll(self):
        find = self.find_le.text()
        rep = self.replace_le.text()
        self.replaceAllSignal.emit([find, rep], self.case_cb.isChecked())
        QTimer.singleShot(10, self.replace_le.setFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super(findWidgetClass, self).keyPressEvent(event)