from vendor.Qt.QtCore import Qt, Signal, QSize
from vendor.Qt.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from vendor.Qt.QtGui import QColor, QFont
from widgets.outline_utils import HtmlDelegate

class SymbolWidget(QDialog):
    symbolSelected = Signal(int)  # emits the line number

    def __init__(self, symbols, parent=None, center_widget=None, qss=None, font=None, colors=None, ext='.py'):
        super(SymbolWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(QSize(400, 300))
        
        self.symbols = symbols
        self.colors = colors
        self._font = font
        self.ext = ext

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Search field
        self.search_le = QLineEdit(self)
        self.search_le.setPlaceholderText("Search symbol...")
        self.search_le.textChanged.connect(self.filter_symbols)
        if font:
            self.search_le.setFont(font)
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
        
        from widgets.outline_utils import create_symbol_item
        
        for sym in self.symbols:
            name = sym.get('name', '')
            if filter_text in name.lower():
                item = create_symbol_item(sym, self.colors, self._font, ext=self.ext)
                self.list_widget.addItem(item)
                
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
    def filter_symbols(self, text):
        self.populate_list(text)
        
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
        else:
            # Pass other keys to the search line edit
            self.search_le.keyPressEvent(event)
