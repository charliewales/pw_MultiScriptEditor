import os, sys, re
from vendor.Qt.QtCore import * 
from vendor.Qt.QtWidgets import * 
from vendor.Qt.QtGui import * 

from multi_script_editor import scriptEditor
import MaxPlus
q3dsmax = QApplication.instance()

class MaxDialogEvents(QObject):
    def eventFilter(self, obj, event):
        import MaxPlus
        if event.type() == QEvent.WindowActivate:
            MaxPlus.CUI.DisableAccelerators()
        elif event.type() == QEvent.WindowDeactivate:
            MaxPlus.CUI.EnableAccelerators()
        return False

def show():
    try:
        qtwindow = MaxPlus.GetQMaxWindow()
    except:
        qtwindow = MaxPlus.GetQMaxMainWindow()
    se = scriptEditor.scriptEditorClass(parent=qtwindow)
    #se.installEventFilter(MaxDialogEvents())
    se.runCommand('import MaxPlus')
    #se.MaxEventFilter = MaxDialogEvents()
    #se.installEventFilter(se.MaxEventFilter)
    se.show()
