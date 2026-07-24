import os
import shutil

from icons import icons
from vendor.Qt.QtCore import QDir, QModelIndex, QSortFilterProxyModel, Qt, Signal, QUrl
from vendor.Qt.QtGui import QColor, QDesktopServices, QIcon
from vendor.Qt.QtWidgets import (
    QAction,
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QHeaderView,
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
    # C / C++ / Rust / Go
    ".c": "#c678dd", ".cpp": "#c678dd", ".h": "#c678dd", ".hpp": "#c678dd",
    ".rs": "#d19a66", ".go": "#00add8",
    # Web
    ".html": "#e06c75", ".css": "#56b6c2", ".js": "#e5c07b", ".ts": "#61afef",
    # Shell / Scripts
    ".sh": "#98c379", ".bat": "#98c379", ".cmd": "#98c379", ".ps1": "#98c379",
    # Media
    ".png": "#c678dd", ".jpg": "#c678dd", ".jpeg": "#c678dd", ".gif": "#c678dd", ".svg": "#c678dd",
}


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
    and colors different file types in QFileSystemModel.
    """
    def __init__(self, parent=None):
        super(FileSystemFilterProxyModel, self).__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._filter_text = ""

    def setFilterFixedString(self, pattern):
        self._filter_text = pattern.strip().lower() if pattern else ""
        super(FileSystemFilterProxyModel, self).setFilterFixedString(pattern)

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True

        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        file_name = source_model.fileName(index)

        # Direct match on name
        if self._filter_text in file_name.lower():
            return True

        # If it's a directory, check if any child item matches recursively
        if source_model.isDir(index):
            num_children = source_model.rowCount(index)
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
    Subclassed QTreeView to catch Return/Enter key presses to open files in tabs or toggle folders.
    """
    file_open_requested = Signal(str)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_index = self.currentIndex()
            if current_index.isValid():
                model = self.model()
                source_index = model.mapToSource(current_index) if hasattr(model, 'mapToSource') else current_index
                fs_model = model.sourceModel() if hasattr(model, 'sourceModel') else model
                path = fs_model.filePath(source_index)
                if os.path.isfile(path):
                    self.file_open_requested.emit(path)
                    event.accept()
                    return
                elif os.path.isdir(path):
                    self.setExpanded(current_index, not self.isExpanded(current_index))
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

    def __init__(self, parent=None, root_path=None):
        super(ExplorerWidget, self).__init__(parent)
        self.setObjectName("explorerWidget")

        self.bookmarks = get_default_bookmarks()
        self._current_root = root_path or os.getcwd()

        self._setup_ui()
        self._setup_connections()
        self.set_root_path(self._current_root)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(4)

        # Top Bar: QLineEdit for filter & direct path navigation
        self.path_filter_input = QLineEdit()
        self.path_filter_input.setObjectName("explorerPathFilterInput")
        self.path_filter_input.setPlaceholderText("Filter or paste path + Enter...")
        self.path_filter_input.setClearButtonEnabled(True)

        # Control Buttons on top right
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(2)

        self.up_btn = QToolButton()
        self.up_btn.setToolTip("Up to Parent Directory")
        self.up_btn.setIcon(QIcon(icons.get("up", "")))

        self.add_bookmark_btn = QToolButton()
        self.add_bookmark_btn.setToolTip("Bookmark Current Directory")
        self.add_bookmark_btn.setIcon(QIcon(icons.get("bookmark_toggle", "")))

        self.bookmarks_menu_btn = QToolButton()
        self.bookmarks_menu_btn.setToolTip("Show Saved Directory Favorites")
        self.bookmarks_menu_btn.setIcon(QIcon(icons.get("bookmark_prev", icons.get("bookmark_toggle", ""))))

        self.bookmarks_menu = QMenu(self)
        self.bookmarks_menu_btn.setMenu(self.bookmarks_menu)
        self.bookmarks_menu_btn.setPopupMode(QToolButton.InstantPopup)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setToolTip("Refresh Directory")
        self.refresh_btn.setIcon(QIcon(icons.get("reload_plugins", icons.get("clear", ""))))

        self.controls_layout.addWidget(self.up_btn)
        self.controls_layout.addWidget(self.add_bookmark_btn)
        self.controls_layout.addWidget(self.bookmarks_menu_btn)
        self.controls_layout.addWidget(self.refresh_btn)

        top_header_layout = QHBoxLayout()
        top_header_layout.setContentsMargins(0, 0, 0, 0)
        top_header_layout.setSpacing(2)
        top_header_layout.addWidget(self.path_filter_input, 1)
        top_header_layout.addLayout(self.controls_layout)

        main_layout.addLayout(top_header_layout)

        # Tree View & File System Model
        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden)

        self.proxy_model = FileSystemFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.fs_model)

        self.tree_view = ExplorerTreeView()
        self.tree_view.setObjectName("explorerTreeView")
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.setAnimated(True)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setDragDropMode(QAbstractItemView.DragOnly)
        self.proxy_model.sort(0, Qt.AscendingOrder)

        # Hide extra columns (size, type, date modified) to keep explorer compact
        for col in range(1, 4):
            self.tree_view.setColumnHidden(col, True)

        main_layout.addWidget(self.tree_view, 1)

        self._update_bookmarks_menu()

    def _setup_connections(self):
        self.path_filter_input.textChanged.connect(self._on_filter_changed)
        self.path_filter_input.returnPressed.connect(self._on_path_entered)

        self.up_btn.clicked.connect(self.navigate_up)
        self.add_bookmark_btn.clicked.connect(self.add_current_to_bookmarks)
        self.refresh_btn.clicked.connect(self.refresh_tree)

        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        self.tree_view.file_open_requested.connect(self.file_selected.emit)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.fs_model.directoryLoaded.connect(self._on_directory_loaded)

    def set_root_path(self, path):
        if not path or not os.path.exists(path):
            path = os.path.expanduser("~")

        if os.path.isfile(path):
            path = os.path.dirname(path)

        path = os.path.abspath(path)
        self._current_root = path

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

    def get_current_root(self):
        return self._current_root

    def _on_filter_changed(self, text):
        self.proxy_model.setFilterFixedString(text)
        if text.strip():
            self.tree_view.expandAll()

    def _on_path_entered(self):
        text = self.path_filter_input.text().strip().strip('"\'')
        if not text:
            return

        norm_path = os.path.abspath(os.path.expanduser(text))

        if os.path.exists(norm_path):
            # Clear filter FIRST so proxy model reveals all contents
            self.path_filter_input.blockSignals(True)
            self.path_filter_input.clear()
            self.path_filter_input.blockSignals(False)
            self.proxy_model.setFilterFixedString("")

            if os.path.isdir(norm_path):
                self.set_root_path(norm_path)
            elif os.path.isfile(norm_path):
                parent_dir = os.path.dirname(norm_path)
                self.set_root_path(parent_dir)
                self._select_and_highlight_file(norm_path)
                self.file_selected.emit(norm_path)
        else:
            # If not a disk path, apply as search filter text
            self.proxy_model.setFilterFixedString(text)

    def _select_and_highlight_file(self, filepath):
        source_index = self.fs_model.index(filepath)
        if source_index.isValid():
            proxy_index = self.proxy_model.mapFromSource(source_index)
            if proxy_index.isValid():
                self.tree_view.setCurrentIndex(proxy_index)
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

        add_act = QAction("★ Bookmark Current Directory", self.bookmarks_menu)
        add_act.setIcon(QIcon(icons.get("bookmark_toggle", "")))
        add_act.triggered.connect(self.add_current_to_bookmarks)
        self.bookmarks_menu.addAction(add_act)

        if sorted_bookmarks:
            remove_menu = QMenu("Remove Favorite...", self.bookmarks_menu)
            remove_menu.setIcon(QIcon(icons.get("clear", "")))
            for path in sorted_bookmarks:
                r_act = QAction(f"{os.path.basename(path) or path}", remove_menu)
                r_act.triggered.connect(lambda checked=False, p=path: self.remove_bookmark(p))
                remove_menu.addAction(r_act)
            self.bookmarks_menu.addMenu(remove_menu)

    def _show_context_menu(self, position):
        proxy_index = self.tree_view.indexAt(position)
        source_index = self.proxy_model.mapToSource(proxy_index) if proxy_index.isValid() else QModelIndex()

        target_path = self.fs_model.filePath(source_index) if source_index.isValid() else self._current_root
        if not target_path:
            target_path = self._current_root

        menu = QMenu(self)

        if os.path.isfile(target_path):
            open_act = QAction("Open in Editor", menu)
            open_act.setIcon(QIcon(icons.get("open", "")))
            open_act.triggered.connect(lambda: self.file_selected.emit(target_path))
            menu.addAction(open_act)
        elif os.path.isdir(target_path):
            set_root_act = QAction("Set as Explorer Root", menu)
            set_root_act.setIcon(QIcon(icons.get("open", "")))
            set_root_act.triggered.connect(lambda: self.set_root_path(target_path))
            menu.addAction(set_root_act)

            bookmark_act = QAction("Add to Favorites/Bookmarks", menu)
            bookmark_act.setIcon(QIcon(icons.get("bookmark_toggle", "")))
            bookmark_act.triggered.connect(lambda: self.add_path_to_bookmarks(target_path))
            menu.addAction(bookmark_act)

        menu.addSeparator()

        open_os_act = QAction("Reveal in File Explorer", menu)
        open_os_act.setIcon(QIcon(icons.get("file_recent", "")))
        open_os_act.triggered.connect(lambda: self._open_in_os_explorer(target_path))
        menu.addAction(open_os_act)

        copy_path_act = QAction("Copy Full Path", menu)
        copy_path_act.setIcon(QIcon(icons.get("copy", "")))
        copy_path_act.triggered.connect(lambda: QApplication.clipboard().setText(target_path))
        menu.addAction(copy_path_act)

        menu.addSeparator()

        target_dir = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)

        new_file_act = QAction("New File...", menu)
        new_file_act.triggered.connect(lambda: self._create_new_file(target_dir))
        menu.addAction(new_file_act)

        new_folder_act = QAction("New Folder...", menu)
        new_folder_act.triggered.connect(lambda: self._create_new_folder(target_dir))
        menu.addAction(new_folder_act)

        if source_index.isValid():
            menu.addSeparator()

            rename_act = QAction("Rename...", menu)
            rename_act.setIcon(QIcon(icons.get("rename_file", "")))
            rename_act.triggered.connect(lambda: self._rename_path(target_path))
            menu.addAction(rename_act)

            delete_act = QAction("Delete", menu)
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

    def _create_new_file(self, target_dir):
        filename, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and filename.strip():
            filepath = os.path.join(target_dir, filename.strip())
            if not os.path.exists(filepath):
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("")
                    self.refresh_tree()
                    self.file_selected.emit(filepath)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create file: {e}")

    def _create_new_folder(self, target_dir):
        foldername, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and foldername.strip():
            folderpath = os.path.join(target_dir, foldername.strip())
            if not os.path.exists(folderpath):
                try:
                    os.makedirs(folderpath)
                    self.refresh_tree()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create folder: {e}")

    def _rename_path(self, old_path):
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
            try:
                os.rename(old_path, new_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to rename: {e}")

    def _delete_path(self, target_path):
        name = os.path.basename(target_path)
        reply = QMessageBox.question(
            self,
            "Delete Confirmation",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")

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

        qss = f"""
            QWidget#explorerWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QLineEdit#explorerPathFilterInput {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 3px 5px;
            }}
            QTreeView#explorerTreeView {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
            }}
            QTreeView#explorerTreeView::item:selected {{
                background-color: {sel_bg};
                color: {sel_text};
            }}
            QTreeView#explorerTreeView::item:hover {{
                background-color: {sel_bg};
            }}
            QToolButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 2px;
            }}
            QToolButton:hover {{
                background-color: {sel_bg};
            }}
            QToolButton::menu-indicator {{
                image: none;
            }}
        """
        self.setStyleSheet(qss)

        if font:
            self.setFont(font)
            self.tree_view.setFont(font)
            self.path_filter_input.setFont(font)
