from vendor.Qt.QtCore import Qt, Signal, QSize, QEvent
from vendor.Qt.QtGui import QFontMetrics
from widgets.outline_utils import create_symbol_item, HtmlDelegate
from widgets.searchPopupWidget import SearchPopupWidget

class SymbolWidget(SearchPopupWidget):
    symbolSelected = Signal(object)  # emits the line number or any other data

    def __init__(self, symbols, parent=None, center_widget=None, qss=None, font=None, colors=None, ext='.py', placeholder_text="Search symbol...", auto_accept_on_ctrl_release=False):
        super(SymbolWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text=placeholder_text)

        self.symbols = symbols
        self.ext = ext
        self.auto_accept_on_ctrl_release = auto_accept_on_ctrl_release
        
        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))

        # Calculate dynamic size
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())

        max_text_width = 0
        for sym in self.symbols:
            name = sym.get('name', '')
            indent = sym.get('indent', 0)
            # Indentation in HtmlDelegate is usually around 15-20 pixels per level
            w = fm.horizontalAdvance(name) if hasattr(fm, 'horizontalAdvance') else fm.width(name)
            w += indent * 20
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

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

    def on_item_clicked(self, item):
        line = item.data(Qt.UserRole)
        self.symbolSelected.emit(line)
        self.accept()

    def keyReleaseEvent(self, event):
        if self.auto_accept_on_ctrl_release and event.key() == Qt.Key_Control:
            item = self.list_widget.currentItem()
            if item:
                self.on_item_clicked(item)
        super(SymbolWidget, self).keyReleaseEvent(event)
