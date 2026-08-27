from multi_script_editor import managers
from vendor.Qt.QtCore import QSize, Qt, QTimer
from vendor.Qt.QtGui import QBrush, QColor, QFont, QFontMetrics
from vendor.Qt.QtWidgets import QApplication, QLabel, QListWidget, QListWidgetItem

from .outline_utils import get_symbol_type_icon
from .pythonSyntax import design


_COMPLETION_SYMBOL_TYPES = {
    'class': 'class',
    'function': 'function',
    'method': 'method',
    'module': 'constant',
    'keyword': 'constant',
    'instance': 'variable',
    'param': 'variable',
    'path': 'variable',
    'property': 'variable',
    'statement': 'variable',
    'string': 'variable',
}


class completeMenuClass(QListWidget):
    def __init__(self, parent=None, editor=None):
        super(completeMenuClass, self).__init__(parent)
        self.setAlternatingRowColors(1)
        self.setIconSize(QSize(20, 20))
        self.setUniformItemSizes(True)
        self.lineHeight = 24
        self.e = editor
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        if managers._s == 'x':
            self.setWindowFlags(Qt.FramelessWindowHint |  Qt.Window | Qt.WindowStaysOnTopHint)
        elif managers._s == 'l':
            self.setWindowFlags(Qt.FramelessWindowHint |  Qt.Tool)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint |  Qt.Window)

        self.doc_tooltip = QLabel(self)
        self.doc_tooltip.setObjectName("docTooltip")
        if managers._s == 'l':
            self.doc_tooltip.setWindowFlags(Qt.ToolTip)
        else:
            self.doc_tooltip.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.doc_tooltip.setAttribute(Qt.WA_ShowWithoutActivating)
        self.doc_tooltip.setTextFormat(Qt.PlainText)
        self.doc_tooltip.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.doc_tooltip.setWordWrap(True)
        self.doc_tooltip.setContentsMargins(4, 4, 4, 4)
        self._pending_style = None
        self._completion_colors = {}

        def doc_tooltip_focusOutEvent(event):
            QLabel.focusOutEvent(self.doc_tooltip, event)


            def _check_focus():
                fw = QApplication.focusWidget()
                if fw and (fw == self or self.isAncestorOf(fw) or fw == self.doc_tooltip):
                    return
                self.hideMe()

            QTimer.singleShot(10, _check_focus)

        self.doc_tooltip.focusOutEvent = doc_tooltip_focusOutEvent

        self._icon_cache = {}

        @self.itemDoubleClicked.connect
        def insertSelected(item):
            if item:
                comp = item.data(32)
                self.sendText(comp)
                self.hideMe()
        self.currentItemChanged.connect(self.onItemChanged)

    def onItemChanged(self, current, previous):
        if not current or not self.isVisible():
            if hasattr(self, 'doc_tooltip'):
                self.doc_tooltip.hide()
            return

        show_docstrings = False
        try:
            if hasattr(self.e, 'p') and hasattr(self.e.p, 'show_docstrings_act'):
                show_docstrings = self.e.p.show_docstrings_act.isChecked()
        except Exception:
            pass

        if show_docstrings:
            comp = current.data(32)
            if hasattr(comp, 'docstring'):
                try:
                    doc = comp.docstring()
                    if doc and str(doc).strip():
                        # Limit doc length
                        if len(doc) > 800:
                            doc = doc[:800] + '...'

                        # Show tooltip near the right side of the list
                        pos = self.mapToGlobal(self.rect().topRight())
                        pos.setX(pos.x() + 10)

                        self.doc_tooltip.setText(doc)
                        self.doc_tooltip.adjustSize()
                        self.doc_tooltip.move(pos)
                        self.doc_tooltip.show()
                    else:
                        self.doc_tooltip.hide()
                except Exception:
                    self.doc_tooltip.hide()
            else:
                self.doc_tooltip.hide()
        else:
            self.doc_tooltip.hide()

    def updateStyle(self, colors=None, style=None):
        text = style
        if text is None:
            text = (
                design.applyColorToMainStyle(colors)
                if colors is not None
                else design.editorStyle()
            )
        if colors is not None:
            self._completion_colors = colors
        self._pending_style = text if text != self.styleSheet() else None
        if self.isVisible():
            self._apply_pending_style()
        if hasattr(self, 'e') and self.e:
            use_theme_font = True
            if colors and 'use_theme_font_on_completer' in colors:
                use_theme_font = colors['use_theme_font_on_completer']
            elif hasattr(self.e, 'p') and hasattr(self.e.p, '_current_colors_cache'):
                use_theme_font = self.e.p._current_colors_cache.get('use_theme_font_on_completer', True)

            if use_theme_font:
                new_font = QFont(self.e.font())
            else:
                new_font = QApplication.font("QListWidget")

            completer_size = self.font().pointSize()
            if completer_size > 0:
                new_font.setPointSize(completer_size)
            self.setFont(new_font)
            if hasattr(self, 'doc_tooltip'):
                self.doc_tooltip.setFont(new_font)

    def _apply_pending_style(self):
        if self._pending_style is not None:
            self.setStyleSheet(self._pending_style)
            self._pending_style = None

    def updateCompleteList(self, lines=None, extra=None):
        self.clear()
        if lines or extra:
            self.showMe()
            all_items = (lines or []) + (extra or [])
            for row, i in enumerate(all_items):
                item = QListWidgetItem(i.name)
                item.setData(32, i)
                color_key = (
                    'completer_background'
                    if row % 2 == 0
                    else 'completer_alt_background'
                )
                background = self._completion_colors.get(color_key)
                if background is not None:
                    if isinstance(background, (list, tuple)):
                        background = QColor(*background)
                    item.setBackground(QBrush(background))

                if hasattr(i, 'type') and i.type:
                    symbol_type = _COMPLETION_SYMBOL_TYPES.get(
                        i.type,
                        'variable',
                    )
                    if symbol_type not in self._icon_cache:
                        self._icon_cache[symbol_type] = get_symbol_type_icon(
                            symbol_type
                        )
                    item.setIcon(self._icon_cache[symbol_type])

                self.addItem(item)

            font = self.font()
            fm = QFontMetrics(font)
            width = fm.horizontalAdvance(' ') * max([len(x.name) for x in all_items]) + 40

            self.resize(max(250,width), 250)
            self.setCurrentRow(0)
        else:
            self.hideMe()

    def applyCurrentComplete(self):
        i = self.selectedItems()
        if i:
            comp = i[0].data(32)
            self.sendText(comp)
        self.hideMe()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.accept()
            self.hideMe()
            self.editor().setFocus()
            self.editor()._suppress_autocomplete = True
            return
        # elif event.text():
        #     self.editor().setFocus()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.editor().setFocus()
            self.applyCurrentComplete()
            return event
        elif event.key() == Qt.Key_Up:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i == 0:
                    QListWidget.keyPressEvent(self, event)
                    self.setCurrentRow(self.count()-1)
                    return
        elif event.key() == Qt.Key_Down:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i+1 == self.count():
                    QListWidget.keyPressEvent(self, event)
                    self.setCurrentRow(0)
                    return
        elif event.key() == Qt.Key_Backspace:
            self.editor().setFocus()
            self.editor().activateWindow()
        elif event.text():
            self.editor().keyPressEvent(event)
            return

        QListWidget.keyPressEvent(self, event)

    def updateDocTooltipPosition(self):
        if hasattr(self, 'doc_tooltip') and self.doc_tooltip.isVisible():
            pos = self.mapToGlobal(self.rect().topRight())
            pos.setX(pos.x() + 10)
            self.doc_tooltip.move(pos)

    def moveEvent(self, event):
        super(completeMenuClass, self).moveEvent(event)
        self.updateDocTooltipPosition()

    def resizeEvent(self, event):
        super(completeMenuClass, self).resizeEvent(event)
        self.updateDocTooltipPosition()

    def sendText(self, comp):
        self.editor().insertText(comp)

    def editor(self):
        return self.e

    def activateCompleter(self, key=False):
        self.activateWindow()
        if not key==Qt.Key_Up:
            self.setCurrentRow(min(1, self.count()-1))
        else:
            self.setCurrentRow(self.count()-1)

    def showMe(self):
        self._apply_pending_style()
        self.show()
        self.e.moveCompleter()

    def focusOutEvent(self, event):
        super(completeMenuClass, self).focusOutEvent(event)


        def _check_focus():
            fw = QApplication.focusWidget()
            if fw and (fw == self or self.isAncestorOf(fw) or fw == getattr(self, 'doc_tooltip', None)):
                return
            self.hideMe()

        QTimer.singleShot(10, _check_focus)

    def hideMe(self):
        self.hide()
        if hasattr(self, 'doc_tooltip'):
            self.doc_tooltip.hide()
