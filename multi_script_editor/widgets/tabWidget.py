import os
import re

from vendor.Qt.QtCore import QEvent, QRectF, QSize, Qt, QTimer, Signal
from vendor.Qt.QtGui import (
    QColor,
    QCursor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QTextCursor,
)

from vendor.Qt.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
from core.git_manager import GitManager
from core.diff_manager import DiffManager
from icons import icons
from widgets import inputWidget, numBarWidget
from widgets.breadcrumbsWidget import BreadcrumbBar
from widgets.git_dialogs import GitCommitDialog, GitHistoryDialog
from widgets.pythonSyntax import design


class TabCloseButton(QPushButton):
    """
    Custom close button for editor tabs.
    Displays Git status code (e.g. 'M', 'U', 'A') when in Git repo and modified,
    dirty circle dot when unsaved, and close icon ('x') on hover.
    """
    def __init__(self, parent=None, colors=None):
        super(TabCloseButton, self).__init__(parent)
        self.setObjectName("CustomCloseBtn")
        self.setFixedSize(20, 20)
        self.setMouseTracking(True)
        self._git_status_code = ""
        self._is_dirty = False
        self._is_selected = False
        self._colors = colors or {}
        self._close_icon = None
        self._close_icon_grey = None
        self._load_icons()

    def _load_icons(self):
        try:
            p1 = icons.get('close_tab')
            p2 = icons.get('close_tab_grey')
            if p1 and os.path.exists(p1):
                self._close_icon = QIcon(p1)
            if p2 and os.path.exists(p2):
                self._close_icon_grey = QIcon(p2)
        except Exception:
            pass

    def set_colors(self, colors):
        self._colors = colors or {}
        self.update()

    def set_git_status_code(self, status_code):
        if self._git_status_code != status_code:
            self._git_status_code = status_code
            self.update()

    def set_dirty(self, state):
        if self._is_dirty != state:
            self._is_dirty = state
            self.update()

    def set_selected(self, state):
        if self._is_selected != state:
            self._is_selected = state
            self.update()

    def enterEvent(self, event):
        super(TabCloseButton, self).enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super(TabCloseButton, self).leaveEvent(event)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        is_hovered = self.underMouse()
        has_git = bool(self._git_status_code and self._git_status_code != 'CLEAN')

        if is_hovered:
            bg_color = QColor(*self._colors.get('background', [60, 60, 60])) if isinstance(self._colors.get('background'), list) else QColor(60, 60, 60)
            if bg_color.isValid():
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_color)
                painter.drawRoundedRect(self.rect(), 3, 3)

            icon = self._close_icon or self._close_icon_grey
            if icon and not icon.isNull():
                icon.paint(painter, self.rect())
            else:
                painter.setPen(QColor(200, 200, 200))
                font = painter.font()
                font.setBold(True)
                font.setPointSize(10)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, "×")
        elif has_git:
            code = self._git_status_code
            if 'U' in code or 'A' in code:
                text_color = QColor('#73c991')
            elif 'M' in code or 'S' in code:
                text_color = QColor('#e2c08d')
            elif 'D' in code:
                text_color = QColor('#e06c75')
            else:
                text_color = QColor('#888888')

            painter.setPen(text_color)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, code)
        elif self._is_dirty:
            dirty_color = self._colors.get('tab_selected_text', self._colors.get('window', [200, 200, 200]))
            if isinstance(dirty_color, (list, tuple)):
                painter.setBrush(QColor(*dirty_color))
            elif isinstance(dirty_color, QColor):
                painter.setBrush(dirty_color)
            elif isinstance(dirty_color, str):
                painter.setBrush(QColor(dirty_color))
            else:
                painter.setBrush(QColor(200, 200, 200))
            painter.setPen(Qt.NoPen)
            r = min(self.width(), self.height()) / 4.0
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2.0, r * 2.0))
        else:
            if self._is_selected:
                icon = self._close_icon or self._close_icon_grey
            else:
                icon = self._close_icon_grey or self._close_icon

            if icon and not icon.isNull():
                icon.paint(painter, self.rect())
            else:
                painter.setPen(QColor(150, 150, 150) if not self._is_selected else QColor(220, 220, 220))
                font = painter.font()
                font.setBold(True)
                font.setPointSize(10)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, "×")
        painter.end()


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
        self.setAcceptDrops(True)
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

        self.toggleExplorer_btn = QPushButton(self.corner_widget)
        self.toggleExplorer_btn.setMaximumWidth(30)
        self.toggleExplorer_btn.setCursor(Qt.ArrowCursor)
        self.toggleExplorer_btn.setIcon(QIcon(icons.get('explorer_panel', icons.get('open', ''))))
        self.toggleExplorer_btn.setIconSize(QSize(24, 24))
        self.toggleExplorer_btn.setToolTip("Toggle Explorer (Ctrl+E)")
        self.toggleExplorer_btn.setStatusTip("Show or hide the file explorer panel")
        self.toggleExplorer_btn.setCheckable(True)
        self.toggleExplorer_btn.toggled.connect(self.toggle_explorer)

        newTabButton = QPushButton(self.corner_widget)
        newTabButton.setMaximumWidth(30)
        newTabButton.setCursor(Qt.ArrowCursor)
        newTabButton.setIcon(QIcon(icons['add_tab']))
        newTabButton.setIconSize(QSize(24, 24))
        newTabButton.clicked.connect(lambda checked=False: self.addNewTab())
        newTabButton.setToolTip("New Tab (Ctrl+T)")
        newTabButton.setStatusTip("Open a new empty editor tab")
        newTabButton.setShortcut('Ctrl+T')

        self.corner_layout.addWidget(self.toggleExplorer_btn)
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
            try:
                quick_tab_switching = self.p.quickTabSwitching_act.isChecked()
            except RuntimeError:
                quick_tab_switching = False

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

    def toggle_explorer(self, state):
        if hasattr(self.p, 'toggleExplorer'):
            self.p.toggleExplorer(state)

    def onTabChanged(self, index):
        self.hideAllCompleters()
        if index >= 0:
            self.update_tab_git_status(index)
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
                            edit.verticalScrollBar().setValue(scroll_v)

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
        target_index = i - 1 if i > 0 else 0

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
            else:
                target_index = min(target_index, self.count() - 1)
                self.setCurrentIndex(target_index)

            current_widget = self.currentWidget()
            if current_widget and hasattr(current_widget, 'edit'):
                current_widget.edit.setFocus()

    def closeOtherTabs(self, keep_index=None):
        if keep_index is None or isinstance(keep_index, bool):
            keep_index = self.currentIndex()
        keep_widget = self.widget(keep_index)
        for i in range(self.count() - 1, -1, -1):
            if self.widget(i) != keep_widget:
                self.closeTab(i)

    def closeAllTabs(self):
        for i in range(self.count() - 1, -1, -1):
            self.closeTab(i)

    def openMenu(self, pos=None):
        if pos is not None and not isinstance(pos, bool):
            index = self.tabBar().tabAt(pos)
        else:
            index = self.currentIndex()

        if index < 0:
            return

        widget = self.widget(index)
        has_file = hasattr(widget, 'file_path') and bool(widget.file_path)

        menu = QMenu(self)

        def on_hover(action):
            if hasattr(self.p, 'statusBar'):
                if action and action.statusTip():
                    if getattr(self.p, '_show_status_tips', True):
                        self.p.statusBar().showMessage(action.statusTip())
                else:
                    self.p.statusBar().clearMessage()

        menu.hovered.connect(on_hover)

        if hasattr(self.p, 'menubar') and self.p.menubar:
            menu.setFont(self.p.menubar.font())
            menu.setStyleSheet(self.p.menubar.styleSheet())

        # Git menu (if file exists in git repo and version control is enabled)
        if has_file and getattr(self.p, '_version_control_enabled', False):
            file_path = getattr(widget, 'file_path', None)
            if file_path and os.path.exists(file_path):
                if GitManager.is_in_repo(file_path):
                    git_menu = menu.addMenu('Git')
                    if hasattr(self.p, 'menubar') and self.p.menubar:
                        git_menu.setFont(self.p.menubar.font())
                        git_menu.setStyleSheet(self.p.menubar.styleSheet())
                    elif menu.font():
                        git_menu.setFont(menu.font())
                        git_menu.setStyleSheet(menu.styleSheet())
                    if 'git' in icons:
                        git_menu.setIcon(QIcon(icons['git']))
                    git_menu.hovered.connect(on_hover)
                    self.build_git_menu(git_menu, index)
                    menu.addSeparator()

        # Tab management actions (available for all tabs)
        close_action = QAction('Close Tab', self)
        close_action.setShortcut('Ctrl+W')
        if 'close_tab' in icons:
            close_action.setIcon(QIcon(icons['close_tab']))
        close_action.triggered.connect(lambda checked=False, idx=index: self.closeTab(idx))
        menu.addAction(close_action)

        if self.count() > 1:
            close_others_action = QAction('Close Other Tabs', self)
            if 'close_other_tabs' in icons:
                close_others_action.setIcon(QIcon(icons['close_other_tabs']))
            close_others_action.triggered.connect(lambda checked=False, idx=index: self.closeOtherTabs(idx))
            menu.addAction(close_others_action)

            close_all_action = QAction('Close All Tabs', self)
            if 'close_all_tabs' in icons:
                close_all_action.setIcon(QIcon(icons['close_all_tabs']))
            close_all_action.triggered.connect(lambda checked=False: self.closeAllTabs())
            menu.addAction(close_all_action)

        menu.addSeparator()

        dup_title = 'Duplicate file' if has_file else 'Duplicate Tab'
        dup_action = QAction(dup_title, self)
        if 'duplicate_file' in icons:
            dup_action.setIcon(QIcon(icons['duplicate_file']))
        dup_action.triggered.connect(lambda checked=False, idx=index: self.duplicateTab(idx))
        menu.addAction(dup_action)

        ren_title = 'Rename File' if has_file else 'Rename Tab'
        ren_action = QAction(ren_title, self)
        ren_action.setShortcut('Alt+R')
        if 'rename_file' in icons:
            ren_action.setIcon(QIcon(icons['rename_file']))
        ren_action.triggered.connect(lambda checked=False, idx=index: self.renameTab(idx))
        menu.addAction(ren_action)

        # File specific actions (only when tab has a file_path)
        if has_file:
            menu.addSeparator()

            copy_action = QAction('Copy file path', self)
            copy_action.setShortcut('Alt+Shift+C')
            if 'copy' in icons:
                copy_action.setIcon(QIcon(icons['copy']))
            copy_action.triggered.connect(lambda checked=False, idx=index: self.copyFilePath(idx))
            menu.addAction(copy_action)

            del_action = QAction('Delete file', self)
            if 'delete_file' in icons:
                del_action.setIcon(QIcon(icons['delete_file']))
            del_action.triggered.connect(lambda checked=False, idx=index: self.deleteFile(idx))
            menu.addAction(del_action)

            compare_menu = menu.addMenu('Compare with...')
            if 'git_diff' in icons:
                compare_menu.setIcon(QIcon(icons['git_diff']))
            if hasattr(self.p, 'menubar') and self.p.menubar:
                compare_menu.setFont(self.p.menubar.font())
                compare_menu.setStyleSheet(self.p.menubar.styleSheet())
            elif menu.font():
                compare_menu.setFont(menu.font())
                compare_menu.setStyleSheet(menu.styleSheet())
            compare_menu.hovered.connect(on_hover)
            self.build_compare_menu(compare_menu, index)

        if hasattr(self.p, 'menubar') and not self.p.menubar.isVisible():
            menu.addSeparator()
            show_menus_action = QAction("Show menus\tCtrl+Alt+M", self)
            if 'menu' in icons:
                show_menus_action.setIcon(QIcon(icons['menu']))
            if hasattr(self.p, 'toggleMenus_act'):
                show_menus_action.triggered.connect(self.p.toggleMenus_act.trigger)
            menu.addAction(show_menus_action)

        menu.exec_(QCursor.pos())

    def build_git_menu(self, git_menu, index):
        widget = self.widget(index)
        file_path = getattr(widget, 'file_path', None)
        if not file_path:
            return

        if hasattr(self.p, 'menubar') and self.p.menubar:
            git_menu.setFont(self.p.menubar.font())
            git_menu.setStyleSheet(self.p.menubar.styleSheet())
        elif git_menu.parentWidget() and hasattr(git_menu.parentWidget(), 'font'):
            git_menu.setFont(git_menu.parentWidget().font())
            git_menu.setStyleSheet(git_menu.parentWidget().styleSheet())

        status_info = GitManager.get_file_status(file_path)
        branch = status_info.get('branch', 'HEAD')
        status_text = status_info.get('status_text', 'Clean')

        branch_act = git_menu.addAction(f"Branch: {branch} ({status_text})")
        branch_act.setStatusTip("Current branch and file status")
        branch_act.setEnabled(False)
        if 'git_branch' in icons:
            branch_act.setIcon(QIcon(icons['git_branch']))
        git_menu.addSeparator()

        commit_act = git_menu.addAction("Commit File...")
        commit_act.setStatusTip("Commit this file")
        if 'git_commit' in icons:
            commit_act.setIcon(QIcon(icons['git_commit']))
        commit_act.triggered.connect(lambda checked=False, fp=file_path: self.git_commit_dialog(fp))

        if status_info.get('is_modified'):
            discard_act = git_menu.addAction("Discard Changes...")
            discard_act.setStatusTip("Discard local changes to this file")
            if 'git_discard' in icons:
                discard_act.setIcon(QIcon(icons['git_discard']))
            discard_act.triggered.connect(lambda checked=False, idx=index, fp=file_path: self.git_discard_changes(idx, fp))

        diff_act = git_menu.addAction("Git Diff (vs HEAD)")
        diff_act.setStatusTip("Compare current file with HEAD revision")
        if 'git_diff' in icons:
            diff_act.setIcon(QIcon(icons['git_diff']))
        diff_act.triggered.connect(lambda checked=False, fp=file_path: self.run_git_diff(fp))

        if status_info.get('is_staged'):
            unstage_act = git_menu.addAction("Unstage File")
            unstage_act.setStatusTip("Unstage this file")
            if 'git_unstage' in icons:
                unstage_act.setIcon(QIcon(icons['git_unstage']))
            unstage_act.triggered.connect(lambda checked=False, fp=file_path: self.git_unstage(fp))
        else:
            stage_act = git_menu.addAction("Stage File")
            stage_act.setStatusTip("Stage this file for commit")
            if 'git_stage' in icons:
                stage_act.setIcon(QIcon(icons['git_stage']))
            stage_act.triggered.connect(lambda checked=False, fp=file_path: self.git_stage(fp))

        git_menu.addSeparator()

        rel_path = status_info.get('relative_path', '')
        if rel_path:
            copy_rel_act = git_menu.addAction("Copy Path Relative to Repo")
            copy_rel_act.setStatusTip("Copy file path relative to repository root")
            if 'copy' in icons:
                copy_rel_act.setIcon(QIcon(icons['copy']))
            copy_rel_act.triggered.connect(lambda checked=False, rp=rel_path: QApplication.clipboard().setText(rp))

        log_act = git_menu.addAction("File History / Log...")
        log_act.setStatusTip("View file history and commits")
        if 'git_history' in icons:
            log_act.setIcon(QIcon(icons['git_history']))
        log_act.triggered.connect(lambda checked=False, fp=file_path: self.git_history_dialog(fp))


    def run_git_diff(self, file_path):
        head_path = GitManager.get_head_file_temp_path(file_path)
        if head_path and os.path.exists(head_path):
            DiffManager.run_diff(head_path, file_path, parent=self.p)
        else:
            QMessageBox.information(self, "Git Diff", "No previous HEAD revision found for this file.")

    def git_stage(self, file_path):
        success, msg = GitManager.stage_file(file_path)
        self.update_tab_git_status(self.currentIndex())
        if hasattr(self.p, 'updateStatusBarInfo'):
            self.p.updateStatusBarInfo()

    def git_unstage(self, file_path):
        success, msg = GitManager.unstage_file(file_path)
        self.update_tab_git_status(self.currentIndex())
        if hasattr(self.p, 'updateStatusBarInfo'):
            self.p.updateStatusBarInfo()

    def git_commit_dialog(self, file_path):
        dlg = GitCommitDialog(parent=self.p, file_path=file_path)
        if dlg.exec_():
            self.update_tab_git_status(self.currentIndex())
            if hasattr(self.p, 'updateStatusBarInfo'):
                self.p.updateStatusBarInfo()

    def git_history_dialog(self, file_path):
        dlg = GitHistoryDialog(parent=self.p, file_path=file_path)
        dlg.exec_()

    def _apply_parent_theme_font(self, widget, fallback_font=None):
        font = getattr(self.p, 'theme_font', None) or fallback_font
        if not font:
            return
        widget.setFont(font)
        size_css = f" font-size: {font.pointSize()}pt;" if font.pointSize() > 0 else ""
        widget.setStyleSheet(f"* {{ font-family: '{font.family()}';{size_css} }}")
        for child in widget.findChildren(QWidget):
            child.setFont(font)
        if hasattr(widget, 'buttons'):
            for btn in widget.buttons():
                btn.setFont(font)

    def git_discard_changes(self, index, file_path):
        if hasattr(self.p, 'show_question_msg'):
            reply = self.p.show_question_msg(
                "Discard Changes",
                f"Are you sure you want to discard working modifications to:\n{file_path}?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Discard Changes")
            msg_box.setText(f"Are you sure you want to discard working modifications to:\n{file_path}?\n\nThis action cannot be undone.")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            btn = msg_box.button(QMessageBox.Yes)
            if btn:
                msg_box.setDefaultButton(btn)
                btn.setFocus()
            else:
                msg_box.setDefaultButton(QMessageBox.Yes)
            fallback_font = getattr(self.p, 'current_outline_font', self.font())
            self._apply_parent_theme_font(msg_box, fallback_font)
            reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            success, msg = GitManager.discard_changes(file_path)
            if success:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    w = self.widget(index)
                    if hasattr(w, 'edit') and w.edit:
                        w.edit.setText(text)
                        w.edit.document().setModified(False)
                except Exception:
                    pass
                self.update_tab_git_status(index)
                if hasattr(self.p, 'updateStatusBarInfo'):
                    self.p.updateStatusBarInfo()

    def update_tab_git_status(self, index):
        if index < 0 or index >= self.count():
            return
        widget = self.widget(index)
        file_path = getattr(widget, 'file_path', None)
        btn = getattr(widget, '_custom_close_btn', None)

        if not file_path or not os.path.exists(file_path):
            if btn and hasattr(btn, 'set_git_status_code'):
                btn.set_git_status_code("")
            return

        norm_path = os.path.normpath(file_path)
        if not getattr(self.p, '_version_control_enabled', False):
            self.setTabToolTip(index, norm_path)
            if btn and hasattr(btn, 'set_git_status_code'):
                btn.set_git_status_code("")
            return

        status_info = GitManager.get_file_status(file_path)
        git_code = ""
        if status_info.get('in_repo'):
            tooltip = f"{norm_path}\nGit: {status_info['branch']} [{status_info['status_text']}]"
            git_code = status_info.get('status_code', '')
            if git_code == 'CLEAN':
                git_code = ''
        else:
            tooltip = norm_path

        self.setTabToolTip(index, tooltip)
        if btn and hasattr(btn, 'set_git_status_code'):
            btn.set_git_status_code(git_code)

    def update_all_tabs_git_status(self):
        for i in range(self.count()):
            self.update_tab_git_status(i)

    def build_compare_menu(self, compare_menu, index):
        if index < 0 or index >= self.count():
            return

        current_widget = self.widget(index)
        current_file = getattr(current_widget, 'file_path', "")

        # 1. List other open tabs with file paths
        other_tabs_count = 0
        for i in range(self.count()):
            if i == index:
                continue
            w = self.widget(i)
            other_file = getattr(w, 'file_path', "")
            if other_file and os.path.exists(other_file):
                other_tabs_count += 1
                tab_title = self.tabText(i)
                act_text = f"{tab_title}  ({other_file})"
                act = compare_menu.addAction(act_text)
                act.triggered.connect(
                    lambda checked=False, f1=current_file, f2=other_file: DiffManager.run_diff(
                        f1, f2, parent=self.p
                    )
                )

        if other_tabs_count == 0:
            no_act = compare_menu.addAction("No other open saved files")
            no_act.setEnabled(False)

        compare_menu.addSeparator()

        # 2. Browse File option
        browse_file_act = compare_menu.addAction("Browse File...")
        def _browse_file(checked=False, f1=current_file):
            path, _ = QFileDialog.getOpenFileName(self, "Select File to Compare")
            if path:
                DiffManager.run_diff(f1, path, parent=self.p)
        browse_file_act.triggered.connect(_browse_file)

        compare_menu.addSeparator()

        # 4. Configure Diff Tool option
        cfg_act = compare_menu.addAction("Configure Diff Tool...")
        cfg_act.triggered.connect(lambda checked=False: DiffManager.configure_diff_tool(parent=self.p))

    def deleteFile(self, index=None):
        if index is None or isinstance(index, bool):
            index = self.currentIndex()
        if index < 0:
            return
        widget = self.widget(index)
        if not (hasattr(widget, 'file_path') and widget.file_path):
            return

        file_path = widget.file_path
        filename = os.path.basename(file_path)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Delete File')
        msg_box.setText('Are you sure you want to delete "%s" from disk?' % filename)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        self._apply_parent_theme_font(msg_box)

        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                widget.file_path = None
                if hasattr(widget, 'edit') and hasattr(widget.edit, 'document'):
                    widget.edit.document().setModified(False)
                self.closeTab(index)
                if hasattr(self.p, 'out'):
                    self.p.out.showMessage('Deleted file: %s' % os.path.normpath(file_path))
                elif hasattr(self.p, 'showStatusMessage'):
                    self.p.showStatusMessage('Deleted file: %s' % os.path.normpath(file_path))
            except Exception as e:
                err_box = QMessageBox(self)
                err_box.setIcon(QMessageBox.Critical)
                err_box.setWindowTitle('Delete File Error')
                err_box.setText('Could not delete file:\n%s' % str(e))
                self._apply_parent_theme_font(err_box)
                err_box.exec_()

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
        widget = self.widget(index)
        text = self.getCurrentText(index)
        old_path = getattr(widget, 'file_path', None) if widget else None
        target_index = index + 1

        if old_path:
            dir_name = os.path.dirname(old_path)
            base_name, ext = os.path.splitext(os.path.basename(old_path))
            copy_name = "%s (copy)%s" % (base_name, ext)
            new_path = os.path.join(dir_name, copy_name)
            counter = 2
            while os.path.exists(new_path):
                copy_name = "%s (copy %d)%s" % (base_name, counter, ext)
                new_path = os.path.join(dir_name, copy_name)
                counter += 1

            try:
                with open(new_path, 'w') as f:
                    f.write(text or '')
                new_tab_name = os.path.basename(new_path)
                self.addNewTab(new_tab_name, text, file_path=new_path, insert_index=target_index)
                norm_new_path = os.path.normpath(new_path)
                if hasattr(self.p, 'out'):
                    self.p.out.showMessage('Duplicated file saved to: %s' % norm_new_path)
                elif hasattr(self.p, 'showStatusMessage'):
                    self.p.showStatusMessage('Duplicated file saved to: %s' % norm_new_path)
            except Exception as e:
                if hasattr(self.p, 'out'):
                    self.p.out.showMessage('Error duplicating file: %s' % str(e))
                name = self.tabText(index) + " (copy)"
                self.addNewTab(name, text, insert_index=target_index)
        else:
            name = self.tabText(index) + " (copy)"
            self.addNewTab(name, text, insert_index=target_index)

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
                new_text = edit.text().strip()
                idx = self.indexOf(widget)
                if new_text and idx >= 0:
                    old_path = getattr(widget, 'file_path', None)
                    if old_path:
                        dir_name = os.path.dirname(old_path)
                        _, old_ext = os.path.splitext(os.path.basename(old_path))
                        new_base, new_ext = os.path.splitext(new_text)

                        # Preserve original extension if not provided in new_text
                        if not new_ext and old_ext:
                            new_text = new_text + old_ext

                        new_path = os.path.join(dir_name, new_text)
                        norm_new_path = os.path.normpath(new_path)

                        if os.path.normpath(old_path) != norm_new_path:
                            if os.path.exists(old_path):
                                try:
                                    os.rename(old_path, new_path)
                                    widget.file_path = new_path
                                    self.setTabToolTip(idx, norm_new_path)
                                    self.setTabText(idx, os.path.basename(new_path))
                                    if hasattr(widget, 'edit') and hasattr(widget.edit, 'applyHightLighter') and hasattr(self.p, '_current_settings'):
                                        widget.edit.applyHightLighter(self.p._current_settings.get('theme', 'Multi Script Editor'))
                                    if hasattr(self.p, 'out'):
                                        self.p.out.showMessage('Renamed file to: %s' % norm_new_path)
                                    elif hasattr(self.p, 'showStatusMessage'):
                                        self.p.showStatusMessage('Renamed file to: %s' % norm_new_path)
                                except Exception as e:
                                    if hasattr(self.p, 'out'):
                                        self.p.out.showMessage('Error renaming file: %s' % str(e))
                                    elif hasattr(self.p, 'showStatusMessage'):
                                        self.p.showStatusMessage('Error renaming file: %s' % str(e))
                            else:
                                widget.file_path = new_path
                                self.setTabToolTip(idx, os.path.normpath(new_path))
                                self.setTabText(idx, os.path.basename(new_path))
                        else:
                            self.setTabText(idx, os.path.basename(new_path))
                    else:
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
        tab_font = getattr(self, '_tab_label_font', None) or self.tabBar().font()
        edit.setFont(tab_font)
        family = tab_font.family()
        pt_size = tab_font.pointSizeF()
        px_size = tab_font.pixelSize()
        if pt_size > 0:
            size_css = "font-size: %spt;" % pt_size
        elif px_size > 0:
            size_css = "font-size: %spx;" % px_size
        else:
            size_css = ""

        if family:
            edit.setStyleSheet("QLineEdit#tabRenameEdit { font-family: '%s'; %s }" % (family, size_css))

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

    def addNewTab(self, name='New Tab', text=None, file_path=None, make_current=True, insert_index=None):
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

        cont = EditorTabContainer(
            text,
            self.p,
            self.desk,
            file_path=file_path,
            fallback_name=name,
        )
        cont.edit.saveSignal.connect(self.session_save_requested.emit)
        cont.edit.executeSignal.connect(self.execute_selected_requested.emit)
        if hasattr(self.p, 'showStatusMessage'):
            cont.edit.messageSignal.connect(self.p.showStatusMessage)

        if insert_index is None:
            curr = self.currentIndex()
            if curr >= 0:
                insert_index = curr + 1

        if insert_index is not None and 0 <= insert_index <= self.count():
            self.insertTab(insert_index, cont, name)
        else:
            self.addTab(cont, name)

        new_index = self.indexOf(cont)

        colors = {}
        if hasattr(self.p, '_presenter'):
            theme_name = self.p._presenter.settings_model.read_settings().get('theme', 'Multi Script Editor')
            colors = design.getColors(theme_name)

        btn = TabCloseButton(colors=colors)
        btn.set_selected(new_index == self.currentIndex())
        btn.clicked.connect(lambda checked=False, c=cont: self.tabCloseRequested.emit(self.indexOf(c)))
        self.tabBar().setTabButton(new_index, QTabBar.RightSide, btn)
        cont._custom_close_btn = btn

        if file_path:
            self.setTabToolTip(new_index, os.path.normpath(file_path))
            self.update_tab_git_status(new_index)

        if hasattr(self.p, 'updateStatusBarInfo'):
            cont.edit.cursorPositionChanged.connect(self.p.updateStatusBarInfo)
            cont.edit.textChanged.connect(self.p.updateStatusBarInfo)

        cont.edit.document().modificationChanged.connect(lambda state, c=cont: self.mark_tab_dirty(c, state))
        cont.edit.moveCursor(QTextCursor.Start)
        cont.edit.highlight_current_line()
        if make_current:
            self.setCurrentIndex(new_index)

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

        cont.edit.setFocus()

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

    def _iter_editors(self):
        for i in range(self.count()):
            widget = self.widget(i)
            if widget and hasattr(widget, 'edit'):
                yield widget.edit

    def hideAllCompleters(self):
        for editor in self._iter_editors():
            editor.completer.hideMe()

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

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(tabWidgetClass, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(tabWidgetClass, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.exists(file_path):
                        if os.path.isfile(file_path):
                            if hasattr(self.p, 'loadScript'):
                                self.p.loadScript(file_path)
                            elif hasattr(self.p, 'openRecentFile'):
                                self.p.openRecentFile(file_path)
                        elif os.path.isdir(file_path):
                            if hasattr(self.p, 'explorer_widget'):
                                self.p.explorer_widget.set_root_path(file_path)
            return
        super(tabWidgetClass, self).dropEvent(event)

############################## editor commands
    def update_custom_close_buttons(self, index=None):
        for i in range(self.count()):
            cont = self.widget(i)
            if hasattr(cont, '_custom_close_btn'):
                btn = cont._custom_close_btn
                is_sel = (i == self.currentIndex())
                if hasattr(btn, 'set_selected'):
                    btn.set_selected(is_sel)
                else:
                    btn.setProperty('isSelected', is_sel)
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)

    def mark_tab_dirty(self, container, state):
        if not hasattr(container, '_custom_close_btn'):
            return

        btn = container._custom_close_btn
        if hasattr(btn, 'set_dirty'):
            btn.set_dirty(state)
            return

        btn.setProperty('isDirty', state)

        if state:
            theme_name = 'Multi Script Editor'
            if hasattr(self.p, '_presenter'):
                theme_name = self.p._presenter.settings_model.read_settings().get('theme', theme_name)
            colors = design.getColors(theme_name)
            dirty_color = colors.get('tab_selected_text', colors.get('window', [200, 200, 200]))

            pixmap = QPixmap(btn.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            if isinstance(dirty_color, (list, tuple)):
                painter.setBrush(QColor(*dirty_color))
            elif isinstance(dirty_color, QColor):
                painter.setBrush(dirty_color)
            elif isinstance(dirty_color, str):
                painter.setBrush(QColor(dirty_color))
            else:
                painter.setBrush(QColor(200, 200, 200))
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
            colors = design.defaultColors

        self._use_theme_font_on_tab_label = colors.get('use_theme_font_on_tab_label', True)

        for i in range(self.count()):
            cont = self.widget(i)
            if hasattr(cont, '_custom_close_btn') and hasattr(cont._custom_close_btn, 'set_colors'):
                cont._custom_close_btn.set_colors(colors)

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

        self._tab_label_font = QFont(tab_font)
        self.tabBar().setFont(tab_font)

        css = "\n/*TAB_FONT_START*/\nQTabBar::tab { font-family: '%s'; %s }\nQTabBar::scroller { width: 0px; }\n/*TAB_FONT_END*/\n" % (family, size_css)
        ss = self.styleSheet()
        ss = re.sub(r'/\*TAB_FONT_START\*/.*/\*TAB_FONT_END\*/', '', ss, flags=re.DOTALL)
        self.setStyleSheet(ss + css)

    def render_whitespace(self, state):
        for current_edit in self._iter_editors():
            current_edit.render_whitespace(state)

    def wordWrap(self, state):
        for current_edit in self._iter_editors():
            current_edit.wordWrap(state)
        # update line numbers
        self.update()

    def set_font(self, font):
        self._apply_tab_font(font)
        for current_edit in self._iter_editors():
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
        for current_edit in self._iter_editors():
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
        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        msg_box.addButton("No", QMessageBox.NoRole)
        yes_button.setFocus()
        self._apply_parent_theme_font(msg_box)
        msg_box.exec_()
        return msg_box.clickedButton() == yes_button


class EditorTabContainer(QWidget):
    def __init__(
        self,
        text,
        parent,
        desk,
        file_path=None,
        fallback_name="Untitled",
    ):
        super(EditorTabContainer, self).__init__()
        self.file_path = file_path
        self.setMinimumWidth(0)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Breadcrumbs Bar
        self.breadcrumbs = BreadcrumbBar(
            self,
            file_path=file_path,
            fallback_name=fallback_name,
        )
        self.breadcrumbs.symbolSelected.connect(self._on_breadcrumb_symbol_selected)
        self.breadcrumbs.fileSelected.connect(self._on_breadcrumb_file_selected)
        show_b = False
        if hasattr(parent, 'showBreadcrumbs_act'):
            show_b = parent.showBreadcrumbs_act.isChecked()
        self.breadcrumbs.setVisible(show_b)
        vbox.addWidget(self.breadcrumbs)

        editor_hbox = QHBoxLayout()
        editor_hbox.setSpacing(0)
        editor_hbox.setContentsMargins(0, 2, 0, 0)

        # Input widget
        self.edit = inputWidget.inputClass(parent, desk)
        if text:
            self.edit.addText(text)
            self.edit.document().clearUndoRedoStacks()
            self.edit.document().setModified(False)
        self.lineNum = numBarWidget.lineNumberBarClass(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda: self.lineNum.update())
        self.edit.inputSignal.connect(lambda: self.lineNum.update())
        self.edit.document().blockCountChanged.connect(lambda: self.lineNum.update())
        self.edit.cursorPositionChanged.connect(lambda: self.lineNum.update())
        self.edit.cursorPositionChanged.connect(self._on_cursor_changed_update_breadcrumbs)
        self._initial_horizontal_scroll_pending = True

        editor_hbox.addWidget(self.lineNum)
        editor_hbox.addWidget(self.edit)

        vbox.addLayout(editor_hbox)

    def showEvent(self, event):
        super(EditorTabContainer, self).showEvent(event)
        if self._initial_horizontal_scroll_pending:
            QTimer.singleShot(0, self._restore_initial_horizontal_scroll)

    def _restore_initial_horizontal_scroll(self):
        if not self.isVisible():
            return
        self._initial_horizontal_scroll_pending = False
        self.edit.reset_horizontal_scroll_for_cursor()

    def _on_cursor_changed_update_breadcrumbs(self):
        line_num = self.edit.textCursor().blockNumber() + 1
        self.breadcrumbs.set_cursor_line(line_num)

    def _on_breadcrumb_symbol_selected(self, line):
        if line:
            block = self.edit.document().findBlockByNumber(line - 1)
            if block.isValid():
                cursor = self.edit.textCursor()
                cursor.setPosition(block.position())
                self.edit.setTextCursor(cursor)
                self.edit.centerCursor()
                self.edit.highlight_current_line()
                self.edit.setFocus()

    def _on_breadcrumb_file_selected(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return

        parent = getattr(self.edit, 'p', None)
        if not parent:
            return

        if hasattr(parent, 'tab'):
            tab_widget = parent.tab
            for i in range(tab_widget.count()):
                container = tab_widget.widget(i)
                if container and getattr(container, 'file_path', None) == file_path:
                    tab_widget.setCurrentIndex(i)
                    return

        if hasattr(parent, 'openRecentFile'):
            parent.openRecentFile(file_path)

        self.edit.setFocus()

if __name__ == '__main__':
    app = QApplication([])
    w = tabWidgetClass()
    w.show()
    app.exec_()
