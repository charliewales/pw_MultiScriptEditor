from vendor.Qt.QtCore import Qt, QSize, QEvent
from vendor.Qt.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget

class SearchPopupWidget(QDialog):
    def __init__(self, parent=None, center_widget=None, qss=None, font=None, colors=None, placeholder_text="Search..."):
        super(SearchPopupWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        self.colors = colors
        self._font = font
        self.center_widget = center_widget

        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # Search field
        self.search_le = QLineEdit(self)
        self.search_le.setPlaceholderText(placeholder_text)
        self.search_le.textChanged.connect(self.filter_items)
        if font:
            self.search_le.setFont(font)
        self.search_le.installEventFilter(self)
        self.main_layout.addWidget(self.search_le)

        # List
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        if font:
            self.list_widget.setFont(font)
        self.main_layout.addWidget(self.list_widget)

        if qss:
            # We add a generic border for the floating dialog if not defined
            self.setStyleSheet(qss + "\nQDialog { border: 1px solid #555555; }")

    def resize_and_move(self, max_text_width):
        # Base padding: icon (16) + margins + scrollbar (20) + safe area
        calculated_width = max_text_width + 120

        if self.center_widget:
            max_w = self.center_widget.width()
            final_width = min(calculated_width, max_w)
        else:
            final_width = calculated_width

        final_height = final_width / 2

        # Enforce minimum size of 400x300
        final_width = max(final_width, 400.0)
        final_height = max(final_height, 200.0)

        self.setFixedSize(QSize(int(final_width), int(final_height)))

        # Position
        if self.center_widget:
            center = self.center_widget.mapToGlobal(self.center_widget.rect().center())
            myGeo = self.geometry()
            myGeo.moveCenter(center)
            # Offset it to top-center of the editor
            myGeo.moveTop(self.center_widget.mapToGlobal(self.center_widget.rect().topLeft()).y() + 20)
            self.move(myGeo.topLeft())

    def filter_items(self, text):
        self.populate_list(text)

    def populate_list(self, filter_text):
        pass

    def on_item_clicked(self, item):
        pass

    def eventFilter(self, obj, event):
        if obj == self.search_le and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End, Qt.Key_Tab, Qt.Key_Backtab):
                self.keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Delete and getattr(self, 'allow_delete', False):
                self.keyPressEvent(event)
                return True
        return super(SearchPopupWidget, self).eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_enter()
        elif event.key() == Qt.Key_Up:
            self.navigate_prev()
        elif event.key() == Qt.Key_Down:
            self.navigate_next()
        elif event.key() == Qt.Key_Tab and (event.modifiers() & Qt.ControlModifier):
            self.navigate_next(wrap=True)
            return
        elif event.key() == Qt.Key_Backtab and (event.modifiers() & Qt.ControlModifier):
            self.navigate_prev(wrap=True)
            return
        elif event.key() in (Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
            self.list_widget.keyPressEvent(event)
        else:
            # Pass other keys to the search line edit
            self.search_le.keyPressEvent(event)
            
    def navigate_next(self, wrap=False):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)
        elif wrap:
            self.list_widget.setCurrentRow(0)

    def navigate_prev(self, wrap=False):
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)
        elif wrap:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def handle_enter(self):
        item = self.list_widget.currentItem()
        if item:
            self.on_item_clicked(item)
