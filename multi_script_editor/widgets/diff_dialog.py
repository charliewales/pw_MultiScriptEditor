import os
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFontMetrics, QIcon
from vendor.Qt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
    QListWidgetItem
)
from core.settings_model import SettingsModel
from core.diff_manager import DiffManager
from widgets.searchPopupWidget import SearchPopupWidget
from icons import icons


class DiffToolConfigDialog(QDialog):
    """
    Dialog to select or enter the executable path/command for the external diff tool.
    """
    def __init__(self, parent=None, current_path=""):
        super(DiffToolConfigDialog, self).__init__(parent)
        self.setWindowTitle("Configure External Diff Tool")
        self.resize(520, 140)

        if hasattr(parent, 'theme_font') and parent.theme_font:
            self.setStyleSheet(parent.styleSheet() + "\n* { font-family: '%s'; }" % parent.theme_font.family())

        layout = QVBoxLayout(self)

        info_label = QLabel(
            "Please specify the path or command for your preferred Diff tool\n"
            "(e.g., Meld, WinMerge, KDiff3, Beyond Compare):"
        )
        layout.addWidget(info_label)

        path_layout = QHBoxLayout()
        self.path_le = QLineEdit(current_path)
        self.path_le.setPlaceholderText("e.g. C:\\Program Files\\Meld\\Meld.exe or meld")
        path_layout.addWidget(self.path_le)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_executable)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_executable(self):
        file_filter = "Executables (*.exe *.bat *.cmd);;All Files (*)" if os.name == 'nt' else "All Files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Diff Tool Executable", "", file_filter)
        if path:
            self.path_le.setText(os.path.normpath(path))

    def get_path(self):
        return self.path_le.text().strip()


class CompareWidget(SearchPopupWidget):
    """
    SearchPopupWidget to search and select a file/directory/tab to compare against.
    """
    def __init__(self, tab_widget, current_index, parent=None, center_widget=None, qss=None, font=None, colors=None):
        super(CompareWidget, self).__init__(
            parent, center_widget, qss, font, colors, placeholder_text="Search file or tab to compare..."
        )
        self.tab_widget = tab_widget
        self.current_index = current_index
        self.editor_parent = parent

        current_widget = self.tab_widget.widget(current_index) if (current_index >= 0 and current_index < self.tab_widget.count()) else None
        self.current_file = getattr(current_widget, 'file_path', "") if current_widget else ""

        # Collect items
        self.items_data = []
        self._build_items()

        # Dynamic width calculation
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for item_info in self.items_data:
            text = item_info['label']
            w = fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def _build_items(self):
        # 1. Other open tabs with valid file_path
        if self.current_index >= 0:
            for i in range(self.tab_widget.count()):
                if i == self.current_index:
                    continue
                w = self.tab_widget.widget(i)
                other_file = getattr(w, 'file_path', "")
                if other_file and os.path.exists(other_file):
                    tab_title = self.tab_widget.tabText(i)
                    label = f"{tab_title}  ({other_file})"
                    icon_name = 'git_diff' if 'git_diff' in icons else 'open'
                    self.items_data.append({
                        'label': label,
                        'type': 'tab_file',
                        'path': other_file,
                        'icon': icon_name,
                        'tooltip': f"Compare with open tab: {other_file}"
                    })

        # 2. Browse File & Directory options
        if self.current_file:
            self.items_data.append({
                'label': "Browse File...",
                'type': 'browse_file',
                'icon': 'open' if 'open' in icons else None,
                'tooltip': "Select a file from disk to compare against current file"
            })

        # 3. Configure Diff Tool...
        self.items_data.append({
            'label': "Configure Diff Tool...",
            'type': 'config',
            'icon': 'settings' if 'settings' in icons else None,
            'tooltip': "Specify external diff tool path or command"
        })

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower().strip()

        for item_info in self.items_data:
            label = item_info['label']
            if filter_text in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, item_info)
                if item_info.get('icon') and item_info['icon'] in icons:
                    item.setIcon(QIcon(icons[item_info['icon']]))
                if item_info.get('tooltip'):
                    item.setToolTip(item_info['tooltip'])
                if self._font:
                    item.setFont(self._font)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_item_clicked(self, item):
        item_info = item.data(Qt.UserRole)
        if not item_info:
            return

        self.accept()
        itype = item_info.get('type')

        if itype == 'tab_file':
            other_path = item_info.get('path')
            DiffManager.run_diff(self.current_file, other_path, parent=self.editor_parent)
        elif itype == 'browse_file':
            path, _ = QFileDialog.getOpenFileName(self.editor_parent, "Select File to Compare")
            if path:
                DiffManager.run_diff(self.current_file, path, parent=self.editor_parent)
        elif itype == 'browse_dir':
            path = QFileDialog.getExistingDirectory(self.editor_parent, "Select Directory to Compare")
            if path:
                DiffManager.run_diff(self.current_file, path, parent=self.editor_parent)
        elif itype == 'browse_two_files':
            f1, _ = QFileDialog.getOpenFileName(self.editor_parent, "Select First File")
            if f1:
                f2, _ = QFileDialog.getOpenFileName(self.editor_parent, "Select Second File")
                if f2:
                    DiffManager.run_diff(f1, f2, parent=self.editor_parent)
        elif itype == 'browse_two_dirs':
            d1 = QFileDialog.getExistingDirectory(self.editor_parent, "Select First Directory")
            if d1:
                d2 = QFileDialog.getExistingDirectory(self.editor_parent, "Select Second Directory")
                if d2:
                    DiffManager.run_diff(d1, d2, parent=self.editor_parent)
        elif itype == 'config':
            DiffManager.configure_diff_tool(parent=self.editor_parent)

    def handle_enter(self):
        item = self.list_widget.currentItem()
        if item:
            self.on_item_clicked(item)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.handle_enter()
        else:
            super(CompareWidget, self).keyPressEvent(event)
