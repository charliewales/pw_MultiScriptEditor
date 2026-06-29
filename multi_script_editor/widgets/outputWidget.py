from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFont, QFontMetrics, QTextCursor, QTextOption
from vendor.Qt.QtWidgets import QTextBrowser, QTextEdit

import os
from managers import context

from widgets.pythonSyntax import syntaxHighLighter
from core.settings_model import SettingsModel
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
        default_font = QFont(font_name, self.fs)
        default_font.setStyleHint(QFont.Monospace)
        self.document().setDefaultFont(default_font)
        metrics = QFontMetrics(self.document().defaultFont())
        width = metrics.horizontalAdvance(' ') if hasattr(metrics, 'horizontalAdvance') else metrics.width(' ')
        if hasattr(self, 'setTabStopDistance'):
            self.setTabStopDistance(4 * width)
        else:
            self.setTabStopWidth(4 * width)
        self.setMouseTracking(1)
        data = SettingsModel().read_settings()
        self.applyHightLighter(data.get('theme'))

    def showMessage(self, msg):
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        cursor.insertText(str(msg)+'\n')
        self.setTextCursor(cursor)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def search(self, text=None, case_sensitive=False):
        if text:
            from vendor.Qt.QtGui import QTextDocument
            if not hasattr(self, 'lastSearch'):
                self.lastSearch = [text, 0, case_sensitive]
            
            if text == self.lastSearch[0] and case_sensitive == self.lastSearch[2]:
                self.lastSearch[1] += 1
            else:
                self.lastSearch = [text, 0, case_sensitive]
                
            options = QTextDocument.FindCaseSensitively if case_sensitive else QTextDocument.FindFlags()
            found = self.find(text, options)
            if not found:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Start)
                self.setTextCursor(cursor)
                self.find(text, options)

    def setTextEditFontSize(self, size):
        style = '''QTextEdit
    {
        font-size: %spx;
    }''' % size
        self.setStyleSheet(style)
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)


    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y() if hasattr(event, 'angleDelta') else event.delta()
            if delta > 0:
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
        pointSize = font_d.get('pointSize', 14)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)
        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        self.setFont(editor_font)
