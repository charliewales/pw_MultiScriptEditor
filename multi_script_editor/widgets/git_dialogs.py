import os
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QGroupBox,
    QWidget,
)
from core.git_manager import GitManager
from core.diff_manager import DiffManager


def show_themed_msg_box(parent, title, text, icon=QMessageBox.Information):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)

    p = parent.parent() if hasattr(parent, 'parent') and callable(parent.parent) and parent.parent() else parent
    font = getattr(p, 'theme_font', getattr(p, 'font', None))
    if callable(font):
        font = font()

    if font:
        msg_box.setFont(font)
        family = font.family()
        size = font.pointSize()
        msg_box.setStyleSheet(f"QMessageBox, QLabel, QPushButton {{ font-family: '{family}'; font-size: {size}pt; }}")
        for w in msg_box.findChildren(QWidget):
            w.setFont(font)

    return msg_box.exec_()


class GitCommitDialog(QDialog):
    """
    Dialog for reviewing file status and entering a commit message to commit the tab's file.
    """
    def __init__(self, parent=None, file_path=""):
        super(GitCommitDialog, self).__init__(parent)
        self.file_path = file_path
        self.status_info = GitManager.get_file_status(file_path)

        filename = os.path.basename(file_path)
        self.setWindowTitle(f"Git Commit - {filename}")
        self.resize(550, 380)

        if hasattr(parent, 'theme_font') and parent.theme_font:
            self.setStyleSheet(parent.styleSheet() + f"\n* {{ font-family: '{parent.theme_font.family()}'; }}")

        layout = QVBoxLayout(self)

        # File info section
        info_box = QGroupBox("File Git Status", self)
        info_layout = QVBoxLayout(info_box)

        file_lbl = QLabel(f"<b>File:</b> {file_path}", self)
        file_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        repo_lbl = QLabel(f"<b>Repository:</b> {self.status_info.get('repo_root', '')}", self)
        repo_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        status_str = f"{self.status_info.get('status_text', 'Clean')} (Branch: <b>{self.status_info.get('branch', '')}</b>)"
        status_lbl = QLabel(f"<b>Status:</b> {status_str}", self)

        info_layout.addWidget(file_lbl)
        info_layout.addWidget(repo_lbl)
        info_layout.addWidget(status_lbl)
        layout.addWidget(info_box)

        # Commit message input
        msg_lbl = QLabel("Commit Message:", self)
        layout.addWidget(msg_lbl)

        self.msg_edit = QTextEdit(self)
        self.msg_edit.setPlaceholderText("Enter a descriptive commit message...")
        layout.addWidget(self.msg_edit)

        # Buttons
        btn_layout = QHBoxLayout()

        self.diff_btn = QPushButton("View Diff (vs HEAD)", self)
        self.diff_btn.clicked.connect(self.view_diff)
        btn_layout.addWidget(self.diff_btn)

        btn_layout.addStretch()

        self.commit_btn = QPushButton("Commit File", self)
        self.commit_btn.setDefault(True)
        self.commit_btn.clicked.connect(self.do_commit)
        btn_layout.addWidget(self.commit_btn)

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def view_diff(self):
        head_path = GitManager.get_head_file_temp_path(self.file_path)
        if head_path and os.path.exists(head_path):
            DiffManager.run_diff(head_path, self.file_path, parent=self.parent())
        else:
            show_themed_msg_box(
                self,
                "Git Diff",
                "No previous HEAD revision found for this file (file might be untracked or new).",
                QMessageBox.Information
            )

    def do_commit(self):
        message = self.msg_edit.toPlainText().strip()
        if not message:
            show_themed_msg_box(self, "Commit Warning", "Please enter a commit message.", QMessageBox.Warning)
            return

        success, msg = GitManager.commit_file(self.file_path, message)
        if success:
            show_themed_msg_box(self, "Commit Successful", f"File committed successfully!\n\n{msg}", QMessageBox.Information)
            self.accept()
        else:
            show_themed_msg_box(self, "Commit Failed", f"Could not commit file:\n{msg}", QMessageBox.Critical)


class GitHistoryDialog(QDialog):
    """
    Dialog for viewing Git commit log of a file and comparing revisions.
    """
    def __init__(self, parent=None, file_path=""):
        super(GitHistoryDialog, self).__init__(parent)
        self.file_path = file_path
        filename = os.path.basename(file_path)
        self.setWindowTitle(f"Git File History - {filename}")
        self.resize(750, 450)

        if hasattr(parent, 'theme_font') and parent.theme_font:
            self.setStyleSheet(parent.styleSheet() + f"\n* {{ font-family: '{parent.theme_font.family()}'; }}")

        layout = QVBoxLayout(self)

        # File header
        hdr_lbl = QLabel(f"Commit History for: <b>{file_path}</b>", self)
        hdr_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(hdr_lbl)

        # Table widget
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Commit", "Author", "Date", "Message"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self.compare_selected_revision)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        self.compare_btn = QPushButton("Compare Revision with Current", self)
        self.compare_btn.clicked.connect(self.compare_selected_revision)
        btn_layout.addWidget(self.compare_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self.load_history()

    def load_history(self):
        history = GitManager.get_file_history(self.file_path)
        self.table.setRowCount(len(history))

        for row, item in enumerate(history):
            hash_item = QTableWidgetItem(item['short_hash'])
            hash_item.setData(Qt.UserRole, item['hash'])
            author_item = QTableWidgetItem(item['author'])
            date_item = QTableWidgetItem(item['date'])
            subject_item = QTableWidgetItem(item['subject'])

            self.table.setItem(row, 0, hash_item)
            self.table.setItem(row, 1, author_item)
            self.table.setItem(row, 2, date_item)
            self.table.setItem(row, 3, subject_item)

        if history:
            self.table.selectRow(0)

    def compare_selected_revision(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            show_themed_msg_box(self, "Git History", "Please select a commit to compare.", QMessageBox.Information)
            return

        row = self.table.currentRow()
        commit_hash = self.table.item(row, 0).data(Qt.UserRole)
        short_hash = self.table.item(row, 0).text()

        commit_temp_path = GitManager.get_commit_file_temp_path(self.file_path, commit_hash)
        if commit_temp_path and os.path.exists(commit_temp_path):
            DiffManager.run_diff(commit_temp_path, self.file_path, parent=self.parent())
        else:
            show_themed_msg_box(
                self,
                "Git History Error",
                f"Could not retrieve file content at commit {short_hash}.",
                QMessageBox.Warning
            )
