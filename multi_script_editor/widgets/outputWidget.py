from vendor.Qt.QtCore import *
from vendor.Qt.QtWidgets import *
from vendor.Qt.QtGui import *

import os
from managers import context

from widgets.pythonSyntax import syntaxHighLighter
import settingsManager
from widgets.pythonSyntax import design

# font_name = 'Courier'
font_name = 'Consolas'
# font_name = 'Lucida Console'

class outputClass(QTextBrowser):
    def __init__(self):
        super(outputClass, self).__init__()
        self.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont(font_name)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.fs = 14
        self.document().setDefaultFont(QFont(font_name, self.fs, QFont.Monospace))
        metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopWidth(4 * metrics.width(' '))
        self.setMouseTracking(1)
        data = settingsManager.scriptEditorClass().readSettings()
        self.applyHightLighter(data.get('theme'))

    def showMessage(self, msg):
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        cursor.insertText(str(msg)+'\n')
        self.setTextCursor(cursor)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def setTextEditFontSize(self, size):
        style = '''QTextEdit
    {
        font-size: %spx;
    }''' % size
        self.setStyleSheet(style)


    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.delta() > 0:
                self.changeFontSize(True)
            else:
                self.changeFontSize(False)
        # super(outputClass, self).wheelEvent(event)
        QTextBrowser.wheelEvent(self, event)

    def applyHightLighter(self, theme=None, qss=None):
        self.blockSignals(True)
        colors = None
        if theme or not theme =='default':
            colors = design.getColors(theme)
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        st = design.editorStyle(theme)
        self.setStyleSheet(st)
        self.blockSignals(False)

    def changeFontSize(self, up):
        if context == 'hou':
            if up:
                self.fs = min(30, self.fs+1)
            else:
                self.fs = max(8, self.fs - 1)
            self.setTextEditFontSize(self.fs)
        else:
            f = self.font()
            size = f.pointSize()
            if up:
                size = min(30, size+1)
            else:
                size = max(8, size - 1)
            f.setPointSize(size)
            self.setFont(f)

    def wordWrap(self, state):
        if state:
            self.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QTextEdit.NoWrap)

    def set_font(self, font):
        self.setFont(font)

    def render_whitespace(self, state):
        text_option = QTextOption()
        if state:
            text_option.setFlags(QTextOption.ShowTabsAndSpaces)
            self.document().setDefaultTextOption(text_option)
        else:
            self.document().setDefaultTextOption(text_option)
    
    def set_start_font(self, font_d):
        family = font_d.get('family', 'Courier')
        pointSize = font_d.get('pointSize', 10)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)
        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)        
        self.setFont(editor_font)

