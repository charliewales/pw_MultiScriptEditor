from vendor.Qt.QtCore import *
from vendor.Qt.QtWidgets import *
from vendor.Qt.QtGui import *
import os
from widgets import numBarWidget, inputWidget
from managers import context
from icons import *


style = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'style', 'completer.qss')
if not os.path.exists(style):
    style=None


class tabWidgetClass(QTabWidget):
    def __init__(self, parent=None):
        super(tabWidgetClass, self).__init__(parent)
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
        self.setCornerWidget(self.p.toolBar, Qt.TopRightCorner)
        newTabButton.setCursor(Qt.ArrowCursor)
        newTabButton.setIcon(QIcon(icons['add_tab']))
        newTabButton.clicked.connect(self.addNewTab)
        newTabButton.setToolTip("Add Tab (Ctrl+T)")
        newTabButton.setShortcut('Ctrl+T')
        self.desk = QApplication.desktop()
        whitespace_act = self.p.findChild(QAction, "whitespace_act")
        self.render_whitespace(whitespace_act.isChecked())
        #connects
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, self.renameTab)
        self.currentChanged.connect(self.hideAllCompleters)

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
        menu.addAction(QAction('Rename Current Tab', self, triggered = self.renameTab))
        menu.exec_(QCursor.pos())

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

    def addNewTab(self, name='New Tab', text = None):
        cont = container(text, self.p, self.desk)
        cont.edit.saveSignal.connect(self.p.saveSession)
        self.addTab(cont, name)
        cont.edit.moveCursor(QTextCursor.Start)
        cont.edit.highlight_current_line()
        self.setCurrentIndex(self.count()-1)

        ws_widget = self.p.findChildren(QAction, 'whitespace_act')[0]
        ww_widget = self.p.findChildren(QAction, 'wordWrap_act')[0]

        cont.edit.render_whitespace(ws_widget.isChecked())

        cont.edit.wordWrap(not ww_widget.isChecked())
        cont.edit.wordWrap(ww_widget.isChecked())

        cont.edit.set_start_font()

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
    def undo(self):
        self.current().undo()

    def redo(self):
        self.current().redo()

    def cut(self):
        self.current().cut()

    def copy(self):
        self.current().copy()

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
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.setFont(font)

    def set_start_font(self, font_d):
        family = font_d.get('family', 'Courier')
        pointSize = font_d.get('pointSize', 10)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)
        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        for i in range(self.count()):
            current_edit = self.widget(i).edit
            current_edit.setFont(editor_font)

    def paste(self):
        self.current().paste()

    def search(self, text=None):
        if text:
            if text == self.lastSearch[0]:
                self.lastSearch[1] += 1
            else:
                self.lastSearch = [text, 0]
            self.lastSearch[1] = self.current().selectWord(text, self.lastSearch[1])

    def replace(self, parts):
        find, rep = parts
        self.lastSearch = [find, 0]
        self.lastSearch[1] = self.current().selectWord(find, self.lastSearch[1], rep)
        self.current().selectWord(find, self.lastSearch[1])

    def replaceAll(self, pat):
        find, rep = pat
        text = self.current().toPlainText()
        text = text.replace(find, rep)
        self.current().setPlainText(text)

    def comment(self):
        self.current().commentSelected()

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


class container(QWidget):
    def __init__(self, text, parent, desk):
        super(container, self).__init__()
        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)
        # input widget
        self.edit = inputWidget.inputClass(parent, desk)
        self.edit.executeSignal.connect(parent.executeSelected)
        if text:
            self.edit.addText(text)
        hbox.addWidget(self.edit)
        self.lineNum = numBarWidget.lineNumberBarClass(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda :self.lineNum.update())
        self.edit.inputSignal.connect(lambda :self.lineNum.update())

        hbox.addWidget(self.lineNum)
        hbox.addWidget(self.edit)


if __name__ == '__main__':
    app = QApplication([])
    w = tabWidgetClass()
    w.show()
    app.exec_()
