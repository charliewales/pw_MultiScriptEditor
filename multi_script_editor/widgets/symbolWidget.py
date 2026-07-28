from core.outline_parser import OutlineParser
from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtGui import QFontMetrics
from widgets.outline_utils import HtmlDelegate, create_symbol_item
from widgets.searchPopupWidget import SearchPopupWidget


class SymbolWidget(SearchPopupWidget):
    symbolSelected = Signal(object)  # emits the line number or any other data
    symbolDeleted = Signal(object)

    def __init__(self, symbols, parent=None, center_widget=None, qss=None, font=None, colors=None, ext='.py', placeholder_text="Search symbol...", auto_accept_on_ctrl_release=False, allow_delete=False):
        super(SymbolWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text=placeholder_text)

        if any('children' in s for s in symbols):
            self.symbols = OutlineParser.flatten_symbols(symbols)
        else:
            self.symbols = symbols
        self.ext = ext
        self.auto_accept_on_ctrl_release = auto_accept_on_ctrl_release
        self.allow_delete = allow_delete
        self._items_by_symbol_id = {}
        
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
            if 'icon' in sym:
                w += 24 # Typical icon size + margin
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def populate_list(self, filter_text):
        while self.list_widget.count():
            self.list_widget.takeItem(0)

        filter_text = filter_text.lower()

        for sym in self.symbols:
            name = sym.get('name', '')
            if filter_text in name.lower():
                symbol_id = id(sym)
                item = self._items_by_symbol_id.get(symbol_id)
                if item is None:
                    item = create_symbol_item(
                        sym,
                        self.colors,
                        self._font,
                        ext=self.ext,
                    )
                    self._items_by_symbol_id[symbol_id] = item
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.allow_delete:
            item = self.list_widget.currentItem()
            if item:
                line = item.data(Qt.UserRole)
                self.symbolDeleted.emit(line)
            return
        super(SymbolWidget, self).keyPressEvent(event)

    def remove_item_by_data(self, data_val):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == data_val:
                self.list_widget.takeItem(i)
                break
        for i, sym in enumerate(self.symbols):
            if sym.get('line') == data_val:
                self._items_by_symbol_id.pop(id(sym), None)
                self.symbols.pop(i)
                break
