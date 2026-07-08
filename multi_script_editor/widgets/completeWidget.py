from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFont, QFontMetrics, QPixmap, QPainter, QColor, QIcon
from vendor.Qt.QtWidgets import QListWidget, QListWidgetItem, QLabel
import os
from . pythonSyntax import design
import managers
style = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'style', 'completer.qss')
if not os.path.exists(style):
    style=None


class completeMenuClass(QListWidget):
    def __init__(self, parent=None, editor=None):
        # if managers.context == 'hou':
        #     super(completeMenuClass, self).__init__(managers.main_parent or parent)
        # else:
        super(completeMenuClass, self).__init__(parent)
        self.setAlternatingRowColors(1)
        self.lineHeight = 18
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
        except:
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

    def updateStyle(self, colors=None):
        text = design.editorStyle()
        self.setStyleSheet(text)
        if hasattr(self, 'e') and self.e:
            use_theme_font = True
            if colors and 'use_theme_font_on_completer' in colors:
                use_theme_font = colors['use_theme_font_on_completer']
            elif hasattr(self.e, 'p') and hasattr(self.e.p, '_current_colors_cache'):
                use_theme_font = self.e.p._current_colors_cache.get('use_theme_font_on_completer', True)
            
            if use_theme_font:
                new_font = QFont(self.e.font())
            else:
                new_font = QFont()
                
            completer_size = self.font().pointSize()
            if completer_size > 0:
                new_font.setPointSize(completer_size)
            self.setFont(new_font)
            if hasattr(self, 'doc_tooltip'):
                self.doc_tooltip.setFont(new_font)

    def updateCompleteList(self, lines=None, extra=None):
        self.clear()
        if lines or extra:
            self.showMe()
            all_items = (lines or []) + (extra or [])
            for i in all_items:
                item = QListWidgetItem(i.name)
                item.setData(32, i)
                
                if hasattr(i, 'type') and i.type:
                    t = i.type
                    if t not in self._icon_cache:
                        # Generate a colored icon
                        color_map = {
                            'function': QColor(100, 180, 255),
                            'class': QColor(150, 220, 100),
                            'module': QColor(255, 150, 100),
                            'statement': QColor(200, 200, 200),
                            'keyword': QColor(255, 100, 150)
                        }
                        text_map = {'function': 'f', 'class': 'C', 'module': 'M', 'statement': 'V', 'keyword': 'K'}
                        
                        pix = QPixmap(16, 16)
                        pix.fill(Qt.transparent)
                        painter = QPainter(pix)
                        painter.setRenderHint(QPainter.Antialiasing)
                        
                        c = color_map.get(t, QColor(150, 150, 150))
                        painter.setBrush(c)
                        painter.setPen(Qt.NoPen)
                        painter.drawRect(0, 0, 16, 16)
                        
                        painter.setPen(Qt.black)
                        font = QFont("Arial", 9)
                        painter.setFont(font)
                        char = text_map.get(t, '?')
                        painter.drawText(pix.rect(), Qt.AlignCenter, char)
                        painter.end()
                        
                        self._icon_cache[t] = QIcon(pix)
                        
                    item.setIcon(self._icon_cache[t])
                    
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
        self.show()
        self.e.moveCompleter()

    def hideMe(self):
        self.hide()
        if hasattr(self, 'doc_tooltip'):
            self.doc_tooltip.hide()
