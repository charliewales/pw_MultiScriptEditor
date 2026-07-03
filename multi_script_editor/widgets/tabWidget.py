from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtGui import QCursor, QFont, QIcon, QKeySequence, QTextCursor
from vendor.Qt.QtWidgets import QAction, QApplication, QHBoxLayout, QInputDialog, QMenu, QMessageBox, QPushButton, QShortcut, QTabWidget, QWidget
import os
from widgets import numBarWidget, inputWidget
from managers import context
from icons import *


style = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'style', 'completer.qss')
if not os.path.exists(style):
    style=None


class tabWidgetClass(QTabWidget):
    # Signals to decouple from MainWindow
    tab_closed = Signal(int)
    session_save_requested = Signal()
    execute_selected_requested = Signal()

    def __init__(self, parent=None):
        super(tabWidgetClass, self).__init__(parent)
        self.apply_tab_style()
        # variables
        self.p = parent
        self.lastSearch = [0, None]
        # ui
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self.openMenu)
        newTabButton = QPushButton(self)
        newTabButton.setMaximumWidth(30)
        self.setCornerWidget(newTabButton, Qt.TopLeftCorner)
        if hasattr(self.p, 'toolBar'):
            self.setCornerWidget(self.p.toolBar, Qt.TopRightCorner)
        newTabButton.setCursor(Qt.ArrowCursor)
        newTabButton.setIcon(QIcon(icons['add_tab']))
        newTabButton.clicked.connect(self.addNewTab)
        newTabButton.setToolTip("Add Tab (Ctrl+T)")
        newTabButton.setShortcut('Ctrl+T')
        self.desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None

        # We will render whitespace initially based on presenter, but for now we default to False
        # and wait for apply_settings to trigger it.

        # connects
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, self.renameTab)
        self.currentChanged.connect(self.onTabChanged)

    def onTabChanged(self, index):
        self.hideAllCompleters()
        if index >= 0:
            container = self.widget(index)
            if hasattr(container, 'edit'):
                edit = container.edit
                if hasattr(edit, 'needs_loading_file') or hasattr(edit, 'needs_loading_text'):
                    text = ""
                    file_path = getattr(edit, 'needs_loading_file', None)
                    if file_path and os.path.exists(file_path):
                        try:
                            text = open(file_path, "r", encoding="utf-8").read()
                        except Exception:
                            try:
                                text = open(file_path, "r").read()
                            except Exception:
                                text = getattr(edit, 'needs_loading_text', "") or ""
                    else:
                        text = getattr(edit, 'needs_loading_text', "") or ""

                    if text:
                        edit.addText(text)
                        edit.moveCursor(QTextCursor.Start)
                        edit.highlight_current_line()

                    if hasattr(edit, 'needs_loading_file'):
                        delattr(edit, 'needs_loading_file')
                    if hasattr(edit, 'needs_loading_text'):
                        delattr(edit, 'needs_loading_text')

    def close_current_tab(self):
        index = self.currentIndex()
        self.closeTab(index)
        # set focus on previous Tab
        current_editor = self.currentWidget().edit
        current_editor.setFocus()

    def closeTab(self, i):
        if self.count() > 1:
            if self.getCurrentText(i).strip():
                if self.yes_no_question('Close this tab without saving?\n'+self.tabText(i)):
                    self.removeTab(i)
            else:
                self.removeTab(i)

    def openMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction('Duplicate Current Tab', self, triggered = self.duplicateTab))
        menu.addAction(QAction('Rename Current Tab', self, triggered = self.renameTab))

        index = self.currentIndex()
        if index >= 0:
            widget = self.widget(index)
            if hasattr(widget, 'file_path') and widget.file_path:
                menu.addSeparator()
                menu.addAction(QAction('Copy File Path', self, triggered = self.copyFilePath))

        menu.exec_(QCursor.pos())

    def copyFilePath(self):
        index = self.currentIndex()
        if index >= 0:
            widget = self.widget(index)
            if hasattr(widget, 'file_path') and widget.file_path:
                QApplication.clipboard().setText(os.path.normpath(widget.file_path))

    def duplicateTab(self):
        index = self.currentIndex()
        name = self.tabText(index)
        text = self.getCurrentText(index)
        new_name = name + " (copy)"
        self.addNewTab(new_name, text)
        self.setCurrentIndex(self.count() - 1)

    def renameTab(self):
        index = self.currentIndex()
        text = self.tabText(index)
        result = QInputDialog.getText(self, 'New name', 'Enter New Name', text=text)
        if result[1]:
            self.setTabText(index, result[0])

    def currentTabName(self):
        index = self.currentIndex()
        text = self.tabText(index)
        return text

    def addNewTab(self, name='New Tab', text=None, file_path=None, make_current=True):
        # Ensure name is a string (PySide6 is stricter about types)
        name = str(name) if name is not None else 'New Tab'
        cont = EditorTabContainer(text, self.p, self.desk, file_path=file_path)
        cont.edit.saveSignal.connect(self.session_save_requested.emit)
        cont.edit.executeSignal.connect(self.execute_selected_requested.emit)
        self.addTab(cont, name)
        cont.edit.moveCursor(QTextCursor.Start)
        cont.edit.highlight_current_line()
        if make_current:
            self.setCurrentIndex(self.count()-1)

        # Apply settings from presenter instead of trying to find actions in MainWindow
        if hasattr(self.p, '_presenter'):
            settings = self.p._presenter.settings_model.read_settings()
            show_whitespace = settings.get('show_whitespace', False)
            wrap = settings.get('wrap', False)
            font_d = settings.get('font', {})

            cont.edit.render_whitespace(show_whitespace)
            cont.edit.wordWrap(wrap)
            cont.edit.set_start_font(font_d)

        return cont.edit

    def getTabText(self, i):
        text = self.widget(i).edit.toPlainText()
        return text

    def addToCurrent(self, text):
        i = self.currentIndex()
        self.widget(i).edit.insertPlainText(text)

    def getCurrentSelectedText(self):
        i = self.currentIndex()
        text = self.widget(i).edit.get_current_word()
        return text

    def getCurrentText(self, i=None):
        if i is None:
            i = self.currentIndex()
        text = self.widget(i).edit.toPlainText()
        return text

    def getCurrentLine(self, i=None):
        if i is None:
            i = self.currentIndex()

        edit = self.widget(i).edit
        cursor = edit.textCursor()
        current_cursor_pos = cursor.position()
        cursor.select(QTextCursor.LineUnderCursor)
        edit.setTextCursor(cursor)
        text = edit.getSelection()
        cursor.setPosition(current_cursor_pos)
        edit.setTextCursor(cursor)
        return text

    def setCurrentText(self, text):
        i = self.currentIndex()
        self.widget(i).edit.setPlainText(text)


    def hideAllCompleters(self):
        for i in range(self.count()):
            self.widget(i).edit.completer.hideMe()

    def current(self):
        return self.widget(self.currentIndex()).edit

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            current_index = self.currentIndex()
            self.closeTab(current_index)

############################## editor commands
    def apply_tab_style(self, colors=None):
        if not colors:
            from widgets.pythonSyntax.design import defaultColors
            colors = defaultColors

        self._tab_text_size = float(colors.get('tab_text_size', 10))

        def c(name):
            val = colors.get(name, (128,128,128))
            if isinstance(val, (list, tuple)):
                return "#%02x%02x%02x" % tuple(val)
            return str(val)

        css = """
            QTabBar::tab {
                max-width: 250px;
                min-width: 80px;
                border: 2px solid %(tab_border)s;
                border-top-left-radius: %(tab_radius)s;
                border-top-right-radius: %(tab_radius)s;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 3px;
                padding-bottom: 3px;
                margin-right: 3px;
                background: %(tab_background)s;
                color: %(tab_text)s;
            }
            QTabBar::tab:hover {
                background: %(tab_hover_background)s;
                color: %(tab_hover_text)s;
                border: 2px solid %(tab_hover_border)s;
            }

            QTabBar::tab:selected {
                background: %(tab_selected_background)s;
                color: %(tab_selected_text)s;
                border: 2px solid %(tab_selected_border)s;
                border-top-left-radius: %(tab_radius)s;
                border-top-right-radius: %(tab_radius)s;
            }

            QTabBar::close-button {
                image: url("%(close_tab)s");
                width: 14px;
                height: 14px;
                margin-right: 4px;
            }
            QTabBar::close-button:hover {
                background: rgba(255, 100, 100, 255);
                border-radius: 6px;
            }
        """ % {
            "tab_border": c("tab_border"),
            "tab_background": c("tab_background"),
            "tab_text": c("tab_text"),
            "tab_hover_background": c("tab_hover_background"),
            "tab_hover_text": c("tab_hover_text"),
            "tab_hover_border": c("tab_hover_border"),
            "tab_selected_background": c("tab_selected_background"),
            "tab_selected_text": c("tab_selected_text"),
            "tab_selected_border": c("tab_selected_border"),
            "tab_radius": str(colors.get("tab_radius", 12)) + "px",
            "close_tab": icons["close_tab"].replace("\\", "/")
        }
        
        ss = self.styleSheet()
        import re
        font_match = re.search(r'/\*TAB_FONT_START\*/.*/\*TAB_FONT_END\*/', ss, flags=re.DOTALL)
        if font_match:
            css += '\n' + font_match.group(0)
            
        self.setStyleSheet(css)

    def undo(self):
        self.current().undo()

    def redo(self):
        self.current().redo()

    def cut(self):
        self.current().cut()

    def copy(self):
        self.current().copy()

    def _apply_tab_font(self, font):
        from vendor.Qt.QtGui import QFont
        tab_font = QFont(font)
        family = tab_font.family()
        pt_size = tab_font.pointSizeF()
        custom_size = getattr(self, '_tab_text_size', 10.0)
        
        if pt_size > 0:
            tab_font.setPointSizeF(custom_size)
            size_css = "font-size: %spt;" % custom_size
        else:
            px_size = tab_font.pixelSize()
            if px_size > 0:
                tab_font.setPixelSize(int(custom_size))
                size_css = "font-size: %spx;" % int(custom_size)
            else:
                size_css = ""

        self.tabBar().setFont(tab_font)

        css = "\n/*TAB_FONT_START*/\nQTabBar::tab { font-family: '%s'; %s }\n/*TAB_FONT_END*/\n" % (family, size_css)
        import re
        ss = self.styleSheet()
        ss = re.sub(r'/\*TAB_FONT_START\*/.*/\*TAB_FONT_END\*/', '', ss, flags=re.DOTALL)
        self.setStyleSheet(ss + css)

    def render_whitespace(self, state):
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.render_whitespace(state)

    def wordWrap(self, state):
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.wordWrap(state)
        # update line numbers
        self.update()

    def set_font(self, font):
        self._apply_tab_font(font)
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.setFont(font)

    def set_start_font(self, font_d=None):
        if font_d:
            from vendor.Qt.QtGui import QFont
            family = font_d.get('family', 'monospace')
            size = font_d.get('pointSize', 10)
            weight = font_d.get('weight', -1)
            italic = font_d.get('italic', False)
            
            if family:
                font = QFont(family, size, weight, italic)
                font.setStyleHint(QFont.Monospace)
                self._apply_tab_font(font)
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.set_start_font(font_d)

    def paste(self):
        self.current().paste()

    def search(self, text=None, case_sensitive=False):
        if text:
            if not hasattr(self, 'lastSearch') or len(self.lastSearch) < 3:
                self.lastSearch = [text, 0, case_sensitive]
            if text == self.lastSearch[0] and case_sensitive == self.lastSearch[2]:
                self.lastSearch[1] += 1
            else:
                self.lastSearch = [text, 0, case_sensitive]
            self.lastSearch[1] = self.current().selectWord(text, self.lastSearch[1], case_sensitive=case_sensitive)

    def replace(self, parts, case_sensitive=False):
        find, rep = parts
        self.lastSearch = [find, 0, case_sensitive]
        self.lastSearch[1] = self.current().selectWord(find, self.lastSearch[1], rep, case_sensitive=case_sensitive)
        self.current().selectWord(find, self.lastSearch[1], case_sensitive=case_sensitive)

    def replaceAll(self, parts, case_sensitive=False):
        find, rep = parts
        self.current().replaceAll(find, rep, case_sensitive=case_sensitive)

    def move_line_up(self):
        self.current().move_line_up()

    def move_line_down(self):
        self.current().move_line_down()

    def comment(self):
        self.current().commentSelected()

    def addQuotes(self):
        self.current().addQuotesSelected()

    def selectNextOccurrence(self):
        self.current().select_next_occurrence()

    def selectAllOccurrences(self):
        self.current().select_all_occurrences()

    def yes_no_question(self, question):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Multi Script Editor")
        msg_box.setText(question)
        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        no_button = msg_box.addButton("No", QMessageBox.NoRole)
        yes_button.setFocus()
        msg_box.exec_()
        return msg_box.clickedButton() == yes_button


class EditorTabContainer(QWidget):
    def __init__(self, text, parent, desk, file_path=None):
        super(EditorTabContainer, self).__init__()
        self.file_path = file_path
        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)
        # input widget
        self.edit = inputWidget.inputClass(parent, desk)
        if text:
            self.edit.addText(text)
        self.lineNum = numBarWidget.lineNumberBarClass(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda :self.lineNum.update())
        self.edit.inputSignal.connect(lambda :self.lineNum.update())
        self.edit.document().blockCountChanged.connect(lambda :self.lineNum.update())

        hbox.addWidget(self.lineNum)
        hbox.addWidget(self.edit)


if __name__ == '__main__':
    app = QApplication([])
    w = tabWidgetClass()
    w.show()
    app.exec_()
