import os

from core.base_text_widget import BaseTextWidgetMixin
from core.settings_model import SettingsModel
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QColor, QFont, QFontMetrics, QTextCursor, QTextDocument
from vendor.Qt.QtWidgets import QPlainTextEdit, QTextEdit
from widgets.pythonSyntax import design, syntaxHighLighter

font_name = 'monospace'


class outputClass(BaseTextWidgetMixin, QPlainTextEdit):
    def __init__(self, theme='Multi Script Editor'):
        super(outputClass, self).__init__()
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setReadOnly(True)
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
        self.setAcceptDrops(True)
        self._highlight_word_cache = None
        self.applyHightLighter(theme)
        self.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            if text and '\u2029' not in text and text.strip():
                self.highlight_word(text)
            else:
                self.highlight_word("")
        else:
            self.highlight_word("")

    def _highlight_occurrences_enabled(self):
        action = getattr(
            self.window(),
            'highlightAllOccurrences_act',
            None,
        )
        if action is not None:
            return action.isChecked()
        data = SettingsModel().read_settings() or {}
        return data.get('highlight_all_occurrences', True)

    def highlight_word(self, word):
        doc = self.document()
        highlight_all = (
            bool(word)
            and self._highlight_occurrences_enabled()
        )
        cache_key = (word, doc.revision(), highlight_all)
        if cache_key == self._highlight_word_cache:
            return

        selections = []
        if highlight_all:
            cursor = QTextCursor(doc)
            while True:
                cursor = doc.find(word, cursor)
                if cursor.isNull():
                    break
                sel = QTextEdit.ExtraSelection()
                sel.cursor = cursor
                sel.format.setBackground(QColor(128, 128, 255, 180))
                selections.append(sel)
        self.setExtraSelections(selections)
        self._highlight_word_cache = cache_key

    def showMessage(self, msg):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(str(msg)+'\n')
        self.setTextCursor(cursor)
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
        style = '''QPlainTextEdit
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
        QPlainTextEdit.wheelEvent(self, event)

    def applyHightLighter(self, theme=None, qss=None):
        self.blockSignals(True)
        colors = None
        if theme or not theme =='Multi Script Editor':
            colors = design.getColors(theme)
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self.document(), colors)
        st = design.editorStyle(theme)
        self.setStyleSheet(st)
        self.blockSignals(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QPlainTextEdit.dragEnterEvent(self, event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QPlainTextEdit.dragMoveEvent(self, event)

    def dragLeaveEvent(self, event):
        event.accept()
        QPlainTextEdit.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            main_window = self.window()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        if hasattr(main_window, 'openRecentFile'):
                            main_window.openRecentFile(file_path)
            return
        QPlainTextEdit.dropEvent(self, event)
