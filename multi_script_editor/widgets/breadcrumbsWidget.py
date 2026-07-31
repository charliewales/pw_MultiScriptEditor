import os
from bisect import bisect_right

from vendor.Qt.QtCore import QDir, QFileInfo, QPoint, QRect, QSize, Qt, Signal
from vendor.Qt.QtGui import QBrush, QColor, QIcon, QPalette
from vendor.Qt.QtWidgets import (
    QApplication,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionToolButton,
    QStylePainter,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets.explorerWidget import (
    DIRECTORY_COLOR,
    FILE_TYPE_COLORS,
    file_extension_sort_key,
    get_supported_extensions,
    is_supported_files_filter_enabled,
)
from widgets.outline_utils import (
    get_symbol_text_color,
    get_symbol_type_icon,
)


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


def clean_symbol_name(name):
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
            is_dir = curr != norm
            parts.insert(0, (name, curr, is_dir))
            curr = parent
        else:
            if curr:
                title = curr.rstrip('\\').rstrip('/') or curr
                parts.insert(0, (title, curr, True))
            break

    return parts


def list_directory_entries(dir_path, supported_extensions=None):
    try:
        entries = os.listdir(dir_path)
    except OSError:
        return [], []

    dirs = []
    files = []
    for entry in entries:
        if entry.startswith('.'):
            continue
        p = os.path.join(dir_path, entry)
        if os.path.isdir(p):
            dirs.append((entry, p))
        else:
            if supported_extensions is not None:
                extension = os.path.splitext(entry)[1].lower()
                if extension not in supported_extensions:
                    continue
            files.append((entry, p))

    dirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: file_extension_sort_key(x[0]))
    return dirs, files

def _color_css(value, fallback):
    if isinstance(value, QColor):
        return value.name()
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return "#{:02x}{:02x}{:02x}".format(*value[:3])
    if isinstance(value, str):
        color = QColor(value)
        if color.isValid():
            return color.name()
    return fallback


class BreadcrumbTreePopup(QFrame):
    fileSelected = Signal(str)
    symbolSelected = Signal(int)

    _KIND_ROLE = Qt.UserRole
    _VALUE_ROLE = Qt.UserRole + 1
    _LOADED_ROLE = Qt.UserRole + 2
    _DIRECTORY = "directory"
    _FILE = "file"
    _SYMBOL = "symbol"

    def __init__(self, theme_colors=None, font=None, parent=None):
        super(BreadcrumbTreePopup, self).__init__(
            parent,
            Qt.Popup | Qt.FramelessWindowHint,
        )
        self.setObjectName("breadcrumbPopup")
        self._theme_colors = theme_colors or {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        self.tree = QTreeWidget(self)
        self.tree.setObjectName("breadcrumbTree")
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setIndentation(18)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setAnimated(False)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        if font:
            self.setFont(font)
            self.tree.setFont(font)

        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemPressed.connect(self._on_item_pressed)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.tree)
        self._apply_theme()
        self._pressed_item = None
        self._pressed_item_was_expanded = False

    def populate(self, node_type, path_or_data=None, siblings=None):
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        self.tree.setRootIsDecorated(node_type != "symbol")
        self._supported_extensions = None
        if (
            node_type in ("dir", "file")
            and is_supported_files_filter_enabled()
        ):
            self._supported_extensions = get_supported_extensions()

        if node_type == "symbol":
            self._populate_symbols(siblings or [])
        elif node_type == "file":
            file_path = path_or_data or ""
            self._populate_directory(os.path.dirname(file_path))
        elif node_type == "dir":
            normalized_path = (
                os.path.normpath(path_or_data)
                if path_or_data
                else ""
            )
            if (
                os.name == "nt"
                and normalized_path
                and QFileInfo(normalized_path).isRoot()
            ):
                self._populate_drives()
            else:
                self._populate_directory(
                    os.path.dirname(normalized_path)
                    if normalized_path
                    else ""
                )

        self.tree.setUpdatesEnabled(True)

    def show_for(self, button, node_type, path_or_data=None, siblings=None):
        self.populate(node_type, path_or_data, siblings)

        screen = button.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry()
        row_height = self.tree.sizeHintForRow(0)
        if row_height <= 0:
            row_height = max(24, self.tree.fontMetrics().height() + 8)
        content_rows = max(1, self.tree.topLevelItemCount())
        maximum_height = min(600, max(240, int(available.height() * 0.7)))
        height = min(
            maximum_height,
            content_rows * row_height + self.frameWidth() * 2 + 6,
        )
        width = min(
            max(220, self.tree.sizeHintForColumn(0) + 42),
            max(220, int(available.width() * 0.7)),
        )
        self.resize(width, height)

        position = button.mapToGlobal(QPoint(0, button.height()))
        if position.y() + height > available.bottom() + 1:
            position.setY(
                button.mapToGlobal(QPoint(0, 0)).y() - height
            )
        position.setX(
            min(
                max(position.x(), available.left()),
                available.right() - width + 1,
            )
        )
        position.setY(
            min(
                max(position.y(), available.top()),
                available.bottom() - height + 1,
            )
        )

        self.move(position)
        self.show()
        self.raise_()
        self.tree.setFocus(Qt.PopupFocusReason)

    def _populate_directory(self, dir_path, parent_item=None):
        if not dir_path or not os.path.isdir(dir_path):
            return

        dirs, files = list_directory_entries(
            dir_path,
            self._supported_extensions,
        )
        for name, path in dirs:
            item = self._create_item(
                name,
                self._DIRECTORY,
                path,
                get_folder_icon(path),
            )
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            item.setData(0, self._LOADED_ROLE, False)
            self._add_item(item, parent_item)

        for name, path in files:
            self._add_item(
                self._create_item(
                    name,
                    self._FILE,
                    path,
                    get_file_icon(path),
                ),
                parent_item,
            )

    def _populate_drives(self):
        for drive_info in QDir.drives():
            drive_path = os.path.normpath(drive_info.absoluteFilePath())
            drive_name = os.path.splitdrive(drive_path)[0] or drive_path
            item = self._create_item(
                drive_name,
                self._DIRECTORY,
                drive_path,
                get_folder_icon(drive_path),
            )
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            item.setData(0, self._LOADED_ROLE, False)
            self.tree.addTopLevelItem(item)

    def _populate_symbols(self, siblings):
        for symbol in siblings:
            name = clean_symbol_name(symbol.get('name', ''))
            symbol_type = symbol.get('type', 'function')
            item = self._create_item(
                name,
                self._SYMBOL,
                symbol.get('line', 1),
                get_symbol_type_icon(
                    symbol_type,
                    self._theme_colors,
                ),
            )
            item.setForeground(
                0,
                QBrush(
                    get_symbol_text_color(
                        symbol_type,
                        self._theme_colors,
                    )
                ),
            )
            item.setToolTip(
                0,
                "Navigate to {0} (Line {1})".format(
                    name,
                    symbol.get('line', 1),
                ),
            )
            self.tree.addTopLevelItem(item)

    def _create_item(self, text, kind, value, icon):
        item = QTreeWidgetItem([text])
        item.setIcon(0, icon)
        item.setData(0, self._KIND_ROLE, kind)
        item.setData(0, self._VALUE_ROLE, value)
        if kind == self._DIRECTORY:
            item.setForeground(0, QBrush(QColor(DIRECTORY_COLOR)))
        elif kind == self._FILE:
            extension = os.path.splitext(value)[1].lower()
            file_color = FILE_TYPE_COLORS.get(extension)
            if file_color:
                item.setForeground(0, QBrush(QColor(file_color)))
        return item

    def _add_item(self, item, parent_item):
        if parent_item is None:
            self.tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

    def _on_item_expanded(self, item):
        if item.data(0, self._KIND_ROLE) != self._DIRECTORY:
            return
        if item.data(0, self._LOADED_ROLE):
            return
        item.setData(0, self._LOADED_ROLE, True)
        self._populate_directory(
            item.data(0, self._VALUE_ROLE),
            parent_item=item,
        )
        if item.childCount() == 0:
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.DontShowIndicator
            )

    def _on_item_pressed(self, item, column):
        self._pressed_item = item
        self._pressed_item_was_expanded = item.isExpanded()

    def _on_item_clicked(self, item, column):
        if item.data(0, self._KIND_ROLE) == self._DIRECTORY:
            expansion_changed = (
                self._pressed_item is item
                and item.isExpanded()
                != self._pressed_item_was_expanded
            )
            if not expansion_changed and not item.isExpanded():
                item.setExpanded(True)
            return
        self._activate_leaf(item)

    def _on_item_activated(self, item, column):
        kind = item.data(0, self._KIND_ROLE)
        if kind == self._DIRECTORY:
            item.setExpanded(True)
        else:
            self._activate_leaf(item)

    def _activate_leaf(self, item):
        kind = item.data(0, self._KIND_ROLE)
        if kind == self._FILE:
            self.fileSelected.emit(item.data(0, self._VALUE_ROLE))
            self.close()
        elif kind == self._SYMBOL:
            self.symbolSelected.emit(int(item.data(0, self._VALUE_ROLE)))
            self.close()

    def _apply_theme(self):
        background = _color_css(
            self._theme_colors.get(
                'background',
                self._theme_colors.get('window'),
            ),
            "#232323",
        )
        foreground = _color_css(
            self._theme_colors.get(
                'tab_selected_text',
                self._theme_colors.get('text'),
            ),
            "#dcdcdc",
        )
        highlight = _color_css(
            self._theme_colors.get('highlight_line'),
            "#464646",
        )
        border = _color_css(
            self._theme_colors.get(
                'border',
                self._theme_colors.get('tab_border'),
            ),
            "#555555",
        )
        self.setStyleSheet(
            """
            QFrame#breadcrumbPopup {{
                background-color: {0};
                border: 1px solid {3};
            }}
            QTreeWidget#breadcrumbTree {{
                background-color: {0};
                color: {1};
                border: none;
                outline: none;
                padding: 2px;
            }}
            QTreeWidget#breadcrumbTree::item {{
                min-height: 24px;
                padding: 1px 4px;
                border: 1px solid transparent;
            }}
            QTreeWidget#breadcrumbTree::item:hover,
            QTreeWidget#breadcrumbTree::item:selected {{
                background-color: {2};
                border: 1px solid {3};
                color: {1};
            }}
            """.format(
                background,
                foreground,
                highlight,
                border,
            )
        )


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
        self._menu_font = font
        self._popup = None

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.setAutoRaise(True)
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if font:
            self.setFont(font)

        self.setText(title)
        self.clicked.connect(self._show_popup)

        if self._node_type == "dir":
            self.setStatusTip("Browse folder {0}".format(title))

        elif self._node_type == "file":
            self.setStatusTip("File {0}".format(title))

        else:
            # Code Symbol Node
            sym_data = path_or_data or {}
            line = sym_data.get('line', 1)
            sym_type = sym_data.get('type', 'function')

            self.setStatusTip("Jump to {0} (Line {1})".format(title, line))
            self.setIcon(get_symbol_type_icon(sym_type, self._theme_colors))
            self.setIconSize(QSize(18, 18))

    def paintEvent(self, event):
        if self._node_type != "symbol" or self.icon().isNull():
            super(BreadcrumbItemWidget, self).paintEvent(event)
            return

        painter = QStylePainter(self)
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        icon = QIcon(option.icon)
        icon_size = option.iconSize
        text = option.text

        option.icon = QIcon()
        option.text = ""
        painter.drawComplexControl(QStyle.CC_ToolButton, option)

        metrics = option.fontMetrics
        if hasattr(metrics, "horizontalAdvance"):
            text_width = metrics.horizontalAdvance(text)
        else:
            text_width = metrics.width(text)
        spacing = 4
        content_width = icon_size.width() + spacing + text_width
        start_x = max(0, (self.width() - content_width) // 2)
        icon_rect = QRect(
            start_x,
            (self.height() - icon_size.height()) // 2,
            icon_size.width(),
            icon_size.height(),
        )

        if option.state & QStyle.State_Enabled:
            icon_mode = (
                QIcon.Active
                if option.state & QStyle.State_MouseOver
                else QIcon.Normal
            )
        else:
            icon_mode = QIcon.Disabled
        icon_state = (
            QIcon.On if option.state & QStyle.State_On else QIcon.Off
        )
        icon.paint(
            painter,
            icon_rect,
            Qt.AlignCenter,
            icon_mode,
            icon_state,
        )

        text_rect = QRect(
            start_x + icon_size.width() + spacing,
            0,
            text_width,
            self.height(),
        )
        palette = QPalette(option.palette)
        sym_data = self._path_or_data or {}
        palette.setColor(
            QPalette.ButtonText,
            get_symbol_text_color(
                sym_data.get('type', 'function'),
                self._theme_colors,
            ),
        )
        self.style().drawItemText(
            painter,
            text_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            palette,
            bool(option.state & QStyle.State_Enabled),
            text,
            QPalette.ButtonText,
        )

    def _setup_lazy_popup(self):
        if self._popup is not None:
            return self._popup

        self._popup = BreadcrumbTreePopup(
            theme_colors=self._theme_colors,
            font=self._menu_font,
            parent=self,
        )
        self._popup.fileSelected.connect(self.fileSelected.emit)
        self._popup.symbolSelected.connect(self.symbolSelected.emit)
        return self._popup

    def _show_popup(self):
        popup = self._setup_lazy_popup()
        popup.show_for(
            self,
            self._node_type,
            self._path_or_data,
            self._siblings,
        )


class BreadcrumbBar(QScrollArea):
    """
    VSCode-style Breadcrumbs Bar displaying the full directory path, file node, and code symbol scope hierarchy.
    """
    symbolSelected = Signal(int)
    fileSelected = Signal(str)

    def __init__(
        self,
        parent=None,
        file_path=None,
        fallback_name="",
        theme_colors=None,
        font=None,
    ):
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
        self._container.setFixedHeight(26)

        self.layout = QHBoxLayout(self._container)
        self.layout.setContentsMargins(4, 0, 4, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setWidget(self._container)

        self._raw_symbols = []
        self._file_path = file_path
        self._fallback_name = fallback_name or "Untitled"
        self._ext = ".py"
        self._current_line = 1
        self._theme_colors = theme_colors or {}
        self._font = font
        self._active_chain_key = ()
        self._symbol_line_indexes = {}

        if font:
            self.setFont(font)
            self._container.setFont(font)
        if theme_colors:
            self.apply_theme(theme_colors, font, rebuild=False)
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

    def apply_theme(self, theme_colors, font=None, rebuild=True):
        if theme_colors:
            self._theme_colors = theme_colors
        if font:
            self._font = font
            self.setFont(font)
            self._container.setFont(font)

        bg = self._theme_colors.get('window', self._theme_colors.get('tab_bg', (50, 50, 50)))
        fg = self._theme_colors.get('tab_selected_text', self._theme_colors.get('text', (220, 220, 220)))
        highlight = self._theme_colors.get('highlight_line', (70, 70, 70))

        bg_hex = "#{:02x}{:02x}{:02x}".format(*bg[:3]) if isinstance(bg, (list, tuple)) else "#323232"
        fg_hex = "#{:02x}{:02x}{:02x}".format(*fg[:3]) if isinstance(fg, (list, tuple)) else "#c8c8c8"
        highlight_hex = "#{:02x}{:02x}{:02x}".format(*highlight[:3]) if isinstance(highlight, (list, tuple)) else "#464646"

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
                color: {1};
                background: transparent;
                border: none;
                padding: 1px 0px;
                border-radius: 3px;
            }}
            QToolButton#breadcrumbItem:hover {{
                background-color: rgba(255, 255, 255, 0.12);
            }}
            QToolButton#breadcrumbItem::menu-indicator {{
                image: none;
                width: 0px;
                height: 0px;
            }}
            QToolButton#breadcrumbItem::menu-button {{
                image: none;
                border: none;
                width: 0px;
                padding: 0px;
                margin: 0px;
            }}
            QLabel {{
                color: {2};
                font-weight: bold;
            }}
        """.format(bg_hex, fg_hex, highlight_hex)
        self.setStyleSheet(style)
        if rebuild:
            self.rebuild_breadcrumbs()

    def set_symbols(self, symbols, file_path=None, fallback_name="Untitled", ext=".py"):
        self._raw_symbols = symbols or []
        self._rebuild_symbol_line_indexes()
        self._file_path = file_path
        self._fallback_name = fallback_name or "Untitled"
        self._ext = ext
        self.rebuild_breadcrumbs()

    def set_cursor_line(self, line_num):
        if self._current_line != line_num:
            self._current_line = line_num
            chain = self._find_active_chain(
                self._raw_symbols,
                self._current_line,
            )
            if self._chain_key(chain) != self._active_chain_key:
                self.rebuild_breadcrumbs()

    def set_outline_context(
        self,
        symbols,
        file_path=None,
        fallback_name="Untitled",
        ext=".py",
        theme_colors=None,
        font=None,
        line_num=1,
    ):
        symbols = symbols or []
        fallback_name = fallback_name or "Untitled"
        effective_theme = theme_colors or self._theme_colors
        effective_font = font or self._font
        if (
            symbols == self._raw_symbols
            and file_path == self._file_path
            and fallback_name == self._fallback_name
            and ext == self._ext
            and effective_theme == self._theme_colors
            and effective_font == self._font
            and line_num == self._current_line
        ):
            return

        if (
            effective_theme != self._theme_colors
            or effective_font != self._font
        ):
            self.apply_theme(theme_colors, font, rebuild=False)

        self._raw_symbols = symbols
        self._rebuild_symbol_line_indexes()
        self._file_path = file_path
        self._fallback_name = fallback_name
        self._ext = ext
        self._current_line = line_num
        self.rebuild_breadcrumbs()

    def _rebuild_symbol_line_indexes(self):
        self._symbol_line_indexes = {}
        self._index_symbol_lines(self._raw_symbols)

    def _index_symbol_lines(self, symbols):
        if not symbols:
            return

        entries = []
        for position, symbol in enumerate(symbols):
            entries.append(
                (
                    symbol.get('line', 1),
                    position,
                    symbol,
                )
            )
            self._index_symbol_lines(symbol.get('children', []))

        entries.sort(key=lambda item: (item[0], item[1]))
        self._symbol_line_indexes[id(symbols)] = (
            symbols,
            tuple(item[0] for item in entries),
            tuple(item[2] for item in entries),
        )

    def _indexed_symbols(self, symbols):
        indexed = self._symbol_line_indexes.get(id(symbols))
        if indexed is None or indexed[0] is not symbols:
            self._index_symbol_lines(symbols)
            indexed = self._symbol_line_indexes[id(symbols)]
        return indexed[1], indexed[2]

    def _find_active_chain(self, symbols, line_num):
        chain = []
        current_symbols = symbols

        while current_symbols:
            lines, ordered_symbols = self._indexed_symbols(
                current_symbols
            )
            match_index = bisect_right(lines, line_num) - 1
            if match_index < 0:
                break
            matched = ordered_symbols[match_index]
            chain.append((matched, current_symbols))
            current_symbols = matched.get('children', [])

        return chain

    @staticmethod
    def _chain_key(chain):
        return tuple(
            (
                symbol.get('type'),
                symbol.get('name'),
                symbol.get('line'),
            )
            for symbol, _siblings in chain
        )

    def rebuild_breadcrumbs(self):
        # Clear layout items safely
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
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

        # Build active symbol chain
        chain = self._find_active_chain(self._raw_symbols, self._current_line)
        self._active_chain_key = self._chain_key(chain)

        for sym_data, siblings in chain:
            if not first:
                sep = QLabel(">", self)
                sep.setStatusTip("Breadcrumb separator")
                if self._font:
                    sep.setFont(self._font)
                self.layout.addWidget(sep)
            first = False

            raw_title = sym_data.get('name', '')
            clean_title = clean_symbol_name(raw_title)

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

        if first:
            placeholder = QLabel(">", self)
            placeholder.setStatusTip("Empty breadcrumb")
            if self._font:
                placeholder.setFont(self._font)
            self.layout.addWidget(placeholder)

        self.layout.addStretch(1)
