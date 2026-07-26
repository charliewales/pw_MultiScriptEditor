import os
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFontMetrics, QIcon
from vendor.Qt.QtWidgets import QApplication, QListWidgetItem
from icons import icons
from widgets.outline_utils import HtmlDelegate
from widgets.searchPopupWidget import SearchPopupWidget
from core.git_manager import GitManager


class GitPopupWidget(SearchPopupWidget):
    """
    Floating search popup widget displaying Git actions for the active file tab (Ctrl+Shift+G).
    Subclasses SearchPopupWidget.
    """

    def __init__(
        self,
        parent=None,
        center_widget=None,
        qss=None,
        font=None,
        colors=None,
        file_path="",
        tab_widget=None,
        tab_index=-1,
    ):
        super(GitPopupWidget, self).__init__(
            parent,
            center_widget,
            qss,
            font,
            colors,
            placeholder_text="Search Git action...",
        )
        self.file_path = file_path
        self.tab_widget = tab_widget
        self.tab_index = tab_index

        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))
        self.actions_data = []

        if file_path and os.path.exists(file_path) and GitManager.is_in_repo(file_path):
            self.load_git_actions()

        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for act in self.actions_data:
            title = act.get("title", "")
            w = fm.horizontalAdvance(title) if hasattr(fm, "horizontalAdvance") else fm.width(title)
            w += 40
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def load_git_actions(self):
        status_info = GitManager.get_file_status(self.file_path)
        branch = status_info.get("branch", "HEAD")
        status_text = status_info.get("status_text", "Clean")

        # Branch & status header info item
        self.actions_data.append(
            {
                "title": f"Branch: {branch} ({status_text})",
                "icon": icons.get("git_branch"),
                "is_header": True,
            }
        )

        # Commit File
        self.actions_data.append(
            {
                "title": "Commit File...",
                "icon": icons.get("git_commit"),
                "callback": lambda: self.tab_widget.git_commit_dialog(self.file_path) if self.tab_widget else None,
            }
        )

        # Copy Path Relative to Repo
        rel_path = status_info.get("relative_path", "")
        if rel_path:
            self.actions_data.append(
                {
                    "title": "Copy Path Relative to Repo",
                    "icon": icons.get("copy"),
                    "callback": lambda rp=rel_path: QApplication.clipboard().setText(
                        rp
                    ),
                }
            )

        # Discard Changes
        if status_info.get("is_modified"):
            self.actions_data.append(
                {
                    "title": "Discard Changes...",
                    "icon": icons.get("git_discard"),
                    "callback": lambda: self.tab_widget.git_discard_changes(self.tab_index, self.file_path)
                    if self.tab_widget
                    else None,
                }
            )

        # File History / Log
        self.actions_data.append(
            {
                "title": "File History / Log...",
                "icon": icons.get("git_history"),
                "callback": lambda: self.tab_widget.git_history_dialog(self.file_path) if self.tab_widget else None,
            }
        )

        # Git Diff vs HEAD
        self.actions_data.append(
            {
                "title": "Git Diff (vs HEAD)",
                "icon": icons.get("git_diff"),
                "callback": lambda: self.tab_widget.run_git_diff(self.file_path) if self.tab_widget else None,
            }
        )

        # Stage / Unstage File
        if status_info.get("is_staged"):
            self.actions_data.append(
                {
                    "title": "Unstage File",
                    "icon": icons.get("git_unstage"),
                    "callback": lambda: self.tab_widget.git_unstage(self.file_path) if self.tab_widget else None,
                }
            )
        else:
            self.actions_data.append(
                {
                    "title": "Stage File",
                    "icon": icons.get("git_stage"),
                    "callback": lambda: self.tab_widget.git_stage(self.file_path) if self.tab_widget else None,
                }
            )

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower()

        c = self.colors or {}
        text_color = c.get("text", "#d4d4d4")
        sub_color = c.get("comment", "#808080")

        first_selectable_row = -1

        for act in self.actions_data:
            title = act.get("title", "")
            is_header = act.get("is_header", False)

            if is_header or filter_text in title.lower():
                item = QListWidgetItem()
                if self._font:
                    item.setFont(self._font)
                item.setFlags(Qt.NoItemFlags if is_header else (Qt.ItemIsEnabled | Qt.ItemIsSelectable))

                if is_header:
                    html = f'<div style="color: {sub_color}; font-style: italic;">{title}</div>'
                else:
                    html = f'<div style="color: {text_color};">{title}</div>'

                item.setText(html)
                if act.get("icon"):
                    item.setIcon(QIcon(act["icon"]))

                item.setData(Qt.UserRole, act)
                self.list_widget.addItem(item)

                if not is_header and first_selectable_row == -1:
                    first_selectable_row = self.list_widget.count() - 1

        if first_selectable_row != -1:
            self.list_widget.setCurrentRow(first_selectable_row)

    def on_item_clicked(self, item):
        act_data = item.data(Qt.UserRole)
        if not act_data or act_data.get("is_header"):
            return

        callback = act_data.get("callback")
        self.accept()
        if callback:
            callback()
