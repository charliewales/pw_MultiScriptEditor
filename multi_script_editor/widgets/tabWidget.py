import os

from vendor.Qt.QtCore import Qt, Signal, QSize, QEvent, QRectF, QTimer
from vendor.Qt.QtGui import QCursor, QIcon, QKeySequence, QTextCursor, QFont, QColor, QPixmap, QPainter
from widgets.pythonSyntax.design import defaultColors
import re
from vendor.Qt.QtWidgets import QAction, QApplication, QHBoxLayout, QInputDialog, QMenu, QMessageBox, QPushButton, QShortcut, QTabWidget, QWidget, QTabBar, QLabel, QLineEdit
from widgets import numBarWidget, inputWidget
from widgets.pythonSyntax import design
from icons import *




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
        self._ctrl_pressed = False
        self._mru_tabs = []
        # ui
        self.setTabsClosable(True)
        self.setMovable(True)
        # Ensure scroll buttons are shown instead of squeezing tabs when they exceed the width
        self.setUsesScrollButtons(True)
        self.tabBar().setExpanding(False)
        self.tabBar().setElideMode(Qt.ElideNone)
        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self.update_custom_close_buttons)
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self.openMenu)
        # Corner Widget Layout
        self.corner_widget = QWidget(self)
        self.corner_layout = QHBoxLayout(self.corner_widget)
        self.corner_layout.setContentsMargins(0, 0, 10, 0)
        self.corner_layout.setSpacing(2)

        self.toggleOutline_btn = QPushButton(self.corner_widget)
        self.toggleOutline_btn.setMaximumWidth(30)
        self.toggleOutline_btn.setCursor(Qt.ArrowCursor)
        self.toggleOutline_btn.setIcon(QIcon(icons['outline']))
        self.toggleOutline_btn.setIconSize(QSize(24, 24))
        self.toggleOutline_btn.setToolTip("Toggle Code Outline (Ctrl+Shift+O)")
        self.toggleOutline_btn.setCheckable(True)
        self.toggleOutline_btn.toggled.connect(self.toggle_outline)

        newTabButton = QPushButton(self.corner_widget)
        newTabButton.setMaximumWidth(30)
        newTabButton.setCursor(Qt.ArrowCursor)
        newTabButton.setIcon(QIcon(icons['add_tab']))
        newTabButton.setIconSize(QSize(24, 24))
        newTabButton.clicked.connect(lambda checked=False: self.addNewTab())
        newTabButton.setToolTip("New Tab (Ctrl+T)")
        newTabButton.setShortcut('Ctrl+T')

        self.corner_layout.addWidget(self.toggleOutline_btn)
        self.corner_layout.addWidget(newTabButton)
        self.setCornerWidget(self.corner_widget, Qt.TopLeftCorner)

        if hasattr(self.p, 'toolBar'):
            self.right_corner_widget = QWidget(self)
            self.right_corner_layout = QHBoxLayout(self.right_corner_widget)
            self.right_corner_layout.setContentsMargins(15, 0, 0, 0)
            self.right_corner_layout.setSpacing(0)
            self.right_corner_layout.addWidget(self.p.toolBar)
            self.setCornerWidget(self.right_corner_widget, Qt.TopRightCorner)

        self.desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None

        # We will render whitespace initially based on presenter, but for now we default to False
        # and wait for apply_settings to trigger it.

        # connects
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Alt+R"), self, self.renameTab)
        sc = QShortcut(QKeySequence("Alt+Shift+C"), self, self.copyFilePath)
        sc.setContext(Qt.WidgetWithChildrenShortcut)

        for i in range(1, 10):
            QShortcut(QKeySequence("Ctrl+%d" % i), self, lambda i=i: self.switch_to_tab_index(i-1))

        self.currentChanged.connect(self.onTabChanged)
        self.tabBarDoubleClicked.connect(self.on_tab_bar_double_clicked)
        QApplication.instance().installEventFilter(self)

    def on_tab_bar_double_clicked(self, index):
        if QApplication.mouseButtons() & Qt.LeftButton:
            self.renameTab(index)

    def eventFilter(self, obj, event):
        if obj == getattr(self, '_rename_edit', None) and event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.finishRename(commit=False)
            return True

        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick) and event.button() == Qt.MiddleButton:
            if getattr(self, '_rename_edit', None):
                return True
            # Check if click is on the tab bar or one of its children
            p = obj
            is_tabbar_click = False
            while p:
                if p == self.tabBar():
                    is_tabbar_click = True
                    break
                p = p.parent()
            if is_tabbar_click:
                if event.type() == QEvent.MouseButtonPress:
                    pos = self.tabBar().mapFrom(obj, event.pos())
                    index = self.tabBar().tabAt(pos)
                    if index >= 0:
                        QTimer.singleShot(0, lambda i=index: self.closeTab(i))
                return True

        quick_tab_switching = True
        if hasattr(self.p, 'quickTabSwitching_act'):
            quick_tab_switching = self.p.quickTabSwitching_act.isChecked()

        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Control and not self._ctrl_pressed:
                if quick_tab_switching:
                    self._ctrl_pressed = True
                    self.show_tab_numbers(True)
            elif event.key() == Qt.Key_Tab and (event.modifiers() & Qt.ControlModifier):
                if hasattr(self.p, 'showOpenTabs'):
                    self.p.showOpenTabs()
                return True
        elif event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_Control and self._ctrl_pressed:
                self._ctrl_pressed = False
                self.show_tab_numbers(False)
        elif event.type() == QEvent.WindowDeactivate or event.type() == QEvent.ApplicationDeactivate:
            if self._ctrl_pressed:
                self._ctrl_pressed = False
                self.show_tab_numbers(False)
        return False

    def get_line_num_font_and_color(self, edit):
        font = edit.font()
        pt_size = font.pointSizeF()
        if pt_size > 0:
            if hasattr(edit, '_line_num_size_cache') and edit._line_num_size_cache is not None:
                font.setPointSizeF(float(edit._line_num_size_cache))
            else:
                font.setPointSizeF(max(1.0, pt_size * 0.8))
        else:
            px_size = font.pixelSize()
            if px_size > 0:
                if hasattr(edit, '_line_num_size_cache') and edit._line_num_size_cache is not None:
                    font.setPixelSize(edit._line_num_size_cache)
                else:
                    font.setPixelSize(max(1, int(px_size * 0.8)))

        color = None
        if hasattr(edit, '_line_num_text_cache') and edit._line_num_text_cache:
            color = QColor.fromRgb(*edit._line_num_text_cache)

        return font, color

    def show_tab_numbers(self, show):
        for i in range(min(self.count(), 9)):
            tab_widget = self.widget(i)
            if not tab_widget:
                continue
            if show:
                btn = self.tabBar().tabButton(i, QTabBar.RightSide)
                style = "border-radius: 4px; margin-right: 4px;"
                if btn and type(btn).__name__ != 'QLabel':
                    tab_widget._original_close_button = btn

                    if not hasattr(tab_widget, '_tab_number_label'):
                        lbl = QLabel(str(i + 1))
                        lbl.setAlignment(Qt.AlignCenter)

                        # Apply font and color from line numbers
                        font, color = self.get_line_num_font_and_color(tab_widget.edit)
                        lbl.setFont(font)

                        # style = "font-weight: bold; margin: 0px; padding: 0px; border: 1px solid red;"
                        if color:
                            style += f" color: {color.name()};"
                        lbl.setStyleSheet(style)

                        # Apply original button size
                        if btn.size().width() > 0 and btn.size().height() > 0:
                            lbl.setFixedSize(btn.size())

                        tab_widget._tab_number_label = lbl
                    else:
                        tab_widget._tab_number_label.setText(str(i + 1))
                        # Update size/style in case it changed
                        font, color = self.get_line_num_font_and_color(tab_widget.edit)
                        tab_widget._tab_number_label.setFont(font)
                        # style = "font-weight: bold; margin: 0px; padding: 0px; border: 1px solid red;"
                        if color:
                            style += f" color: {color.name()};"
                        tab_widget._tab_number_label.setStyleSheet(style)
                        if btn.size().width() > 0 and btn.size().height() > 0:
                            tab_widget._tab_number_label.setFixedSize(btn.size())

                    self.tabBar().setTabButton(i, QTabBar.RightSide, tab_widget._tab_number_label)
                    tab_widget._tab_number_label.show()
            else:
                current_btn = self.tabBar().tabButton(i, QTabBar.RightSide)
                if current_btn and type(current_btn).__name__ == 'QLabel':
                    if hasattr(tab_widget, '_original_close_button') and tab_widget._original_close_button:
                        self.tabBar().setTabButton(i, QTabBar.RightSide, tab_widget._original_close_button)
                        tab_widget._original_close_button.show()

    def toggle_outline(self, state):
        if hasattr(self.p, 'toggleOutline'):
            self.p.toggleOutline(state)

    def onTabChanged(self, index):
        self.hideAllCompleters()
        if index >= 0:
            container = self.widget(index)
            if hasattr(self, '_mru_tabs'):
                if container in self._mru_tabs:
                    self._mru_tabs.remove(container)
                self._mru_tabs.insert(0, container)

            if hasattr(container, 'edit'):
                edit = container.edit
                if hasattr(edit, 'needs_loading_file') or hasattr(edit, 'needs_loading_text'):
                    text = ""
                    file_path = getattr(edit, 'needs_loading_file', None)
                    if file_path and os.path.exists(file_path):
                        from core.file_utils import read_file_text
                        text = read_file_text(file_path)
                        if not text:
                            text = getattr(edit, 'needs_loading_text', "") or ""
                    else:
                        text = getattr(edit, 'needs_loading_text', "") or ""

                    if text:
                        edit.addText(text)
                        # Restore line and column once text is loaded
                        if hasattr(edit, 'needs_loading_line'):
                            line_num = edit.needs_loading_line
                            column_num = getattr(edit, 'needs_loading_column', 0)
                            delattr(edit, 'needs_loading_line')
                            if hasattr(edit, 'needs_loading_column'):
                                delattr(edit, 'needs_loading_column')
                            if line_num > 1 or column_num > 0:
                                block = edit.document().findBlockByNumber(line_num - 1)
                                if block.isValid():
                                    cursor = edit.textCursor()
                                    col = min(column_num, max(0, block.length() - 1))
                                    cursor.setPosition(block.position() + col)
                                    edit.setTextCursor(cursor)
                                    if hasattr(edit, 'highlight_current_line'):
                                        edit.highlight_current_line()
                                else:
                                    edit.moveCursor(QTextCursor.Start)
                                    edit.highlight_current_line()
                            else:
                                edit.moveCursor(QTextCursor.Start)
                                edit.highlight_current_line()
                        else:
                            edit.moveCursor(QTextCursor.Start)
                            edit.highlight_current_line()

                        # Restore scroll once text is loaded
                        if hasattr(edit, 'needs_loading_scroll_v'):
                            scroll_v = edit.needs_loading_scroll_v
                            delattr(edit, 'needs_loading_scroll_v')
                            if scroll_v > 0:
                                edit.verticalScrollBar().setValue(scroll_v)
                                from vendor.Qt.QtCore import QTimer
                                QTimer.singleShot(0, lambda: edit.verticalScrollBar().setValue(scroll_v))
                                QTimer.singleShot(150, lambda: edit.verticalScrollBar().setValue(scroll_v))

                        edit.document().clearUndoRedoStacks()
                        edit.document().setModified(False)
                        if hasattr(edit, 'needs_loading_folds') and edit.needs_loading_folds:
                            if hasattr(edit, 'set_folded_blocks'):
                                edit.set_folded_blocks(edit.needs_loading_folds)
                            delattr(edit, 'needs_loading_folds')
                    else:
                        if hasattr(edit, 'needs_loading_line'):
                            delattr(edit, 'needs_loading_line')
                        if hasattr(edit, 'needs_loading_column'):
                            delattr(edit, 'needs_loading_column')
                        if hasattr(edit, 'needs_loading_scroll_v'):
                            delattr(edit, 'needs_loading_scroll_v')
                        if hasattr(edit, 'needs_loading_folds'):
                            delattr(edit, 'needs_loading_folds')
                        edit.moveCursor(QTextCursor.Start)
                        edit.highlight_current_line()

                    # Restore bookmarks once text is loaded
                    if hasattr(edit, 'set_bookmarks') and hasattr(edit, 'needs_loading_bookmarks'):
                        if edit.needs_loading_bookmarks:
                            edit.set_bookmarks(edit.needs_loading_bookmarks)
                        delattr(edit, 'needs_loading_bookmarks')

                    if hasattr(edit, 'needs_loading_folds'):
                        delattr(edit, 'needs_loading_folds')

                    if hasattr(edit, 'needs_loading_file'):
                        delattr(edit, 'needs_loading_file')
                    if hasattr(edit, 'needs_loading_text'):
                        delattr(edit, 'needs_loading_text')

    def close_current_tab(self):
        index = self.currentIndex()
        self.closeTab(index)
        # set focus on previous Tab
        current_widget = self.currentWidget()
        if current_widget:
            current_widget.edit.setFocus()

    def tabNeedsSaving(self, i):
        widget = self.widget(i)
        if not widget or not hasattr(widget, 'edit'):
            return False
        if hasattr(widget, 'file_path') and widget.file_path:
            return widget.edit.document().isModified()
        return bool(self.getCurrentText(i).strip())

    def closeTab(self, i):
        if getattr(self, '_rename_edit', None):
            self.finishRename(commit=False)
        removed = False
        widget_to_remove = self.widget(i)
        if self.tabNeedsSaving(i):
            if self.yes_no_question('Close this tab without saving?\n'+self.tabText(i)):
                self.removeTab(i)
                removed = True
        else:
            self.removeTab(i)
            removed = True

        if removed:
            if hasattr(self, '_mru_tabs') and widget_to_remove in self._mru_tabs:
                self._mru_tabs.remove(widget_to_remove)
            if self.count() == 0:
                self.addNewTab()

    def openMenu(self, pos=None):
        if pos is not None and not isinstance(pos, bool):
            index = self.tabBar().tabAt(pos)
        else:
            index = self.currentIndex()

        if index < 0:
            return

        menu = QMenu(self)
        if hasattr(self.p, 'menubar'):
            menu.setFont(self.p.menubar.font())

        dup_action = QAction('Duplicate Tab', self)
        dup_action.triggered.connect(lambda checked=False, idx=index: self.duplicateTab(idx))
        menu.addAction(dup_action)

        ren_action = QAction('Rename Tab', self)
        ren_action.setShortcut('Alt+R')
        ren_action.triggered.connect(lambda checked=False, idx=index: self.renameTab(idx))
        menu.addAction(ren_action)

        widget = self.widget(index)
        if hasattr(widget, 'file_path') and widget.file_path:
            menu.addSeparator()
            copy_action = QAction('Copy File Path', self)
            copy_action.setShortcut('Alt+Shift+C')
            copy_action.triggered.connect(lambda checked=False, idx=index: self.copyFilePath(idx))
            menu.addAction(copy_action)

        if hasattr(self.p, 'menubar') and not self.p.menubar.isVisible():
            menu.addSeparator()
            show_menus_action = QAction('Show menus\tCtrl+M', self)
            if 'menu' in icons:
                show_menus_action.setIcon(QIcon(icons['menu']))
            if hasattr(self.p, 'toggleMenus_act'):
                show_menus_action.triggered.connect(self.p.toggleMenus_act.trigger)
            menu.addAction(show_menus_action)

        menu.exec_(QCursor.pos())

    def copyFilePath(self, index=None):
        if index is None or isinstance(index, bool):
            index = self.currentIndex()
        if index >= 0:
            widget = self.widget(index)
            if hasattr(widget, 'file_path') and widget.file_path:
                QApplication.clipboard().setText(os.path.normpath(widget.file_path))

    def duplicateTab(self, index=None):
        if index is None or isinstance(index, bool):
            index = self.currentIndex()
        if index < 0:
            return
        name = self.tabText(index)
        text = self.getCurrentText(index)
        new_name = name + " (copy)"
        self.addNewTab(new_name, text)
        self.setCurrentIndex(self.count() - 1)

    def finishRename(self, commit=True):
        edit = getattr(self, '_rename_edit', None)
        if not edit:
            return
        self._rename_edit = None
        try:
            edit.editingFinished.disconnect()
        except Exception:
            pass
        if commit:
            widget = getattr(edit, '_widget_to_rename', None)
            if widget:
                new_text = edit.text()
                idx = self.indexOf(widget)
                if new_text and idx >= 0:
                    self.setTabText(idx, new_text)
        edit.hide()
        edit.deleteLater()

    def renameTab(self, index=None):
        if index is None or isinstance(index, bool):
            index = self.currentIndex()
        if index < 0:
            return

        if getattr(self, '_rename_edit', None):
            self.finishRename(commit=True)

        widget_to_rename = self.widget(index)
        rect = self.tabBar().tabRect(index)

        edit = QLineEdit(self.tabBar())
        edit.setObjectName('tabRenameEdit')
        edit._widget_to_rename = widget_to_rename
        self._rename_edit = edit
        edit.setFont(self.tabBar().font())
        edit.setText(self.tabText(index))
        edit.selectAll()

        # Adjust geometry slightly to fit nicely within the tab
        edit.setGeometry(rect.adjusted(3, 1, -1, -1))
        edit.installEventFilter(self)

        edit.editingFinished.connect(lambda: self.finishRename(commit=True))
        edit.show()
        edit.setFocus()

    def currentTabName(self):
        index = self.currentIndex()
        text = self.tabText(index)
        return text

    def addNewTab(self, name='New Tab', text=None, file_path=None, make_current=True):
        # Ensure name is a string and handle PySide6 signal boolean parameter
        if isinstance(name, bool) or name is None:
            name = 'New Tab'
        else:
            name = str(name)

        if file_path:
            norm_file_path = os.path.normcase(os.path.abspath(file_path))
            for i in range(self.count()):
                w = self.widget(i)
                w_file_path = getattr(w, 'file_path', None)
                if w_file_path and os.path.normcase(os.path.abspath(w_file_path)) == norm_file_path:
                    if make_current:
                        self.setCurrentIndex(i)
                    return w.edit

        cont = EditorTabContainer(text, self.p, self.desk, file_path=file_path)
        cont.edit.saveSignal.connect(self.session_save_requested.emit)
        cont.edit.executeSignal.connect(self.execute_selected_requested.emit)
        if hasattr(self.p, 'showStatusMessage'):
            cont.edit.messageSignal.connect(self.p.showStatusMessage)
        self.addTab(cont, name)

        btn = QPushButton()
        btn.setObjectName("CustomCloseBtn")
        btn.setFixedSize(20, 20)
        # btn.setCursor(Qt.ArrowCursor)
        btn.setProperty('isDirty', False)
        btn.setProperty('isSelected', self.count() - 1 == self.currentIndex())
        btn.clicked.connect(lambda checked=False, c=cont: self.tabCloseRequested.emit(self.indexOf(c)))
        self.tabBar().setTabButton(self.count() - 1, QTabBar.RightSide, btn)
        cont._custom_close_btn = btn

        if file_path:
            self.setTabToolTip(self.count() - 1, os.path.normpath(file_path))

        if hasattr(self.p, 'updateStatusBarInfo'):
            cont.edit.cursorPositionChanged.connect(self.p.updateStatusBarInfo)
            cont.edit.textChanged.connect(self.p.updateStatusBarInfo)

        cont.edit.document().modificationChanged.connect(lambda state, c=cont: self.mark_tab_dirty(c, state))
        cont.edit.moveCursor(QTextCursor.Start)
        cont.edit.highlight_current_line()
        if make_current:
            self.setCurrentIndex(self.count()-1)

        # Apply settings from presenter instead of trying to find actions in MainWindow
        if hasattr(self.p, '_presenter'):
            settings = self.p._presenter.settings_model.read_settings()
            show_whitespace = settings.get('show_whitespace', False)
            wrap = settings.get('wrap', False)

            # Resolve font: theme font first, then general settings font
            theme_name = settings.get('theme', 'Multi Script Editor')

            colors = design.getColors(theme_name)
            font_d = colors.get('font')
            if not font_d:
                font_d = settings.get('font', {})

            cont.edit.render_whitespace(show_whitespace)
            cont.edit.wordWrap(wrap)
            cont.edit.set_start_font(font_d)
            cont.edit.applyHightLighter(theme_name)

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
        self.widget(i).edit.document().clearUndoRedoStacks()


    def hideAllCompleters(self):
        for i in range(self.count()):
            self.widget(i).edit.completer.hideMe()

    def current(self):
        w = self.widget(self.currentIndex())
        if w:
            return w.edit
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            if getattr(self, '_rename_edit', None):
                return
            pos = self.tabBar().mapFrom(self, event.pos())
            index = self.tabBar().tabAt(pos)
            if index >= 0:
                QTimer.singleShot(0, lambda i=index: self.closeTab(i))
        else:
            super(tabWidgetClass, self).mousePressEvent(event)

############################## editor commands
    def update_custom_close_buttons(self, index=None):
        for i in range(self.count()):
            cont = self.widget(i)
            if hasattr(cont, '_custom_close_btn'):
                btn = cont._custom_close_btn
                is_sel = (i == self.currentIndex())
                btn.setProperty('isSelected', is_sel)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def mark_tab_dirty(self, container, state):
        if not hasattr(container, '_custom_close_btn'):
            return

        if not hasattr(container, 'file_path') or not container.file_path:
            return

        btn = container._custom_close_btn
        btn.setProperty('isDirty', state)

        if state:
            theme_name = 'Multi Script Editor'
            if hasattr(self.p, '_presenter'):
                theme_name = self.p._presenter.settings_model.read_settings().get('theme', theme_name)
            colors = design.getColors(theme_name)
            window_color = colors.get('window', [160, 160, 160])

            pixmap = QPixmap(btn.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(*window_color))
            painter.setPen(Qt.NoPen)

            r = min(pixmap.width(), pixmap.height()) / 4.0
            cx = pixmap.width() / 2.0
            cy = pixmap.height() / 2.0
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2.0, r * 2.0))
            painter.end()

            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(btn.size())
        else:
            btn.setIcon(QIcon())

        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def apply_tab_style(self, colors=None):
        if not colors:
            colors = defaultColors

        self._use_theme_font_on_tab_label = colors.get('use_theme_font_on_tab_label', True)

        tab_text_size = colors.get('tab_text_size', None)
        if tab_text_size is not None:
            self._tab_text_size = float(tab_text_size)
        elif 'textsize' in colors:
            self._tab_text_size = float(colors['textsize'])
        else:
            self._tab_text_size = 10.0

        ss = self.styleSheet()
        font_match = re.search(r'/\*TAB_FONT_START\*/.*/\*TAB_FONT_END\*/', ss, flags=re.DOTALL)
        if font_match:
            self.setStyleSheet(font_match.group(0))
        else:
            self.setStyleSheet('')

    def undo(self):
        self.current().undo()

    def redo(self):
        self.current().redo()

    def cut(self):
        self.current().cut()

    def copy(self):
        self.current().copy()

    def showClipboardManager(self):
        if hasattr(self.current(), 'show_clipboard_popup'):
            self.current().show_clipboard_popup()

    def switch_to_tab_index(self, index):
        if hasattr(self.p, 'quickTabSwitching_act') and not self.p.quickTabSwitching_act.isChecked():
            return
        if 0 <= index < self.count():
            self.setCurrentIndex(index)
            current_widget = self.widget(index)
            if current_widget and hasattr(current_widget, 'edit'):
                current_widget.edit.setFocus()

    def _apply_tab_font(self, font):
        use_theme_font = getattr(self, '_use_theme_font_on_tab_label', True)
        if use_theme_font:
            tab_font = QFont(font)
            family = tab_font.family()
        else:
            tab_font = QApplication.font("QTabBar")
            family = tab_font.family() or "sans-serif"

        pt_size = tab_font.pointSizeF()
        custom_size = getattr(self, '_tab_text_size', None)
        if custom_size is None:
            if pt_size > 0:
                custom_size = pt_size * 0.8
            else:
                custom_size = tab_font.pixelSize() * 0.8 if tab_font.pixelSize() > 0 else 10.0

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

        css = "\n/*TAB_FONT_START*/\nQTabBar::tab { font-family: '%s'; %s }\nQTabBar::scroller { width: 0px; }\n/*TAB_FONT_END*/\n" % (family, size_css)
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
        prefer_single_quotes = self.p.preferSingleQuotes_act.isChecked() if hasattr(self.p, 'preferSingleQuotes_act') else False
        self.current().addQuotesSelected(prefer_single_quotes)

    def fString(self):
        prefer_single_quotes = self.p.preferSingleQuotes_act.isChecked() if hasattr(self.p, 'preferSingleQuotes_act') else False
        self.current().fStringSelected(prefer_single_quotes)

    def selectNextOccurrence(self):
        self.current().select_next_occurrence()

    def selectAllOccurrences(self):
        self.current().select_all_occurrences()

    def nextSelection(self):
        self.current().next_selection()

    def previousSelection(self):
        self.current().previous_selection()

    def addCursorsToLineEnds(self):
        self.current().add_cursors_to_line_ends()

    def addCursorAbove(self):
        self.current().add_cursor_above()

    def addCursorBelow(self):
        self.current().add_cursor_below()



    def yes_no_question(self, question):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Multi Script Editor")
        msg_box.setText(question)
        if hasattr(self.p, 'theme_font'):
            msg_box.setFont(self.p.theme_font)
        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        msg_box.addButton("No", QMessageBox.NoRole)
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
            self.edit.document().clearUndoRedoStacks()
            self.edit.document().setModified(False)
        self.lineNum = numBarWidget.lineNumberBarClass(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda :self.lineNum.update())
        self.edit.inputSignal.connect(lambda :self.lineNum.update())
        self.edit.document().blockCountChanged.connect(lambda :self.lineNum.update())
        self.edit.cursorPositionChanged.connect(lambda :self.lineNum.update())

        hbox.addWidget(self.lineNum)
        hbox.addWidget(self.edit)


if __name__ == '__main__':
    app = QApplication([])
    w = tabWidgetClass()
    w.show()
    app.exec_()
