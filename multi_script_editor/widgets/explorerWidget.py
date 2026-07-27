import os
import shutil

from icons import icons
from vendor.Qt.QtCore import (
    QDir,
    QItemSelectionModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
    QTimer,
    QUrl,
    QSize,
)
from vendor.Qt.QtGui import QColor, QDesktopServices, QIcon
from vendor.Qt.QtWidgets import (
    QAction,
    QAbstractItemView,
    QApplication,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

FILE_TYPE_COLORS = {
    # Python
    ".py": "#61afef", ".pyw": "#61afef", ".pyx": "#61afef", ".pyc": "#5c6370",
    # Data / Config
    ".json": "#d19a66", ".yaml": "#d19a66", ".yml": "#d19a66",
    ".xml": "#d19a66", ".ini": "#d19a66", ".toml": "#d19a66", ".csv": "#d19a66",
    # Docs / Text
    ".md": "#98c379", ".txt": "#98c379", ".rst": "#98c379", ".log": "#abb2bf",
    # Web
    ".html": "#e06c75", ".htm": "#e06c75", ".css": "#56b6c2", ".js": "#e5c07b",
    # Shell / Scripts / Batch
    ".sh": "#98c379", ".bat": "#98c379", ".cmd": "#98c379", ".ps1": "#98c379",
    # USD
    ".usd": "#e5c07b", ".usda": "#e5c07b",
}

SUPPORTED_EXTENSIONS_EXTRA = set()


def register_supported_extension(ext):
    """
    Dynamically register an extra supported file extension for Explorer filtering.
    """
    if not ext:
        return
    if not ext.startswith("."):
        ext = "." + ext
    SUPPORTED_EXTENSIONS_EXTRA.add(ext.lower())


def get_supported_extensions():
    """
    Dynamically returns all supported file extensions in Multi Script Editor.
    Fetches SUPPORTED_EXTENSIONS from scriptEditor and combines with FILE_TYPE_COLORS.
    """
    exts = set(FILE_TYPE_COLORS.keys()) | SUPPORTED_EXTENSIONS_EXTRA
    try:
        import scriptEditor
        if hasattr(scriptEditor, 'SUPPORTED_EXTENSIONS'):
            exts.update(scriptEditor.SUPPORTED_EXTENSIONS)
    except Exception:
        pass
    return exts


def get_default_bookmarks():
    """
    Returns default favorite directories (User Home and Desktop if available).
    """
    defaults = []
    home = os.path.abspath(os.path.expanduser("~"))
    if os.path.exists(home):
        defaults.append(home)

    desktop = os.path.join(home, "Desktop")
    if os.path.exists(desktop):
        defaults.append(desktop)

    return defaults


class FileSystemFilterProxyModel(QSortFilterProxyModel):
    """
    Custom proxy model that recursively filters, sorts by extension ascending,
    colors file types, and supports filtering by supported file types dynamically.
    """
    def __init__(self, parent=None):
        super(FileSystemFilterProxyModel, self).__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._filter_text = ""
        self._filter_supported_only = True

    def setFilterFixedString(self, pattern):
        self._filter_text = pattern.strip().lower() if pattern else ""
        super(FileSystemFilterProxyModel, self).setFilterFixedString(pattern)

    def setFilterSupportedOnly(self, enabled):
        """
        If enabled (True / Checked button): Show ONLY supported file types.
        If disabled (False / Unchecked button): Show ALL files.
        """
        self._filter_supported_only = bool(enabled)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        file_name = source_model.fileName(index)

        if not source_model.isDir(index):
            # If _filter_supported_only is True (Checked button), filter to supported extensions only
            if self._filter_supported_only:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in get_supported_extensions():
                    return False

            # Check if name text filter matches
            if self._filter_text:
                if self._filter_text not in file_name.lower():
                    return False

            return True

        # If it's a directory, check if any child item matches recursively
        num_children = source_model.rowCount(index)
        if num_children == 0:
            return True

        for i in range(num_children):
            if self.filterAcceptsRow(i, index):
                return True

        return False

    def lessThan(self, left_index, right_index):
        source_model = self.sourceModel()
        if not source_model:
            return super(FileSystemFilterProxyModel, self).lessThan(left_index, right_index)

        left_is_dir = source_model.isDir(left_index)
        right_is_dir = source_model.isDir(right_index)

        # Always keep directories at top
        if left_is_dir and not right_is_dir:
            return True
        if not left_is_dir and right_is_dir:
            return False

        left_name = source_model.fileName(left_index)
        right_name = source_model.fileName(right_index)

        if left_is_dir and right_is_dir:
            return left_name.lower() < right_name.lower()

        # For files: sort by file extension ascending
        left_ext = os.path.splitext(left_name)[1].lower()
        right_ext = os.path.splitext(right_name)[1].lower()

        if left_ext == right_ext:
            return left_name.lower() < right_name.lower()

        return left_ext < right_ext

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole:
            source_index = self.mapToSource(index)
            source_model = self.sourceModel()
            if source_index.isValid() and source_model:
                if source_model.isDir(source_index):
                    # Directory color (Folder gold/yellow)
                    return QColor("#e5c07b")
                else:
                    file_name = source_model.fileName(source_index)
                    ext = os.path.splitext(file_name)[1].lower()
                    color_hex = FILE_TYPE_COLORS.get(ext)
                    if color_hex:
                        return QColor(color_hex)
        return super(FileSystemFilterProxyModel, self).data(index, role)


class ExplorerTreeView(QTreeView):
    """
    Subclassed QTreeView to catch Return/Enter, Middle Click, and Backspace keys for navigation.
    """
    file_open_requested = Signal(str)
    directory_set_root_requested = Signal(str)
    navigate_parent_requested = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            idx = self.indexAt(event.pos())
            if idx.isValid():
                model = self.model()
                source_index = model.mapToSource(idx) if hasattr(model, 'mapToSource') else idx
                fs_model = model.sourceModel() if hasattr(model, 'sourceModel') else model
                path = fs_model.filePath(source_index)
                if os.path.isdir(path):
                    self.directory_set_root_requested.emit(path)
                    event.accept()
                    return
                elif os.path.isfile(path):
                    self.file_open_requested.emit(path)
                    event.accept()
                    return
        super(ExplorerTreeView, self).mousePressEvent(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            selected_indexes = [idx for idx in self.selectedIndexes() if idx.column() == 0]
            if selected_indexes:
                model = self.model()
                source_model = model.sourceModel() if hasattr(model, 'sourceModel') else model
                for idx in selected_indexes:
                    source_index = model.mapToSource(idx) if hasattr(model, 'mapToSource') else idx
                    path = source_model.filePath(source_index)
                    if os.path.isfile(path):
                        self.file_open_requested.emit(path)
                    elif len(selected_indexes) == 1 and os.path.isdir(path):
                        self.directory_set_root_requested.emit(path)
                event.accept()
                return

        elif key == Qt.Key_Backspace:
            self.navigate_parent_requested.emit()
            event.accept()
            return

        super(ExplorerTreeView, self).keyPressEvent(event)


class ExplorerWidget(QWidget):
    """
    VSCode-style File Explorer Widget with path navigation, filtering, extension sorting,
    file type coloring, and directory bookmarks popup menu.
    """
    file_selected = Signal(str)
    folder_changed = Signal(str)
    bookmarks_changed = Signal(list)
    sync_to_current_tab_requested = Signal()
    options_changed = Signal()

    def __init__(self, parent=None, root_path=None):
        super(ExplorerWidget, self).__init__(parent)
        self.setObjectName("explorerWidget")

        self.bookmarks = get_default_bookmarks()
        self._current_root = root_path or os.getcwd()

        self._is_initialized = False
        self._setup_ui()
        self._setup_connections()
        self.path_filter_input.setText(self._current_root)

    def showEvent(self, event):
        super(ExplorerWidget, self).showEvent(event)
        if not self._is_initialized:
            self.set_root_path(self._current_root)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Top Bar Layout
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 2, 0, 0)
        self.top_layout.setSpacing(2)

        # Top Bar: QLineEdit for filter & direct path navigation
        self.path_filter_input = QLineEdit()
        self.path_filter_input.setObjectName("explorerPathFilterInput")
        self.path_filter_input.setPlaceholderText("Enter path...")


        self.up_btn = QToolButton()
        self.up_btn.setToolTip("Up to parent directory")
        self.up_btn.setStatusTip("Navigate up to the parent directory")
        self.up_btn.setIcon(QIcon(icons.get("up", "")))

        self.sync_tab_btn = QToolButton()
        self.sync_tab_btn.setIconSize(QSize(24, 24))
        self.sync_tab_btn.setToolTip("Set root to current tab directory")
        self.sync_tab_btn.setStatusTip("Set the explorer root path to match the currently active tab")
        self.sync_tab_btn.setIcon(QIcon(icons.get("view_file", icons.get("open", ""))))

        self.auto_sync_tab_btn = QToolButton()
        self.auto_sync_tab_btn.setIconSize(QSize(24, 24))
        self.auto_sync_tab_btn.setCheckable(True)
        self.auto_sync_tab_btn.setChecked(False)
        self.auto_sync_tab_btn.setToolTip("Toggle: auto-sync explorer root on tab change")
        self.auto_sync_tab_btn.setStatusTip("Automatically set the explorer root path when switching tabs")
        self.auto_sync_tab_btn.setIcon(QIcon(icons.get("file_recent", icons.get("open", ""))))

        self.filter_supported_btn = QToolButton()
        self.filter_supported_btn.setIconSize(QSize(24, 24))
        self.filter_supported_btn.setCheckable(True)
        self.filter_supported_btn.setChecked(True)
        self.filter_supported_btn.setIcon(QIcon(icons.get("filter_files", "")))
        self.filter_supported_btn.setToolTip("Toggle: show all files (checked = supported files only, unchecked = all files)")
        self.filter_supported_btn.setStatusTip("Toggle whether to show all files or only supported scripts/files")

        self.add_bookmark_btn = QToolButton()
        self.add_bookmark_btn.setIconSize(QSize(24, 24))
        self.add_bookmark_btn.setToolTip("Bookmark current directory")
        self.add_bookmark_btn.setStatusTip("Add the current directory to your explorer bookmarks")
        self.add_bookmark_btn.setIcon(QIcon(icons.get("bookmark_toggle", "")))

        self.bookmarks_menu_btn = QToolButton()
        self.bookmarks_menu_btn.setIconSize(QSize(24, 24))
        self.bookmarks_menu_btn.setToolTip("Show saved directory favorites")
        self.bookmarks_menu_btn.setStatusTip("Show a menu of your bookmarked directories")
        self.bookmarks_menu_btn.setIcon(QIcon(icons.get("bookmark_prev", icons.get("bookmark_toggle", ""))))

        self.bookmarks_menu = QMenu(self)
        self.bookmarks_menu_btn.setMenu(self.bookmarks_menu)
        self.bookmarks_menu_btn.setPopupMode(QToolButton.InstantPopup)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setIconSize(QSize(24, 24))
        self.refresh_btn.setToolTip("Refresh directory")
        self.refresh_btn.setStatusTip("Refresh the file explorer view")
        self.refresh_btn.setIcon(QIcon(icons.get("reload_plugins", icons.get("clear", ""))))

        self.top_layout.addWidget(self.up_btn)
        self.top_layout.addWidget(self.sync_tab_btn)
        self.top_layout.addWidget(self.auto_sync_tab_btn)
        self.top_layout.addWidget(self.filter_supported_btn)
        self.top_layout.addWidget(self.add_bookmark_btn)
        self.top_layout.addWidget(self.bookmarks_menu_btn)
        # self.top_layout.addWidget(self.refresh_btn)

        # Path filter input layout with margins matching Outline filter
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 2, 0, 0)
        path_layout.setSpacing(0)
        path_layout.addWidget(self.path_filter_input)
        path_layout.addLayout(self.top_layout)

        main_layout.addLayout(path_layout)

        # Tree View & File System Model
        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden)

        self.proxy_model = FileSystemFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.fs_model)

        self.tree_view = ExplorerTreeView()
        self.tree_view.setObjectName("explorerTreeView")
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.setAnimated(True)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setDragDropMode(QAbstractItemView.DragOnly)
        self.tree_view.setToolTip(
            "- Return/Enter/Middle Click: set root folder\n- Backspace: go to parent folder"
        )
        self.proxy_model.sort(0, Qt.AscendingOrder)

        # Hide extra columns (size, type, date modified) to keep explorer compact
        for col in range(1, 4):
            self.tree_view.setColumnHidden(col, True)

        main_layout.addWidget(self.tree_view, 1)

        self._update_bookmarks_menu()

    def _setup_connections(self):
        self.path_filter_input.textChanged.connect(self.path_filter_input.setToolTip)
        self.path_filter_input.returnPressed.connect(self._on_path_entered)

        self.up_btn.clicked.connect(self.navigate_up)
        self.sync_tab_btn.clicked.connect(self.sync_to_current_tab_requested.emit)
        self.auto_sync_tab_btn.toggled.connect(self._on_auto_sync_toggled)
        self.auto_sync_tab_btn.toggled.connect(lambda state: self.options_changed.emit())
        self.filter_supported_btn.toggled.connect(self.proxy_model.setFilterSupportedOnly)
        self.filter_supported_btn.toggled.connect(lambda state: self.options_changed.emit())
        self.bookmarks_changed.connect(lambda b: self.options_changed.emit())
        self.add_bookmark_btn.clicked.connect(self.add_current_to_bookmarks)
        self.refresh_btn.clicked.connect(self.refresh_tree)

        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        self.tree_view.file_open_requested.connect(self.file_selected.emit)
        self.tree_view.directory_set_root_requested.connect(self.set_root_path)
        self.tree_view.navigate_parent_requested.connect(self.navigate_up)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.fs_model.directoryLoaded.connect(self._on_directory_loaded)

    def _on_auto_sync_toggled(self, checked):
        if checked:
            self.sync_to_current_tab_requested.emit()

    def set_root_path(self, path):
        if not path or not os.path.exists(path):
            path = os.path.expanduser("~")

        if os.path.isfile(path):
            path = os.path.dirname(path)

        path = os.path.abspath(path)
        self._current_root = path
        if getattr(self, '_is_initialized', False):
            self.options_changed.emit()
        self._is_initialized = True

        self.path_filter_input.setText(path)

        source_index = self.fs_model.setRootPath(path)
        proxy_index = self.proxy_model.mapFromSource(source_index)

        if proxy_index.isValid():
            self.tree_view.setRootIndex(proxy_index)

        self.folder_changed.emit(path)

    def _on_directory_loaded(self, path):
        if os.path.abspath(path) == os.path.abspath(self._current_root):
            source_index = self.fs_model.index(path)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            if proxy_index.isValid():
                self.tree_view.setRootIndex(proxy_index)
            if getattr(self, '_pending_select_file', None):
                self._select_and_highlight_file(self._pending_select_file)
                self._pending_select_file = None

    def get_current_root(self):
        return self._current_root

    def _on_filter_changed(self, text):
        self.proxy_model.setFilterFixedString(text)
        if text.strip():
            self.tree_view.expandAll()

    def _on_path_entered(self):
        text = self.path_filter_input.text().strip().strip('"\'')
        if not text:
            self.path_filter_input.setText(self._current_root)
            return

        norm_path = os.path.abspath(os.path.expanduser(text))

        if os.path.exists(norm_path):
            self.proxy_model.setFilterFixedString("")

            if os.path.isdir(norm_path):
                self.set_root_path(norm_path)
            elif os.path.isfile(norm_path):
                parent_dir = os.path.dirname(norm_path)
                self.set_root_path(parent_dir)
                self._select_and_highlight_file(norm_path)
                self.file_selected.emit(norm_path)
        else:
            # If not a disk path, revert to current root
            self.path_filter_input.setText(self._current_root)

    def select_file(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        filepath = os.path.abspath(filepath)
        dirpath = os.path.dirname(filepath) if os.path.isfile(filepath) else filepath
        self._pending_select_file = filepath if os.path.isfile(filepath) else None

        self.set_root_path(dirpath)
        self._select_and_highlight_file(filepath)
        QTimer.singleShot(50, lambda: self._select_and_highlight_file(filepath))
        QTimer.singleShot(200, lambda: self._select_and_highlight_file(filepath))

    def _select_and_highlight_file(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        source_index = self.fs_model.index(filepath)
        if source_index.isValid():
            proxy_index = self.proxy_model.mapFromSource(source_index)
            if proxy_index.isValid():
                self.tree_view.setCurrentIndex(proxy_index)
                if self.tree_view.selectionModel():
                    self.tree_view.selectionModel().select(
                        proxy_index,
                        QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
                    )
                self.tree_view.scrollTo(proxy_index)

    def navigate_up(self):
        parent_dir = os.path.dirname(self._current_root)
        if parent_dir and parent_dir != self._current_root and os.path.exists(parent_dir):
            self.set_root_path(parent_dir)

    def refresh_tree(self):
        current = self._current_root
        self.fs_model.setRootPath("")
        self.fs_model.setRootPath(current)
        self.set_root_path(current)

    def _on_item_double_clicked(self, proxy_index):
        source_index = self.proxy_model.mapToSource(proxy_index)
        filepath = self.fs_model.filePath(source_index)

        if os.path.isfile(filepath):
            self.file_selected.emit(filepath)

    def get_bookmarks(self):
        return list(self.bookmarks)

    def set_bookmarks(self, bookmarks_list):
        self.bookmarks = []
        if isinstance(bookmarks_list, (list, tuple)):
            for b in bookmarks_list:
                if isinstance(b, str) and b not in self.bookmarks and os.path.exists(b):
                    self.bookmarks.append(b)

        # Always ensure defaults exist
        for d in get_default_bookmarks():
            if d not in self.bookmarks and os.path.exists(d):
                self.bookmarks.append(d)

        self._update_bookmarks_menu()

    def add_current_to_bookmarks(self):
        current = self._current_root
        if current and current not in self.bookmarks:
            self.bookmarks.append(current)
            self._update_bookmarks_menu()
            self.bookmarks_changed.emit(list(self.bookmarks))

    def add_path_to_bookmarks(self, path):
        if path and os.path.isdir(path) and path not in self.bookmarks:
            self.bookmarks.append(path)
            self._update_bookmarks_menu()
            self.bookmarks_changed.emit(list(self.bookmarks))

    def remove_bookmark(self, path):
        if path in self.bookmarks:
            self.bookmarks.remove(path)
            self._update_bookmarks_menu()
            self.bookmarks_changed.emit(list(self.bookmarks))

    def _update_bookmarks_menu(self):
        self.bookmarks_menu.clear()

        # Ensure defaults are included
        for d in get_default_bookmarks():
            if d not in self.bookmarks and os.path.exists(d):
                self.bookmarks.append(d)

        # Sort bookmarks alphabetically by folder name, then full path
        sorted_bookmarks = sorted(self.bookmarks, key=lambda p: (os.path.basename(p).lower() or p.lower(), p.lower()))

        for path in sorted_bookmarks:
            folder_name = os.path.basename(path) or path
            act = QAction(f"{folder_name}  ({path})", self.bookmarks_menu)
            act.setIcon(QIcon(icons.get("open", "")))
            act.triggered.connect(lambda checked=False, p=path: self.set_root_path(p))
            self.bookmarks_menu.addAction(act)

        if sorted_bookmarks:
            self.bookmarks_menu.addSeparator()

        add_act = QAction("Bookmark current directory", self.bookmarks_menu)
        add_act.setIcon(QIcon(icons.get("bookmark_toggle", "")))
        add_act.triggered.connect(self.add_current_to_bookmarks)
        self.bookmarks_menu.addAction(add_act)

        if sorted_bookmarks:
            remove_menu = QMenu("Remove favorite...", self.bookmarks_menu)
            remove_menu.setIcon(QIcon(icons.get("clear", "")))
            for path in sorted_bookmarks:
                r_act = QAction(f"{os.path.basename(path) or path}", remove_menu)
                r_act.triggered.connect(lambda checked=False, p=path: self.remove_bookmark(p))
                remove_menu.addAction(r_act)
            self.bookmarks_menu.addMenu(remove_menu)

    def _show_context_menu(self, position):
        selected_indexes = [idx for idx in self.tree_view.selectedIndexes() if idx.column() == 0]
        click_proxy_index = self.tree_view.indexAt(position)

        if click_proxy_index.isValid() and click_proxy_index not in selected_indexes:
            selected_indexes = [click_proxy_index]

        selected_paths = []
        for idx in selected_indexes:
            src_idx = self.proxy_model.mapToSource(idx)
            p = self.fs_model.filePath(src_idx)
            if p:
                selected_paths.append(p)

        if not selected_paths:
            selected_paths = [self._current_root]

        menu = QMenu(self)
        menu.setFont(self.font())

        def on_hover(action):
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                if action and action.statusTip():
                    if getattr(main_window, '_show_status_tips', True):
                        main_window.statusBar().showMessage(action.statusTip())
                else:
                    main_window.statusBar().clearMessage()

        menu.hovered.connect(on_hover)

        if len(selected_paths) > 1:
            files_to_open = [p for p in selected_paths if os.path.isfile(p)]
            if files_to_open:
                open_all_act = QAction(f"Open selected files ({len(files_to_open)})", menu)
                open_all_act.setStatusTip("Open all selected files in tabs")
                open_all_act.setIcon(QIcon(icons.get("open", "")))
                open_all_act.triggered.connect(lambda: [self.file_selected.emit(p) for p in files_to_open])
                menu.addAction(open_all_act)

            copy_all_paths_act = QAction("Copy selected full paths", menu)
            copy_all_paths_act.setStatusTip("Copy all selected paths to clipboard")
            copy_all_paths_act.setIcon(QIcon(icons.get("copy", "")))
            copy_all_paths_act.triggered.connect(lambda: QApplication.clipboard().setText("\n".join(selected_paths)))
            menu.addAction(copy_all_paths_act)

            menu.addSeparator()

            delete_all_act = QAction(f"Delete selected ({len(selected_paths)})", menu)
            delete_all_act.setStatusTip("Delete selected files and folders")
            delete_all_act.setIcon(QIcon(icons.get("delete_file", "")))
            delete_all_act.triggered.connect(lambda: [self._delete_path(p) for p in selected_paths])
            menu.addAction(delete_all_act)
        else:
            target_path = selected_paths[0]
            source_index = self.proxy_model.mapToSource(self.tree_view.indexAt(position)) if click_proxy_index.isValid() else QModelIndex()

            if os.path.isfile(target_path):
                open_act = QAction("Open in editor [MMB]", menu)
                open_act.setStatusTip("Open this file in a new tab (Middle Mouse Button)")
                open_act.setIcon(QIcon(icons.get("open", "")))
                open_act.triggered.connect(lambda: self.file_selected.emit(target_path))
                menu.addAction(open_act)
            elif os.path.isdir(target_path):
                set_root_act = QAction("Set as explorer root [MMB]", menu)
                set_root_act.setStatusTip("Navigate into this folder (Middle Mouse Button)")
                set_root_act.setIcon(QIcon(icons.get("open", "")))
                set_root_act.triggered.connect(lambda: self.set_root_path(target_path))
                menu.addAction(set_root_act)

                bookmark_act = QAction("Add to favorites/bookmarks", menu)
                bookmark_act.setStatusTip("Bookmark this folder")
                bookmark_act.setIcon(QIcon(icons.get("bookmark_toggle", "")))
                bookmark_act.triggered.connect(lambda: self.add_path_to_bookmarks(target_path))
                menu.addAction(bookmark_act)

            menu.addSeparator()

            open_os_act = QAction("Reveal in file explorer", menu)
            open_os_act.setStatusTip("Open in system file manager")
            open_os_act.setIcon(QIcon(icons.get("file_recent", "")))
            open_os_act.triggered.connect(lambda: self._open_in_os_explorer(target_path))
            menu.addAction(open_os_act)

            copy_path_act = QAction("Copy full path", menu)
            copy_path_act.setStatusTip("Copy the absolute file path to clipboard")
            copy_path_act.setIcon(QIcon(icons.get("copy", "")))
            copy_path_act.triggered.connect(lambda: QApplication.clipboard().setText(target_path))
            menu.addAction(copy_path_act)

            menu.addSeparator()

            target_dir = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)

            new_file_act = QAction("New file...", menu)
            new_file_act.setStatusTip("Create a new file in this directory")
            if "new_file" in icons:
                new_file_act.setIcon(QIcon(icons["new_file"]))
            new_file_act.triggered.connect(lambda: self._create_new_file(target_dir))
            menu.addAction(new_file_act)

            new_folder_act = QAction("New folder...", menu)
            new_folder_act.setStatusTip("Create a new folder in this directory")
            if "new_folder" in icons:
                new_folder_act.setIcon(QIcon(icons["new_folder"]))
            new_folder_act.triggered.connect(lambda: self._create_new_folder(target_dir))
            menu.addAction(new_folder_act)

            if source_index.isValid():
                menu.addSeparator()

                rename_act = QAction("Rename...", menu)
                rename_act.setStatusTip("Rename this file or folder")
                rename_act.setIcon(QIcon(icons.get("rename_file", "")))
                rename_act.triggered.connect(lambda: self._rename_path(target_path))
                menu.addAction(rename_act)

                delete_act = QAction("Delete", menu)
                delete_act.setStatusTip("Move this file or folder to trash")
                delete_act.setIcon(QIcon(icons.get("delete_file", "")))
                delete_act.triggered.connect(lambda: self._delete_path(target_path))
                menu.addAction(delete_act)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def _open_in_os_explorer(self, path):
        if not path or not os.path.exists(path):
            return
        if os.path.isfile(path):
            path = os.path.dirname(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _apply_dialog_font(self, dlg):
        font = getattr(self, "_current_font", self.font())
        if font:
            dlg.setFont(font)
            family = font.family()
            size = font.pointSize()
            dlg.setStyleSheet(f"* {{ font-family: '{family}'; font-size: {size}pt; }}")
            for btn in dlg.findChildren(QPushButton):
                btn.setFont(font)
            for lbl in dlg.findChildren(QLabel):
                lbl.setFont(font)
            for le in dlg.findChildren(QLineEdit):
                le.setFont(font)

    def _get_input_text(self, title, label, text=""):
        dlg = QInputDialog(self)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setTextValue(text)
        self._apply_dialog_font(dlg)
        ok = (dlg.exec_() if hasattr(dlg, 'exec_') else dlg.exec()) == QInputDialog.Accepted
        return dlg.textValue(), ok

    def _show_question_dialog(self, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(buttons)
        msg_box.setDefaultButton(default_button)
        self._apply_dialog_font(msg_box)
        return msg_box.exec_() if hasattr(msg_box, 'exec_') else msg_box.exec()

    def _show_warning_dialog(self, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Warning)
        self._apply_dialog_font(msg_box)
        return msg_box.exec_() if hasattr(msg_box, 'exec_') else msg_box.exec()

    def _create_new_file(self, target_dir):
        filename, ok = self._get_input_text("New File", "Enter file name:")
        if ok and filename.strip():
            filepath = os.path.join(target_dir, filename.strip())
            if not os.path.exists(filepath):
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("")
                    self.refresh_tree()
                    self.file_selected.emit(filepath)
                except Exception as e:
                    self._show_warning_dialog("Error", f"Failed to create file: {e}")

    def _create_new_folder(self, target_dir):
        foldername, ok = self._get_input_text("New Folder", "Enter folder name:")
        if ok and foldername.strip():
            folderpath = os.path.join(target_dir, foldername.strip())
            if not os.path.exists(folderpath):
                try:
                    os.makedirs(folderpath)
                    self.refresh_tree()
                except Exception as e:
                    self._show_warning_dialog("Error", f"Failed to create folder: {e}")

    def _rename_path(self, old_path):
        old_name = os.path.basename(old_path)
        new_name, ok = self._get_input_text("Rename", "Enter new name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
            try:
                os.rename(old_path, new_path)
                self.refresh_tree()
            except Exception as e:
                self._show_warning_dialog("Error", f"Failed to rename: {e}")

    def _delete_path(self, target_path):
        name = os.path.basename(target_path)
        reply = self._show_question_dialog(
            "Delete Confirmation",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                norm_target = os.path.normcase(os.path.abspath(target_path))
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

                editor = getattr(self, 'editor', None)
                if not editor and hasattr(self, 'parent'):
                    editor = self.parent()
                tab_widget = getattr(editor, 'tab', None)
                if tab_widget:
                    for i in range(tab_widget.count() - 1, -1, -1):
                        w = tab_widget.widget(i)
                        fp = getattr(w, 'file_path', None)
                        if fp:
                            norm_fp = os.path.normcase(os.path.abspath(fp))
                            if norm_fp == norm_target or norm_fp.startswith(norm_target + os.sep):
                                w.file_path = None
                                if hasattr(w, 'edit') and hasattr(w.edit, 'document'):
                                    w.edit.document().setModified(False)
                                tab_widget.closeTab(i)

                self.refresh_tree()
            except Exception as e:
                self._show_warning_dialog("Error", f"Failed to delete: {e}")

    def apply_theme(self, colors=None, font=None):
        if not colors:
            colors = {}

        def rgb2hex(rgb):
            if not isinstance(rgb, (list, tuple)) or len(rgb) < 3:
                return "#2b2b2b"
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        bg_color = rgb2hex(colors.get("background", (40, 40, 40)))
        text_color = rgb2hex(colors.get("default", colors.get("tab_selected_text", (210, 210, 210))))
        sel_bg = rgb2hex(colors.get("selection_background", (60, 80, 110)))
        sel_text = rgb2hex(colors.get("selection", (255, 255, 255)))
        border_color = rgb2hex(colors.get("border", (60, 60, 60)))

        if font:
            self._current_font = font
            self.setFont(font)
            self.tree_view.setFont(font)
            self.path_filter_input.setFont(font)
            self.bookmarks_menu.setFont(font)
