from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtWidgets import QListWidgetItem
from vendor.Qt.QtGui import QIntValidator
from widgets.searchPopupWidget import SearchPopupWidget
from widgets.outline_utils import HtmlDelegate
from widgets.bookmarkWidget import create_bookmark_item

class GotoLineWidget(SearchPopupWidget):
    lineSelected = Signal(int)

    def __init__(self, editor_widget, max_lines, parent=None, center_widget=None, qss=None, font=None, colors=None, highlighter_class=None):
        super(GotoLineWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text="Go to line (1-{})...".format(max_lines))
        self.editor_widget = editor_widget
        self.max_lines = max_lines
        self.highlighter_class = highlighter_class

        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))

        self.search_le.setValidator(QIntValidator(1, max_lines, self))
        self.resize_and_move(640)

    def populate_list(self, filter_text):
        self.list_widget.clear()
        if not filter_text.isdigit():
            return

        line_num = int(filter_text)
        if 1 <= line_num <= self.max_lines:
            start_line = max(1, line_num - 4)
            end_line = min(self.max_lines, line_num + 5)

            target_item = None
            for i in range(start_line, end_line + 1):
                block = self.editor_widget.document().findBlockByNumber(i - 1)
                text = block.text()
                if len(text) > 80:
                    text = text[:80] + "..."

                b = {'line': i, 'text': text}
                item = create_bookmark_item(b, self.colors, self._font, self.highlighter_class)

                self.list_widget.addItem(item)
                if i == line_num:
                    target_item = item

            if target_item:
                self.list_widget.setCurrentItem(target_item)

    def on_item_clicked(self, item):
        line = item.data(Qt.UserRole)
        self.lineSelected.emit(line)
        self.accept()

    def handle_enter(self):
        item = self.list_widget.currentItem()
        if item:
            line = item.data(Qt.UserRole)
            self.lineSelected.emit(line)
            self.accept()
            return
            
        text = self.search_le.text()
        if text.isdigit():
            line_num = int(text)
            if 1 <= line_num <= self.max_lines:
                self.lineSelected.emit(line_num)
                self.accept()
                return
        super(GotoLineWidget, self).handle_enter()
