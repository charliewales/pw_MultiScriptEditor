from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtGui import QFontMetrics
from vendor.Qt.QtWidgets import QListWidgetItem, QMessageBox
from widgets.searchPopupWidget import SearchPopupWidget


class SnippetWidget(SearchPopupWidget):
    snippetSelected = Signal(str)  # emits the snippet content
    snippetNameSelected = Signal(str)  # emits the snippet name for save mode
    snippetDeleted = Signal(str)  # emits the snippet name to delete
    snippetExecuted = Signal(str)  # emits the snippet content to execute

    def __init__(self, snippets, parent=None, center_widget=None, qss=None, font=None, colors=None, mode="insert"):
        placeholder = "Enter snippet name to save..." if mode == "save" else "Search snippet to insert..."
        super(SnippetWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text=placeholder)

        self.snippets = snippets  # Dict of {name: content}
        self.mode = mode

        # Calculate dynamic size
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for name in self.snippets.keys():
            w = fm.horizontalAdvance(name) if hasattr(fm, 'horizontalAdvance') else fm.width(name)
            if w > max_text_width:
                max_text_width = w
                
        self.resize_and_move(max_text_width)
        self.populate_list("")

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower()

        for name, content in self.snippets.items():
            if filter_text in name.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, content)
                if self._font:
                    item.setFont(self._font)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _apply_dialog_font(self, dialog):
        parent = self.parent()
        font = getattr(parent, 'theme_font', None) if parent else None
        if not font:
            font = self._font
        if not font:
            return
        dialog.setFont(font)
        dialog.setStyleSheet(f"* {{ font-family: '{font.family()}'; }}")
        for btn in dialog.buttons():
            btn.setFont(font)

    def on_item_clicked(self, item):
        if self.mode == "save":
            self.search_le.setText(item.text())
        else:
            content = item.data(Qt.UserRole)
            self.snippetSelected.emit(content)
            self.accept()

    def handle_enter(self):
        if self.mode == "save":
            name = self.search_le.text().strip()
            if name:
                if name in self.snippets:
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle('Overwrite Snippet')
                    msg_box.setText(f"A snippet named '{name}' already exists. Overwrite?")
                    msg_box.setIcon(QMessageBox.Question)
                    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    no_button = msg_box.button(QMessageBox.No)
                    if no_button:
                        msg_box.setDefaultButton(no_button)
                        no_button.setFocus()
                    else:
                        msg_box.setDefaultButton(QMessageBox.No)
                    self._apply_dialog_font(msg_box)
                    reply = msg_box.exec_()
                    if reply == QMessageBox.No:
                        return
                self.snippetNameSelected.emit(name)
                self.accept()
        else:
            super(SnippetWidget, self).handle_enter()

    def handle_execute(self):
        if self.mode != "save":
            item = self.list_widget.currentItem()
            if item:
                content = item.data(Qt.UserRole)
                self.snippetExecuted.emit(content)
                self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            item = self.list_widget.currentItem()
            if item:
                self.snippetDeleted.emit(item.text())
        elif event.key() == Qt.Key_Enter:
            self.handle_execute()
        else:
            super(SnippetWidget, self).keyPressEvent(event)
