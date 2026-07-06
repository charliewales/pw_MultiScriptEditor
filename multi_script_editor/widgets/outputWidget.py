from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFont, QFontMetrics, QTextCursor, QTextDocument
from vendor.Qt.QtWidgets import QTextBrowser, QTextEdit


from widgets.pythonSyntax import syntaxHighLighter
from widgets.pythonSyntax import design
from core.base_text_widget import BaseTextWidgetMixin


font_name = 'monospace'


class outputClass(QTextBrowser, BaseTextWidgetMixin):
    def __init__(self, theme='Multi Script Editor'):
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
        self.applyHightLighter(theme)

    def showMessage(self, msg):
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        cursor.insertText(str(msg)+'\n')
        self.setTextCursor(cursor)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def search(self, text=None, case_sensitive=False):
        if text:
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
        if theme or not theme =='Multi Script Editor':
            colors = design.getColors(theme)
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        st = design.editorStyle(theme)
        self.setStyleSheet(st)
        self.blockSignals(False)
