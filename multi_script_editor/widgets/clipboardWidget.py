from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtWidgets import QListWidgetItem
from vendor.Qt.QtGui import QFontMetrics
from widgets.searchPopupWidget import SearchPopupWidget


MAX_ENTRIES = 30

class ClipboardManager(object):
    _history = []
    _initialized = False

    @classmethod
    def init(cls):
        """
        Initialize the ClipboardManager by loading the saved history from disk
        and connecting to the system clipboard's dataChanged signal.
        """
        if cls._initialized:
            return
        try:
            from core.settings_model import ClipboardModel
            model = ClipboardModel()
            data = model.read_settings()
            cls._history = data.get('history', [])
        except Exception:
            cls._history = []

        from vendor.Qt.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.dataChanged.connect(cls._on_clipboard_changed)
        cls._initialized = True

    @classmethod
    def _on_clipboard_changed(cls):
        """
        Triggered when the system clipboard changes. Reads the text and appends it to the history.
        """
        from vendor.Qt.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data and mime_data.hasText():
            text = mime_data.text()
            cls.add_text(text)

    @classmethod
    def add_text(cls, text):
        """
        Add text to the history, preventing duplicates and keeping up to MAX_ENTRIES entries.
        """
        if not text or not text.strip():
            return
        if text in cls._history:
            cls._history.remove(text)
        cls._history.insert(0, text)
        if len(cls._history) > MAX_ENTRIES:
            cls._history = cls._history[:MAX_ENTRIES]
        cls.save_history()

    @classmethod
    def save_history(cls):
        """
        Write the current history back to disk.
        """
        try:
            from core.settings_model import ClipboardModel
            model = ClipboardModel()
            model.write_settings({'history': cls._history})
        except Exception:
            pass


class ClipboardWidget(SearchPopupWidget):
    textSelected = Signal(str)

    def __init__(self, history, parent=None, center_widget=None, qss=None, font=None, colors=None):
        """
        Constructor for ClipboardWidget.
        history: list of strings containing previously copied texts.
        """
        super(ClipboardWidget, self).__init__(
            parent, center_widget, qss, font, colors, placeholder_text="Search clipboard history..."
        )
        self.history = history
        self.allow_delete = True

        # Calculate dynamic size based on the longest item preview
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for text in self.history:
            preview = text.replace('\n', ' ↵ ').replace('\r', '').strip()
            if len(preview) > 100:
                preview = preview[:97] + "..."
            w = fm.horizontalAdvance(preview) if hasattr(fm, 'horizontalAdvance') else fm.width(preview)
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def populate_list(self, filter_text):
        """
        Filter and populate the list of clipboard entries.
        """
        self.list_widget.clear()
        filter_text = filter_text.lower()

        for text in self.history:
            preview = text.replace('\n', ' ↵ ').replace('\r', '').strip()
            # Search both in preview (with arrows) and original text
            if filter_text in preview.lower() or filter_text in text.lower():
                item = QListWidgetItem()
                item.setData(Qt.UserRole, text)

                display_text = preview
                if len(display_text) > 100:
                    display_text = display_text[:97] + "..."

                item.setText(display_text)
                if self._font:
                    item.setFont(self._font)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_item_clicked(self, item):
        """
        Handle item selection by emitting the selected text signal and closing the dialog.
        """
        text = item.data(Qt.UserRole)
        self.textSelected.emit(text)
        self.accept()

    def keyPressEvent(self, event):
        """
        Handle Key Press Events. Support deleting entries with the Delete key.
        """
        if event.key() == Qt.Key_Delete and self.allow_delete:
            item = self.list_widget.currentItem()
            if item:
                text = item.data(Qt.UserRole)
                if text in self.history:
                    self.history.remove(text)
                # Persist to disk
                ClipboardManager.save_history()

                # Remove from QListWidget
                row = self.list_widget.row(item)
                self.list_widget.takeItem(row)

                if not self.history:
                    self.reject()
                else:
                    new_row = min(row, self.list_widget.count() - 1)
                    if new_row >= 0:
                        self.list_widget.setCurrentRow(new_row)
            return
        super(ClipboardWidget, self).keyPressEvent(event)
