import os

from icons import icons
from vendor.Qt.QtCore import QFileInfo, QSize, Qt, Signal
from vendor.Qt.QtGui import QColor, QFont, QIcon
from vendor.Qt.QtWidgets import (
    QAction,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QWidget,
)
from widgets.outline_utils import get_symbol_type_icon


_icon_provider = None


def get_system_icon_provider():
    global _icon_provider
    if _icon_provider is None:
        _icon_provider = QFileIconProvider()
    return _icon_provider


def get_folder_icon(dir_path=None):
    provider = get_system_icon_provider()
    if dir_path and os.path.exists(dir_path):
        return provider.icon(QFileInfo(dir_path))
    return provider.icon(QFileIconProvider.Folder)


def get_file_icon(file_path=None):
    provider = get_system_icon_provider()
    if file_path and os.path.exists(file_path):
        return provider.icon(QFileInfo(file_path))
    return provider.icon(QFileIconProvider.File)


def clean_symbol_name(name, sym_type):
    """
    Strips 'class ', 'def ', 'async def ', etc. prefixes for clean breadcrumb display.
    """
    clean = name or ""
    for prefix in ['class ', 'async def ', 'def ', 'function ', 'struct ', 'enum ']:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    if clean.endswith('='):
        clean = clean.rstrip('=').rstrip()
    return clean


def split_path_into_components(full_path):
    """
    Decomposes an absolute file path into a list of (display_name, absolute_path, is_dir) tuples.
    """
    if not full_path or not os.path.isabs(full_path):
        return []

    norm = os.path.normpath(full_path)
    parts = []
    curr = norm

    while True:
        parent, name = os.path.split(curr)
        if name:
            is_dir = os.path.isdir(curr)
            parts.insert(0, (name, curr, is_dir))
            curr = parent
        else:
            if curr:
                title = curr.rstrip('\\').rstrip('/') or curr
                parts.insert(0, (title, curr, os.path.isdir(curr)))
            break

    return parts


def populate_dir_menu(menu, dir_path, on_file_selected, theme_colors=None, font=None):
    """
    Dynamically populates a QMenu with subdirectories and files of dir_path.
    """
    menu.clear()
    try:
        entries = os.listdir(dir_path)
    except Exception:
        return

    dirs = []
    files = []
    for entry in entries:
        if entry.startswith('.'):
            continue
        p = os.path.join(dir_path, entry)
        if os.path.isdir(p):
            dirs.append((entry, p))
        else:
            files.append((entry, p))

    dirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())

    for name, p in dirs:
        sub_menu = QMenu(name, menu)
        sub_menu.setIcon(get_folder_icon(p))
        if font:
            sub_menu.setFont(font)
        sub_menu.menuAction().setStatusTip("Browse folder {0}".format(name))
        sub_menu.aboutToShow.connect(
            lambda m=sub_menu, path=p: populate_dir_menu(m, path, on_file_selected, theme_colors, font)
        )
        menu.addMenu(sub_menu)

    if dirs and files:
        menu.addSeparator()

    for name, p in files:
        file_icon = get_file_icon(p)
        act = QAction(file_icon, name, menu)
        act.setStatusTip("Open {0}".format(name))
        act.triggered.connect(lambda checked=False, path=p: on_file_selected(path))
        menu.addAction(act)


class BreadcrumbItemWidget(QToolButton):
    """
    Custom button for a single breadcrumb segment (Directory, File, or Code Symbol).
    """
    symbolSelected = Signal(int)
    fileSelected = Signal(str)

    def __init__(self, title, node_type="symbol", path_or_data=None, siblings=None, theme_colors=None, font=None, parent=None):
        super(BreadcrumbItemWidget, self).__init__(parent)
        self.setObjectName("breadcrumbItem")
        self._title = title
        self._node_type = node_type  # 'dir', 'file', or 'symbol'
        self._path_or_data = path_or_data
        self._siblings = siblings or []
        self._theme_colors = theme_colors or {}

        if self._node_type in ["dir", "file"]:
            self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        else:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.setAutoRaise(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if font:
            self.setFont(font)

        self.setText(title)

        if self._node_type == "dir":
            self.setPopupMode(QToolButton.InstantPopup)
            self.setStatusTip("Browse folder {0}".format(title))
            self._setup_lazy_menu(font)

        elif self._node_type == "file":
            self.setPopupMode(QToolButton.MenuButtonPopup if self._siblings else QToolButton.InstantPopup)
            self.setStatusTip("File {0}".format(title))
            self.clicked.connect(self._on_file_clicked)
            if self._siblings:
                self._setup_lazy_menu(font)

        else:
            # Code Symbol Node
            sym_data = path_or_data or {}
            line = sym_data.get('line', 1)
            sym_type = sym_data.get('type', 'function')

            self.setPopupMode(QToolButton.MenuButtonPopup if self._siblings else QToolButton.InstantPopup)
            self.setStatusTip("Jump to {0} (Line {1})".format(title, line))
            self.setIcon(get_symbol_type_icon(sym_type, self._theme_colors))
            self.setIconSize(QSize(16, 16))
            self.clicked.connect(self._on_symbol_clicked)
            if self._siblings:
                self._setup_lazy_menu(font)

    def _setup_lazy_menu(self, font):
        menu = QMenu(self)
        if font:
            menu.setFont(font)
        self._apply_menu_style(menu)
        menu.aboutToShow.connect(self._on_menu_about_to_show)
        self.setMenu(menu)

    def _on_menu_about_to_show(self):
        menu = self.menu()
        if not menu:
            return
        menu.clear()
        font = menu.font()

        if self._node_type == "dir":
            dir_path = self._path_or_data
            if dir_path and os.path.exists(dir_path):
                populate_dir_menu(menu, dir_path, self.fileSelected.emit, self._theme_colors, font)

        elif self._node_type == "file":
            dir_path = os.path.dirname(self._path_or_data) if self._path_or_data else ""
            if dir_path and os.path.exists(dir_path):
                populate_dir_menu(menu, dir_path, self.fileSelected.emit, self._theme_colors, font)

        elif self._node_type == "symbol":
            for sym in self._siblings:
                s_name = sym.get('name', '')
                s_type = sym.get('type', 'function')
                s_line = sym.get('line', 1)
                c_name = clean_symbol_name(s_name, s_type)

                act = QAction(get_symbol_type_icon(s_type, self._theme_colors), c_name, menu)
                act.setStatusTip("Navigate to {0} (Line {1})".format(c_name, s_line))
                act.setData(s_line)
                act.triggered.connect(lambda checked=False, line=s_line: self.symbolSelected.emit(line))
                menu.addAction(act)

    def _apply_menu_style(self, menu):
        bg = self._theme_colors.get('window', self._theme_colors.get('tab_bg', (35, 35, 35)))
        fg = self._theme_colors.get('tab_selected_text', self._theme_colors.get('text', (220, 220, 220)))
        sel_bg = self._theme_colors.get('tab_selected_bg', (60, 60, 60))
        sel_fg = self._theme_colors.get('tab_selected_text', (255, 255, 255))

        bg_hex = "#{:02x}{:02x}{:02x}".format(*bg[:3]) if isinstance(bg, (list, tuple)) else "#232323"
        fg_hex = "#{:02x}{:02x}{:02x}".format(*fg[:3]) if isinstance(fg, (list, tuple)) else "#dcdcdc"
        sel_bg_hex = "#{:02x}{:02x}{:02x}".format(*sel_bg[:3]) if isinstance(sel_bg, (list, tuple)) else "#3c3c3c"
        sel_fg_hex = "#{:02x}{:02x}{:02x}".format(*sel_fg[:3]) if isinstance(sel_fg, (list, tuple)) else "#ffffff"

        style = """
            QMenu {{
                background-color: {0};
                color: {1};
                border: 1px solid #444;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 4px 20px 4px 8px;
                border-radius: 2px;
            }}
            QMenu::item:selected {{
                background-color: {2};
                color: {3};
            }}
        """.format(bg_hex, fg_hex, sel_bg_hex, sel_fg_hex)
        menu.setStyleSheet(style)

    def _on_file_clicked(self):
        if self._path_or_data:
            self.fileSelected.emit(self._path_or_data)

    def _on_symbol_clicked(self):
        line = self._path_or_data.get('line', 1) if isinstance(self._path_or_data, dict) else 1
        self.symbolSelected.emit(line)


class BreadcrumbBar(QScrollArea):
    """
    VSCode-style Breadcrumbs Bar displaying the full directory path, file node, and code symbol scope hierarchy.
    """
    symbolSelected = Signal(int)
    fileSelected = Signal(str)

    def __init__(self, parent=None):
        super(BreadcrumbBar, self).__init__(parent)
        self.setObjectName("breadcrumbBar")
        self.setFixedHeight(26)
        self.setMinimumWidth(0)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setFocusPolicy(Qt.NoFocus)

        self._container = QWidget(self)
        self._container.setObjectName("breadcrumbContainer")

        self.layout = QHBoxLayout(self._container)
        self.layout.setContentsMargins(6, 1, 6, 1)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setWidget(self._container)

        self._raw_symbols = []
        self._file_path = None
        self._fallback_name = "Untitled"
        self._ext = ".py"
        self._current_line = 1
        self._theme_colors = {}
        self._font = None

        self.rebuild_breadcrumbs()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta != 0:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
        else:
            super(BreadcrumbBar, self).wheelEvent(event)

    def minimumSizeHint(self):
        return QSize(0, 26)

    def sizeHint(self):
        return QSize(100, 26)

    def set_font(self, font):
        self._font = font
        if font:
            self.setFont(font)
            self._container.setFont(font)
        self.rebuild_breadcrumbs()

    def apply_theme(self, theme_colors, font=None):
        if theme_colors:
            self._theme_colors = theme_colors
        if font:
            self._font = font
            self.setFont(font)
            self._container.setFont(font)

        bg = self._theme_colors.get('window', self._theme_colors.get('tab_bg', (50, 50, 50)))
        fg = self._theme_colors.get('tab_selected_text', self._theme_colors.get('text', (220, 220, 220)))
        border = self._theme_colors.get('line_number_fg', (70, 70, 70))

        bg_hex = "#{:02x}{:02x}{:02x}".format(*bg[:3]) if isinstance(bg, (list, tuple)) else "#323232"
        fg_hex = "#{:02x}{:02x}{:02x}".format(*fg[:3]) if isinstance(fg, (list, tuple)) else "#c8c8c8"
        border_hex = "#{:02x}{:02x}{:02x}".format(*border[:3]) if isinstance(border, (list, tuple)) else "#464646"

        style = """
            QScrollArea#breadcrumbBar {{
                background-color: {0};
                border: none;
            }}
            QWidget#breadcrumbContainer {{
                background-color: {0};
                border: none;
            }}
            QToolButton#breadcrumbItem {{
                color: {2};
                background: transparent;
                border: none;
                padding: 1px 3px;
                border-radius: 3px;
            }}
            QToolButton#breadcrumbItem:hover {{
                background-color: rgba(255, 255, 255, 0.12);
            }}
            QToolButton#breadcrumbItem::menu-button {{
                border: none;
                background: transparent;
                padding-left: 1px;
                padding-right: 1px;
            }}
            QToolButton#breadcrumbItem::menu-button:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
            }}
            QLabel {{
                color: {1};
                font-weight: bold;
            }}
        """.format(bg_hex, border_hex, fg_hex)
        self.setStyleSheet(style)
        self.rebuild_breadcrumbs()

    def set_symbols(self, symbols, file_path=None, fallback_name="Untitled", ext=".py"):
        self._raw_symbols = symbols or []
        self._file_path = file_path
        self._fallback_name = fallback_name or "Untitled"
        self._ext = ext
        self.rebuild_breadcrumbs()

    def set_cursor_line(self, line_num):
        if self._current_line != line_num:
            self._current_line = line_num
            self.rebuild_breadcrumbs()

    def _find_active_chain(self, symbols, line_num):
        chain = []
        current_symbols = symbols

        while current_symbols:
            candidates = [s for s in current_symbols if s.get('line', 1) <= line_num]
            if not candidates:
                break

            candidates.sort(key=lambda x: x.get('line', 1))
            matched = None
            matched_siblings = current_symbols

            for sym in candidates:
                sym_index = current_symbols.index(sym)
                next_sym_line = None
                if sym_index + 1 < len(current_symbols):
                    next_sym_line = current_symbols[sym_index + 1].get('line', 1)

                if next_sym_line is None or line_num < next_sym_line:
                    matched = sym
                    break

            if matched:
                chain.append((matched, matched_siblings))
                current_symbols = matched.get('children', [])
            else:
                break

        return chain

    def rebuild_breadcrumbs(self):
        # Clear layout items safely
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        first = True

        # Build full directory path and file nodes
        if self._file_path and os.path.isabs(self._file_path):
            components = split_path_into_components(self._file_path)
            for title, abs_path, is_dir in components:
                if not first:
                    sep = QLabel(">", self)
                    sep.setStatusTip("Breadcrumb separator")
                    if self._font:
                        sep.setFont(self._font)
                    self.layout.addWidget(sep)
                first = False

                node_type = "dir" if is_dir else "file"
                item_btn = BreadcrumbItemWidget(
                    title=title,
                    node_type=node_type,
                    path_or_data=abs_path,
                    siblings=None,
                    theme_colors=self._theme_colors,
                    font=self._font,
                    parent=self
                )
                item_btn.fileSelected.connect(self.fileSelected.emit)
                self.layout.addWidget(item_btn)
        else:
            # Unsaved / New Tab fallback
            item_btn = BreadcrumbItemWidget(
                title=self._fallback_name,
                node_type="file",
                path_or_data=None,
                siblings=None,
                theme_colors=self._theme_colors,
                font=self._font,
                parent=self
            )
            item_btn.fileSelected.connect(self.fileSelected.emit)
            self.layout.addWidget(item_btn)
            first = False

        # Build active symbol chain
        chain = self._find_active_chain(self._raw_symbols, self._current_line)

        for sym_data, siblings in chain:
            sep = QLabel(">", self)
            sep.setStatusTip("Breadcrumb separator")
            if self._font:
                sep.setFont(self._font)
            self.layout.addWidget(sep)

            raw_title = sym_data.get('name', '')
            sym_type = sym_data.get('type', 'function')
            clean_title = clean_symbol_name(raw_title, sym_type)

            item_btn = BreadcrumbItemWidget(
                title=clean_title,
                node_type="symbol",
                path_or_data=sym_data,
                siblings=siblings,
                theme_colors=self._theme_colors,
                font=self._font,
                parent=self
            )
            item_btn.symbolSelected.connect(self.symbolSelected.emit)
            self.layout.addWidget(item_btn)

        self.layout.addStretch(1)
