from vendor.Qt.QtCore import Qt, Signal, QSize, QEvent
from vendor.Qt.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from vendor.Qt.QtGui import QFontMetrics

class SnippetWidget(QDialog):
    snippetSelected = Signal(str)  # emits the snippet content
    snippetNameSelected = Signal(str)  # emits the snippet name for save mode

    def __init__(self, snippets, parent=None, center_widget=None, qss=None, font=None, colors=None, mode="insert"):
        super(SnippetWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        self.snippets = snippets  # Dict of {name: content}
        self.colors = colors
        self._font = font
        self.mode = mode

        # Calculate dynamic size
        if font:
            fm = QFontMetrics(font)
        else:
            fm = QFontMetrics(self.font())

        max_text_width = 0
        for name in self.snippets.keys():
            w = fm.horizontalAdvance(name) if hasattr(fm, 'horizontalAdvance') else fm.width(name)
            if w > max_text_width:
                max_text_width = w

        # Base padding: icon (16) + margins + scrollbar (20) + safe area
        calculated_width = max_text_width + 120

        if center_widget:
            max_w = center_widget.width()
            final_width = min(calculated_width, max_w)
        else:
            final_width = calculated_width

        final_height = final_width / 2

        # Enforce minimum size of 400x300
        final_width = max(final_width, 400.0)
        final_height = max(final_height, 200.0)

        self.setFixedSize(QSize(int(final_width), int(final_height)))

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Search field
        self.search_le = QLineEdit(self)
        if self.mode == "save":
            self.search_le.setPlaceholderText("Enter snippet name to save...")
        else:
            self.search_le.setPlaceholderText("Search snippet to insert...")
        self.search_le.textChanged.connect(self.filter_snippets)
        if font:
            self.search_le.setFont(font)
        self.search_le.installEventFilter(self)
        layout.addWidget(self.search_le)

        # List
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        if font:
            self.list_widget.setFont(font)
        layout.addWidget(self.list_widget)

        if qss:
            # We add a generic border for the floating dialog if not defined
            self.setStyleSheet(qss + "\nQDialog { border: 1px solid #555555; }")

        self.populate_list("")

        # Position
        if center_widget:
            center = center_widget.mapToGlobal(center_widget.rect().center())
            myGeo = self.geometry()
            myGeo.moveCenter(center)
            # Offset it to top-center of the editor
            myGeo.moveTop(center_widget.mapToGlobal(center_widget.rect().topLeft()).y() + 20)
            self.move(myGeo.topLeft())

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

    def filter_snippets(self, text):
        self.populate_list(text)

    def eventFilter(self, obj, event):
        if obj == self.search_le and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
                self.keyPressEvent(event)
                return True
        return super(SnippetWidget, self).eventFilter(obj, event)

    def on_item_clicked(self, item):
        if self.mode == "save":
            self.search_le.setText(item.text())
        else:
            content = item.data(Qt.UserRole)
            self.snippetSelected.emit(content)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.mode == "save":
                name = self.search_le.text().strip()
                if name:
                    if name in self.snippets:
                        from vendor.Qt.QtWidgets import QMessageBox
                        reply = QMessageBox.question(self, 'Overwrite Snippet', f"A snippet named '{name}' already exists. Overwrite?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.No:
                            return
                    self.snippetNameSelected.emit(name)
                    self.accept()
            else:
                item = self.list_widget.currentItem()
                if item:
                    self.on_item_clicked(item)
        elif event.key() == Qt.Key_Up:
            row = self.list_widget.currentRow()
            if row > 0:
                self.list_widget.setCurrentRow(row - 1)
        elif event.key() == Qt.Key_Down:
            row = self.list_widget.currentRow()
            if row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(row + 1)
        elif event.key() in (Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
            self.list_widget.keyPressEvent(event)
        else:
            # Pass other keys to the search line edit
            self.search_le.keyPressEvent(event)
