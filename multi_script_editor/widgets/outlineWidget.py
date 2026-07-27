from icons import icons
from vendor.Qt.QtCore import QSize, Qt, Signal
from vendor.Qt.QtGui import QIcon, QKeySequence
from vendor.Qt.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QShortcut,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets.outline_utils import HtmlDelegate, create_tree_symbol_item


class OutlineWidget(QWidget):
    """
    Enhanced Outline Panel featuring a hierarchical tree view of document symbols
    (classes, methods, functions, global variables, and constants).
    """

    symbolSelected = Signal(int)
    options_changed = Signal()

    def __init__(self, parent=None):
        super(OutlineWidget, self).__init__(parent)
        self.setObjectName("outlineWidget")

        self._raw_symbols = []
        self._theme_colors = None
        self._font = None
        self._ext = '.py'
        self._follow_cursor = False
        self._sort_alphabetical = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header bar with search input and toolbar buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 2, 0, 0)
        header_layout.setSpacing(2)

        self.filter_le = QLineEdit()
        self.filter_le.setObjectName("outlineFilter")
        self.filter_le.setPlaceholderText("Filter outline...")
        self.filter_le.setClearButtonEnabled(True)
        self.filter_le.setStatusTip("Filter symbols in the outline tree")
        self.filter_le.textChanged.connect(self._on_filter_changed)

        esc_shortcut = QShortcut(QKeySequence("Esc"), self.filter_le)
        esc_shortcut.setContext(Qt.WidgetShortcut)
        esc_shortcut.activated.connect(self.filter_le.clear)

        # Toolbar Buttons
        self.collapse_btn = QToolButton()
        self.collapse_btn.setIcon(QIcon(icons.get("fold_all", icons.get("fold", ""))))
        self.collapse_btn.setToolTip("Collapse All")
        self.collapse_btn.setStatusTip("Collapse all items in the symbol outline tree")
        self.collapse_btn.setIconSize(QSize(24, 24))
        self.collapse_btn.clicked.connect(self.collapse_all)

        self.expand_btn = QToolButton()
        self.expand_btn.setIcon(QIcon(icons.get("unfold_all", icons.get("unfold", ""))))
        self.expand_btn.setToolTip("Expand All")
        self.expand_btn.setStatusTip("Expand all items in the symbol outline tree")
        self.expand_btn.setIconSize(QSize(24, 24))
        self.expand_btn.clicked.connect(self.expand_all)

        self.sort_btn = QToolButton()
        self.sort_btn.setIcon(QIcon(icons.get("goto_symbol", "")))
        self.sort_btn.setCheckable(True)
        self.sort_btn.setToolTip("Sort Alphabetically")
        self.sort_btn.setStatusTip("Toggle sorting symbols alphabetically or by line number")
        self.sort_btn.setIconSize(QSize(24, 24))
        self.sort_btn.toggled.connect(self._on_sort_toggled)

        self.sync_btn = QToolButton()
        self.sync_btn.setIcon(QIcon(icons.get("bookmark_toggle", icons.get("goto_line", ""))))
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(False)
        self.sync_btn.setToolTip("Follow Cursor")
        self.sync_btn.setStatusTip("Toggle auto-highlighting active symbol based on editor line")
        self.sync_btn.setIconSize(QSize(24, 24))
        self.sync_btn.toggled.connect(self._on_sync_toggled)

        header_layout.addWidget(self.filter_le, 1)
        header_layout.addWidget(self.collapse_btn)
        header_layout.addWidget(self.expand_btn)
        header_layout.addWidget(self.sort_btn)
        header_layout.addWidget(self.sync_btn)

        # Symbol Tree Widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setObjectName("outlineTree")
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIconSize(QSize(18, 18))
        self.tree_widget.setIndentation(14)
        self.tree_widget.setFocusPolicy(Qt.NoFocus)
        self.tree_widget.setItemDelegate(HtmlDelegate(self.tree_widget))
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.itemActivated.connect(self._on_item_clicked)

        layout.addLayout(header_layout)
        layout.addWidget(self.tree_widget)

    def set_font(self, font):
        self._font = font
        if font:
            self.setFont(font)
            self.tree_widget.setFont(font)
            self.filter_le.setFont(font)

    def set_symbols(self, symbols, theme_colors=None, font=None, ext='.py'):
        """
        Populates the tree with hierarchical code symbols.
        """
        self._raw_symbols = symbols or []
        self._theme_colors = theme_colors
        if font:
            self._font = font
            self.setFont(font)
            self.tree_widget.setFont(font)
            self.filter_le.setFont(font)
        self._ext = ext

        self.rebuild_tree()

    def rebuild_tree(self):
        """
        Rebuilds tree items from raw symbols according to current sort and filter settings.
        Preserves previously expanded node states across updates, defaulting to 1st level only.
        """
        expanded_keys = set()

        def _save_expanded(item):
            if item.isExpanded():
                sym_data = item.data(0, Qt.UserRole + 2)
                if sym_data:
                    key = (sym_data.get('type'), sym_data.get('name'), sym_data.get('line'))
                    expanded_keys.add(key)
            for i in range(item.childCount()):
                _save_expanded(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            _save_expanded(self.tree_widget.topLevelItem(i))

        self.tree_widget.clear()
        if not self._raw_symbols:
            return

        def _add_nodes(parent_item, sym_list):
            items_to_process = list(sym_list)
            if self._sort_alphabetical:
                items_to_process.sort(key=lambda x: x.get('raw_name', x.get('name', '')).lower())

            for sym in items_to_process:
                tree_item = create_tree_symbol_item(sym, self._theme_colors, self._font, ext=self._ext)
                if parent_item:
                    parent_item.addChild(tree_item)
                else:
                    self.tree_widget.addTopLevelItem(tree_item)

                children = sym.get('children', [])
                if children:
                    _add_nodes(tree_item, children)

        self.tree_widget.setUpdatesEnabled(False)
        _add_nodes(None, self._raw_symbols)

        if expanded_keys:
            def _restore_expanded(item):
                sym_data = item.data(0, Qt.UserRole + 2)
                if sym_data:
                    key = (sym_data.get('type'), sym_data.get('name'), sym_data.get('line'))
                    if key in expanded_keys:
                        item.setExpanded(True)
                for i in range(item.childCount()):
                    _restore_expanded(item.child(i))

            for i in range(self.tree_widget.topLevelItemCount()):
                _restore_expanded(self.tree_widget.topLevelItem(i))
        else:
            # By default expand top-level nodes only (1st level: classes, top-level functions)
            for i in range(self.tree_widget.topLevelItemCount()):
                top_item = self.tree_widget.topLevelItem(i)
                top_item.setExpanded(True)

        if self.filter_le.text():
            self._on_filter_changed(self.filter_le.text())

        self.tree_widget.setUpdatesEnabled(True)

    def collapse_all(self):
        self.tree_widget.collapseAll()

    def expand_all(self):
        self.tree_widget.expandAll()

    def _on_sort_toggled(self, checked):
        self._sort_alphabetical = checked
        self.rebuild_tree()
        self.options_changed.emit()

    def _on_sync_toggled(self, checked):
        self._follow_cursor = checked
        self.options_changed.emit()

    def is_follow_cursor_enabled(self):
        return self._follow_cursor

    def _on_filter_changed(self, text):
        """
        Filters tree nodes by matching query string and expanding matching branches.
        """
        query = text.lower().strip()

        def _filter_item(item):
            match = False
            raw_text = item.text(0).lower()
            sym_data = item.data(0, Qt.UserRole + 2)
            raw_name = sym_data.get('raw_name', '').lower() if sym_data else ''

            if not query or (query in raw_text or query in raw_name):
                match = True

            child_match = False
            for i in range(item.childCount()):
                if _filter_item(item.child(i)):
                    child_match = True

            should_show = match or child_match
            item.setHidden(not should_show)
            if query and child_match:
                item.setExpanded(True)

            return should_show

        self.tree_widget.setUpdatesEnabled(False)
        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)
            _filter_item(top_item)
        self.tree_widget.setUpdatesEnabled(True)

    def _on_item_clicked(self, item, column=0):
        line = item.data(0, Qt.UserRole)
        if line:
            self.symbolSelected.emit(line)

    def highlight_symbol_at_line(self, line_num):
        """
        Highlights the symbol in the tree corresponding to the active cursor line number.
        """
        if not self._follow_cursor or self.tree_widget.topLevelItemCount() == 0:
            return

        best_item = None
        best_line = -1

        def _find_best_match(parent_item=None):
            nonlocal best_item, best_line
            count = parent_item.childCount() if parent_item else self.tree_widget.topLevelItemCount()
            for i in range(count):
                item = parent_item.child(i) if parent_item else self.tree_widget.topLevelItem(i)
                item_line = item.data(0, Qt.UserRole)
                if item_line and item_line <= line_num and item_line > best_line:
                    best_line = item_line
                    best_item = item
                if item.childCount() > 0:
                    _find_best_match(item)

        _find_best_match(None)

        if best_item:
            self.tree_widget.blockSignals(True)
            parent = best_item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            self.tree_widget.setCurrentItem(best_item)
            self.tree_widget.scrollToItem(best_item)
            self.tree_widget.blockSignals(False)
