from vendor.Qt.QtCore import Qt, Signal, QSize, QEvent
from vendor.Qt.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget
from vendor.Qt.QtGui import QFontMetrics
from widgets.outline_utils import create_symbol_item, HtmlDelegate

class SymbolWidget(QDialog):
    symbolSelected = Signal(object)  # emits the line number or any other data

    def __init__(self, symbols, parent=None, center_widget=None, qss=None, font=None, colors=None, ext='.py', placeholder_text="Search symbol...", auto_accept_on_ctrl_release=False):
        super(SymbolWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        self.symbols = symbols
        self.colors = colors
        self._font = font
        self.ext = ext
        self.auto_accept_on_ctrl_release = auto_accept_on_ctrl_release

        # Calculate dynamic size
        if font:
            fm = QFontMetrics(font)
        else:
            fm = QFontMetrics(self.font())

        max_text_width = 0
        for sym in self.symbols:
            name = sym.get('name', '')
            indent = sym.get('indent', 0)
            # Indentation in HtmlDelegate is usually around 15-20 pixels per level
            w = fm.horizontalAdvance(name) if hasattr(fm, 'horizontalAdvance') else fm.width(name)
            w += indent * 20
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
        self.search_le.setPlaceholderText(placeholder_text)
        self.search_le.textChanged.connect(self.filter_symbols)
        if font:
            self.search_le.setFont(font)
        self.search_le.installEventFilter(self)
        layout.addWidget(self.search_le)

        # List
        self.list_widget = QListWidget(self)
        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))
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

        for sym in self.symbols:
            name = sym.get('name', '')
            if filter_text in name.lower():
                item = create_symbol_item(sym, self.colors, self._font, ext=self.ext)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_symbols(self, text):
        self.populate_list(text)

    def eventFilter(self, obj, event):
        if obj == self.search_le and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
                self.keyPressEvent(event)
                return True
        return super(SymbolWidget, self).eventFilter(obj, event)

    def on_item_clicked(self, item):
        line = item.data(Qt.UserRole)
        self.symbolSelected.emit(line)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
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
        elif event.key() == Qt.Key_Tab and (event.modifiers() & Qt.ControlModifier):
            row = self.list_widget.currentRow()
            if row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(row + 1)
            else:
                self.list_widget.setCurrentRow(0)
            return
        elif event.key() == Qt.Key_Backtab and (event.modifiers() & Qt.ControlModifier):
            row = self.list_widget.currentRow()
            if row > 0:
                self.list_widget.setCurrentRow(row - 1)
            else:
                self.list_widget.setCurrentRow(self.list_widget.count() - 1)
            return
        elif event.key() in (Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):
            self.list_widget.keyPressEvent(event)
        else:
            # Pass other keys to the search line edit
            self.search_le.keyPressEvent(event)

    def navigate_next(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)
        else:
            self.list_widget.setCurrentRow(0)

    def navigate_prev(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)
        else:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def keyReleaseEvent(self, event):
        if self.auto_accept_on_ctrl_release and event.key() == Qt.Key_Control:
            item = self.list_widget.currentItem()
            if item:
                self.on_item_clicked(item)
        super(SymbolWidget, self).keyReleaseEvent(event)
