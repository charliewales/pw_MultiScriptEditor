import os
from vendor.Qt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox
)
from core.settings_model import SettingsModel


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
