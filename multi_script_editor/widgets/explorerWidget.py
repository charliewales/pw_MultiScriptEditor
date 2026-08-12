import os
import shutil

from core.diff_manager import DiffManager
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
    QLineEdit,
    QMenu,
    QMessageBox,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

DIRECTORY_COLOR = "#e5c07b"

FILE_TYPE_COLORS = {
    # Python
    ".py": "#61afef", ".pyw": "#61afef", ".pyx": "#61afef",
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
FILTERED_DIRECTORY_NAMES = {"__pycache__"}
_SUPPORTED_EXTENSIONS_VERSION = 0
_SUPPORTED_FILES_FILTER_ENABLED = True


def file_extension_sort_key(file_name):
    return (
        os.path.splitext(file_name)[1].lower(),
        file_name.lower(),
    )


def is_supported_files_filter_enabled():
    return _SUPPORTED_FILES_FILTER_ENABLED


def register_supported_extension(ext):
    """
    Dynamically register an extra supported file extension for Explorer filtering.
    """
    if not ext:
        return
    if not ext.startswith("."):
        ext = "." + ext
    ext = ext.lower()
    if ext in SUPPORTED_EXTENSIONS_EXTRA:
        return

    SUPPORTED_EXTENSIONS_EXTRA.add(ext)
    global _SUPPORTED_EXTENSIONS_VERSION
    _SUPPORTED_EXTENSIONS_VERSION += 1


def get_supported_extensions():
    """
    Returns built-in and dynamically registered file extensions.
    """
    return (
        set(FILE_TYPE_COLORS.keys())
        | SUPPORTED_EXTENSIONS_EXTRA
    )


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
        self._supported_extensions = set()
        self._supported_extensions_version = -1

    def _get_supported_extensions(self):
        if self._supported_extensions_version != _SUPPORTED_EXTENSIONS_VERSION:
            self._supported_extensions = get_supported_extensions()
            self._supported_extensions_version = _SUPPORTED_EXTENSIONS_VERSION
        return self._supported_extensions

    def setFilterFixedString(self, pattern):
        self._filter_text = pattern.strip().lower() if pattern else ""
        super(FileSystemFilterProxyModel, self).setFilterFixedString(pattern)

    def setFilterSupportedOnly(self, enabled):
        """
        If enabled (True / Checked button): Show ONLY supported file types.
        If disabled (False / Unchecked button): Show ALL files.
        """
        self._filter_supported_only = bool(enabled)
        global _SUPPORTED_FILES_FILTER_ENABLED
        _SUPPORTED_FILES_FILTER_ENABLED = self._filter_supported_only
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        file_name = source_model.fileName(index)

        is_directory = source_model.isDir(index)
        if is_directory:
            if (
                self._filter_supported_only
                and file_name.lower() in FILTERED_DIRECTORY_NAMES
            ):
                return False
        else:
            ext = os.path.splitext(file_name)[1].lower()
            # If _filter_supported_only is True (Checked button), filter to supported extensions only
            if self._filter_supported_only:
                if ext not in self._get_supported_extensions():
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
        return (
            file_extension_sort_key(left_name)
            < file_extension_sort_key(right_name)
        )

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole:
            source_index = self.mapToSource(index)
            source_model = self.sourceModel()
            if source_index.isValid() and source_model:
                if source_model.isDir(source_index):
                    # Directory color (Folder gold/yellow)
                    return QColor(DIRECTORY_COLOR)
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


class FileBrowserTree(ExplorerTreeView):
    root_loaded = Signal(str)

    def __init__(
        self,
        parent=None,
        action_handler=None,
        expand_directories_on_click=False,
    ):
        super(FileBrowserTree, self).__init__(parent)
        self._action_handler = action_handler
        self._current_root = ""
        self._loaded_paths = set()
        self._expand_directories_on_click = (
            expand_directories_on_click
        )
        self._pressed_index = QModelIndex()
        self._pressed_index_was_expanded = False

        self.fs_model = QFileSystemModel(self)
        self.fs_model.setFilter(
            QDir.AllEntries
            | QDir.NoDotAndDotDot
            | QDir.AllDirs
            | QDir.Hidden
        )
        self.proxy_model = FileSystemFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.fs_model)

        self.setModel(self.proxy_model)
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAnimated(True)
        self.setSortingEnabled(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setToolTip(
            "- Return/Enter/Middle Click: set root folder\n"
            "- Backspace: go to parent folder"
        )

        self.filter_edit = QLineEdit(self)
        self.filter_edit.setObjectName("fileBrowserFilterInput")
        self.filter_edit.setPlaceholderText("Filter paths...")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setStatusTip("Filter file browser paths")
        self.filter_edit.setFont(self.font())
        self.filter_edit.textChanged.connect(self._on_filter_changed)

        self.proxy_model.sort(0, Qt.AscendingOrder)
        for column in range(1, 4):
            self.setColumnHidden(column, True)

        self.customContextMenuRequested.connect(
            self.show_context_menu
        )
        self.doubleClicked.connect(self._activate_index)
        self.clicked.connect(self._expand_clicked_directory)
        self.fs_model.directoryLoaded.connect(
            self._on_directory_loaded
        )
        self.updateGeometries()
        self._position_filter_edit()

    def setFont(self, font):
        super(FileBrowserTree, self).setFont(font)
        if hasattr(self, "filter_edit"):
            self.filter_edit.setFont(font)
            self.updateGeometries()
            self._position_filter_edit()

    def updateGeometries(self):
        super(FileBrowserTree, self).updateGeometries()
        self.setViewportMargins(
            0,
            self.filter_edit.sizeHint().height() + 2,
            0,
            0,
        )

    def resizeEvent(self, event):
        super(FileBrowserTree, self).resizeEvent(event)
        self._position_filter_edit()

    def _position_filter_edit(self):
        filter_height = self.filter_edit.sizeHint().height()
        frame_width = self.frameWidth()
        self.filter_edit.setGeometry(
            frame_width,
            frame_width,
            max(0, self.width() - frame_width * 2),
            filter_height,
        )

    def _on_filter_changed(self, text):
        self.proxy_model.setFilterFixedString(text)
        if text.strip():
            self.expandAll()

    def set_action_handler(self, handler):
        self._action_handler = handler

    def set_filter_supported_only(self, enabled):
        self.proxy_model.setFilterSupportedOnly(enabled)

    def set_root_path(self, path):
        self._current_root = path or ""
        source_index = self.fs_model.setRootPath(self._current_root)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        self.setRootIndex(
            proxy_index if proxy_index.isValid() else QModelIndex()
        )
        return source_index, proxy_index

    def is_root_loaded(self):
        if not self._current_root:
            return True
        return self._normalized_path(self._current_root) in self._loaded_paths

    @staticmethod
    def _normalized_path(path):
        if not path:
            return ""
        return os.path.normcase(os.path.abspath(path))

    def path_for_index(self, proxy_index):
        if not proxy_index.isValid():
            return ""
        source_index = self.proxy_model.mapToSource(proxy_index)
        return self.fs_model.filePath(source_index)

    def _on_directory_loaded(self, path):
        normalized_path = self._normalized_path(path)
        self._loaded_paths.add(normalized_path)
        if normalized_path != self._normalized_path(self._current_root):
            return
        source_index = self.fs_model.index(self._current_root)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.setRootIndex(proxy_index)
        self.root_loaded.emit(self._current_root)

    def mousePressEvent(self, event):
        self._pressed_index = self.indexAt(event.pos())
        self._pressed_index_was_expanded = (
            self._pressed_index.isValid()
            and self.isExpanded(self._pressed_index)
        )
        super(FileBrowserTree, self).mousePressEvent(event)

    def _activate_index(self, proxy_index):
        path = self.path_for_index(proxy_index)
        if os.path.isfile(path):
            self.file_open_requested.emit(path)

    def _expand_clicked_directory(self, proxy_index):
        if not self._expand_directories_on_click:
            return
        path = self.path_for_index(proxy_index)
        if not os.path.isdir(path):
            return
        expansion_changed = (
            self._pressed_index == proxy_index
            and self.isExpanded(proxy_index)
            != self._pressed_index_was_expanded
        )
        if not expansion_changed and not self.isExpanded(proxy_index):
            self.expand(proxy_index)

    def _selected_paths(self, position):
        selected_indexes = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]
        clicked_index = self.indexAt(position)
        if (
            clicked_index.isValid()
            and clicked_index not in selected_indexes
        ):
            selected_indexes = [clicked_index]

        selected_paths = [
            self.path_for_index(index)
            for index in selected_indexes
        ]
        selected_paths = [path for path in selected_paths if path]
        if not selected_paths and self._current_root:
            selected_paths = [self._current_root]
        return selected_paths, clicked_index

    def _handler_method(self, name):
        return getattr(self._action_handler, name, None)

    def _show_status_tip(self, action):
        owner = self._action_handler or self
        main_window = owner.window()
        if not hasattr(main_window, 'statusBar'):
            return
        if (
            action
            and action.statusTip()
            and getattr(main_window, '_show_status_tips', True)
        ):
            main_window.statusBar().showMessage(action.statusTip())
        else:
            main_window.statusBar().clearMessage()

    def _copy_path(self, path):
        normalized_path = os.path.normpath(path)
        QApplication.clipboard().setText(normalized_path)
        owner = self._action_handler or self
        main_window = owner.window()
        if hasattr(main_window, 'out'):
            main_window.out.showMessage(
                "File path: %s" % normalized_path
            )
        if hasattr(main_window, 'showStatusMessage'):
            main_window.showStatusMessage(
                "File path copied to clipboard"
            )

    def show_context_menu(self, position):
        selected_paths, clicked_index = self._selected_paths(position)
        if not selected_paths:
            return

        menu = QMenu(self)
        menu.setFont(self.font())
        menu.hovered.connect(self._show_status_tip)

        if len(selected_paths) > 1:
            self._populate_multi_path_menu(
                menu,
                selected_paths,
            )
        else:
            self._populate_single_path_menu(
                menu,
                selected_paths[0],
                clicked_index,
            )

        menu.exec_(self.viewport().mapToGlobal(position))

    def _populate_multi_path_menu(self, menu, selected_paths):
        files_to_open = [
            path for path in selected_paths if os.path.isfile(path)
        ]
        if files_to_open:
            open_action = QAction(
                "Open selected files ({0})".format(
                    len(files_to_open)
                ),
                menu,
            )
            open_action.setStatusTip("Open all selected files in tabs")
            open_action.setIcon(QIcon(icons.get("open", "")))
            open_action.triggered.connect(
                lambda: [
                    self.file_open_requested.emit(path)
                    for path in files_to_open
                ]
            )
            menu.addAction(open_action)

        compare_label = ""
        if len(selected_paths) == 2:
            if all(os.path.isfile(path) for path in selected_paths):
                compare_label = "Compare files"
            elif all(os.path.isdir(path) for path in selected_paths):
                compare_label = "Compare folders"
        if compare_label:
            compare_action = QAction(compare_label, menu)
            compare_action.setStatusTip(
                "Compare the two selected items with the configured diff tool"
            )
            compare_action.setIcon(QIcon(icons.get("git_diff", "")))
            compare_action.triggered.connect(
                lambda: DiffManager.run_diff(
                    selected_paths[0],
                    selected_paths[1],
                    parent=self,
                )
            )
            menu.addAction(compare_action)

        copy_action = QAction("Copy selected full paths", menu)
        copy_action.setStatusTip(
            "Copy all selected paths to clipboard"
        )
        copy_action.setIcon(QIcon(icons.get("copy", "")))
        copy_action.triggered.connect(
            lambda: QApplication.clipboard().setText(
                "\n".join(selected_paths)
            )
        )
        menu.addAction(copy_action)

        delete_path = self._handler_method("_delete_path")
        if delete_path:
            menu.addSeparator()
            delete_action = QAction(
                "Delete selected ({0})".format(
                    len(selected_paths)
                ),
                menu,
            )
            delete_action.setStatusTip(
                "Delete selected files and folders"
            )
            delete_action.setIcon(
                QIcon(icons.get("delete_file", ""))
            )
            delete_action.triggered.connect(
                lambda: [
                    delete_path(path)
                    for path in selected_paths
                ]
            )
            menu.addAction(delete_action)

    def _populate_single_path_menu(
        self,
        menu,
        target_path,
        clicked_index,
    ):
        copy_action = QAction("Copy file path", menu)
        copy_action.setStatusTip(
            "Copy the absolute file path to clipboard"
        )
        copy_action.setIcon(QIcon(icons.get("copy", "")))
        copy_action.triggered.connect(
            lambda: self._copy_path(target_path)
        )
        menu.addAction(copy_action)

        menu.addSeparator()

        if os.path.isfile(target_path):
            open_action = QAction(
                "Open in editor",
                menu,
            )
            open_action.setStatusTip(
                "Open this file in a new tab (Double Click / Middle Mouse Button)"
            )
            open_action.setIcon(QIcon(icons.get("open", "")))
            open_action.triggered.connect(
                lambda: self.file_open_requested.emit(target_path)
            )
            menu.addAction(open_action)
        elif os.path.isdir(target_path):
            root_action = QAction(
                "Set as explorer root [MMB]",
                menu,
            )
            root_action.setStatusTip(
                "Navigate into this folder (Middle Mouse Button)"
            )
            root_action.setIcon(QIcon(icons.get("open", "")))
            root_action.triggered.connect(
                lambda: self.directory_set_root_requested.emit(
                    target_path
                )
            )
            menu.addAction(root_action)

            add_bookmark = self._handler_method(
                "add_path_to_bookmarks"
            )
            if add_bookmark:
                menu.addSeparator()
                bookmark_action = QAction(
                    "Add to favorites/bookmarks",
                    menu,
                )
                bookmark_action.setStatusTip("Bookmark this folder")
                bookmark_action.setIcon(
                    QIcon(icons.get("bookmark_toggle", ""))
                )
                bookmark_action.triggered.connect(
                    lambda: add_bookmark(target_path)
                )
                menu.addAction(bookmark_action)

        menu.addSeparator()


        menu.addSeparator()

        reveal_action = QAction("Reveal in file explorer", menu)
        reveal_action.setStatusTip("Open in system file manager")
        reveal_action.setIcon(
            QIcon(icons.get("file_recent", ""))
        )
        reveal_action.triggered.connect(
            lambda: self._reveal_path(target_path)
        )
        menu.addAction(reveal_action)


        target_dir = (
            target_path
            if os.path.isdir(target_path)
            else os.path.dirname(target_path)
        )
        create_file = self._handler_method("_create_new_file")
        create_folder = self._handler_method("_create_new_folder")
        if create_file or create_folder:
            menu.addSeparator()
        if create_file:
            new_file_action = QAction("New file...", menu)
            new_file_action.setStatusTip(
                "Create a new file in this directory"
            )
            if "new_file" in icons:
                new_file_action.setIcon(QIcon(icons["new_file"]))
            new_file_action.triggered.connect(
                lambda: create_file(target_dir)
            )
            menu.addAction(new_file_action)
        if create_folder:
            new_folder_action = QAction("New folder...", menu)
            new_folder_action.setStatusTip(
                "Create a new folder in this directory"
            )
            if "new_folder" in icons:
                new_folder_action.setIcon(
                    QIcon(icons["new_folder"])
                )
            new_folder_action.triggered.connect(
                lambda: create_folder(target_dir)
            )
            menu.addAction(new_folder_action)

        rename_path = self._handler_method("_rename_path")
        delete_path = self._handler_method("_delete_path")
        if (
            clicked_index.isValid()
            and (rename_path or delete_path)
        ):
            menu.addSeparator()
            if delete_path:
                delete_action = QAction("Delete", menu)
                delete_action.setStatusTip(
                    "Move this file or folder to trash"
                )
                delete_action.setIcon(
                    QIcon(icons.get("delete_file", ""))
                )
                delete_action.triggered.connect(
                    lambda: delete_path(target_path)
                )
                menu.addAction(delete_action)
            if rename_path:
                rename_action = QAction("Rename...", menu)
                rename_action.setStatusTip(
                    "Rename this file or folder"
                )
                rename_action.setIcon(
                    QIcon(icons.get("rename_file", ""))
                )
                rename_action.triggered.connect(
                    lambda: rename_path(target_path)
                )
                menu.addAction(rename_action)

    def _reveal_path(self, path):
        reveal_path = self._handler_method("_open_in_os_explorer")
        if reveal_path:
            reveal_path(path)
            return
        if not path or not os.path.exists(path):
            return
        if os.path.isfile(path):
            path = os.path.dirname(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))


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
        self.refresh_btn.setIcon(QIcon(icons.get("clear", "")))

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

        # Shared file browser used by both Explorer and breadcrumbs.
        self.tree_view = FileBrowserTree(
            self,
            action_handler=self,
        )
        self.tree_view.setObjectName("explorerTreeView")
        self.fs_model = self.tree_view.fs_model
        self.proxy_model = self.tree_view.proxy_model

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

        self.tree_view.file_open_requested.connect(self.file_selected.emit)
        self.tree_view.directory_set_root_requested.connect(self.set_root_path)
        self.tree_view.navigate_parent_requested.connect(self.navigate_up)
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

        self.tree_view.set_root_path(path)

        self.folder_changed.emit(path)

    def _on_directory_loaded(self, path):
        if os.path.abspath(path) == os.path.abspath(self._current_root):
            if getattr(self, '_pending_select_file', None):
                self._retry_pending_selection(self._pending_select_file)

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
        self._pending_select_file = filepath

        if os.path.normcase(dirpath) != os.path.normcase(self._current_root):
            self.set_root_path(dirpath)

        if self._select_and_highlight_file(filepath):
            self._pending_select_file = None
            return

        QTimer.singleShot(
            50,
            lambda path=filepath: self._retry_pending_selection(path),
        )
        QTimer.singleShot(
            200,
            lambda path=filepath: self._retry_pending_selection(path),
        )

    def _retry_pending_selection(self, filepath):
        if self._pending_select_file != filepath:
            return
        if self._select_and_highlight_file(filepath):
            self._pending_select_file = None

    def _select_and_highlight_file(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return False
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
                return True
        return False

    def navigate_up(self):
        parent_dir = os.path.dirname(self._current_root)
        if parent_dir and parent_dir != self._current_root and os.path.exists(parent_dir):
            self.set_root_path(parent_dir)

    def refresh_tree(self):
        current = self._current_root
        self.fs_model.setRootPath("")
        self.fs_model.setRootPath(current)
        self.set_root_path(current)

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
        self.tree_view.show_context_menu(position)

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
            for child in dlg.findChildren(QWidget):
                child.setFont(font)

    def _exec_dialog(self, dlg):
        return dlg.exec_() if hasattr(dlg, 'exec_') else dlg.exec()

    def _get_input_text(self, title, label, text=""):
        dlg = QInputDialog(self)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setTextValue(text)
        self._apply_dialog_font(dlg)
        ok = self._exec_dialog(dlg) == QInputDialog.Accepted
        return dlg.textValue(), ok

    def _show_question_dialog(self, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.Yes):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(buttons)
        button = msg_box.button(default_button)
        if button:
            msg_box.setDefaultButton(button)
            button.setFocus()
        else:
            msg_box.setDefaultButton(default_button)
        self._apply_dialog_font(msg_box)
        return self._exec_dialog(msg_box)

    def _show_warning_dialog(self, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Warning)
        self._apply_dialog_font(msg_box)
        return self._exec_dialog(msg_box)

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

        if font:
            self._current_font = font
            self.setFont(font)
            self.tree_view.setFont(font)
            self.path_filter_input.setFont(font)
            self.bookmarks_menu.setFont(font)
