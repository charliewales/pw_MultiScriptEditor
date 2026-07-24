import html

from icons import icons
from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtGui import QFontMetrics, QIcon
from vendor.Qt.QtWidgets import QListWidgetItem
from widgets.outline_utils import HtmlDelegate
from widgets.searchPopupWidget import SearchPopupWidget


def create_bookmark_item(bookmark, theme_colors=None, font=None, highlighter_class=None):
    """
    Creates and formats a QListWidgetItem for a given bookmark,
    displaying the line number and the syntax-highlighted line preview.
    """
    line = bookmark.get('line', 1)
    text = bookmark.get('text', '')

    item = QListWidgetItem()
    item.setData(Qt.UserRole, line)

    if font:
        item.setFont(font)

    if not theme_colors:
        theme_colors = {}

    def rgb2hex(rgb):
        if not isinstance(rgb, (list, tuple)) or len(rgb) < 3:
            return "#ffffff"
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

    c_line = rgb2hex(theme_colors.get('methods', (120, 190, 205)))
    c_text = rgb2hex(theme_colors.get('default', theme_colors.get("tab_selected_text", (210, 210, 210))))

    if highlighter_class:
        from vendor.Qt.QtGui import QTextDocument
        # We create a temporary document to highlight the text of this bookmark.
        temp_doc = QTextDocument()
        if font:
            temp_doc.setDefaultFont(font)

        # Instantiate highlighter first
        highlighter = highlighter_class(temp_doc, theme_colors)

        # Set text second
        temp_doc.setPlainText(text)

        # Force synchronous rehighlighting
        highlighter.rehighlight()

        # Traverse formatting and build HTML using block layout formats
        html_text = ""
        block = temp_doc.begin()
        while block.isValid():
            block_text = block.text()
            layout = block.layout()
            formats = layout.formats()

            char_styles = [None] * len(block_text)

            for fmt_range in formats:
                start = fmt_range.start
                length = fmt_range.length
                fmt = fmt_range.format

                color = fmt.foreground().color()
                hex_color = color.name() if (color.isValid() and color.name() != "#000000") else c_text

                bold = fmt.fontWeight() == 75 or fmt.font().bold()
                italic = fmt.fontItalic()

                style_info = {
                    'color': hex_color,
                    'bold': bold,
                    'italic': italic
                }

                for idx in range(start, min(start + length, len(block_text))):
                    char_styles[idx] = style_info

            # Now build HTML by grouping characters with the same style
            last_style = None
            current_span_text = ""

            for idx, char in enumerate(block_text):
                style = char_styles[idx]
                if style is None:
                    style = {'color': c_text, 'bold': False, 'italic': False}

                if style != last_style:
                    if current_span_text:
                        escaped = html.escape(current_span_text).replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                        style_str = f"color:{last_style['color']};"
                        if last_style['bold']:
                            style_str += "font-weight:bold;"
                        if last_style['italic']:
                            style_str += "font-style:italic;"
                        html_text += f'<span style="{style_str}">{escaped}</span>'
                        current_span_text = ""
                    last_style = style

                current_span_text += char

            if current_span_text:
                escaped = html.escape(current_span_text).replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                style_str = f"color:{last_style['color']};"
                if last_style['bold']:
                    style_str += "font-weight:bold;"
                if last_style['italic']:
                    style_str += "font-style:italic;"
                html_text += f'<span style="{style_str}">{escaped}</span>'

            block = block.next()
            if block.isValid():
                html_text += "<br/>"

        display_name = f'<span style="color:{c_line}">{line}:</span> &nbsp;{html_text}'
    else:
        escaped_text = html.escape(text.strip())
        display_name = f'<span style="color:{c_line}">{line}:</span> &nbsp;<span style="color:{c_text}">{escaped_text}</span>'

    item.setText(display_name)
    item.setIcon(QIcon(icons.get('goto_line', '')))

    return item


class BookmarkWidget(SearchPopupWidget):
    bookmarkSelected = Signal(int)  # Emits selected 1-based line number
    bookmarkDeleted = Signal(int)   # Emits deleted 1-based line number

    def __init__(self, bookmarks, parent=None, center_widget=None, qss=None, font=None, colors=None, highlighter_class=None):
        """
        Constructor for BookmarkWidget.
        bookmarks: list of dicts: [{'line': line_num, 'text': line_text}]
        """
        super(BookmarkWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text="Search bookmark...")

        self.bookmarks = bookmarks
        self.allow_delete = True
        self.highlighter_class = highlighter_class

        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))

        # Calculate dynamic size
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())

        max_text_width = 0
        for b in self.bookmarks:
            label = f"{b['line']}: {b['text'].strip()}"
            w = fm.horizontalAdvance(label) if hasattr(fm, 'horizontalAdvance') else fm.width(label)
            w += 40  # Icon + margin padding
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower()

        for b in self.bookmarks:
            label = f"{b['line']}: {b['text']}"
            if filter_text in label.lower():
                item = create_bookmark_item(b, self.colors, self._font, self.highlighter_class)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_item_clicked(self, item):
        line = item.data(Qt.UserRole)
        self.bookmarkSelected.emit(line)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.allow_delete:
            item = self.list_widget.currentItem()
            if item:
                line = item.data(Qt.UserRole)
                self.bookmarkDeleted.emit(line)
            return
        super(BookmarkWidget, self).keyPressEvent(event)

    def remove_item_by_data(self, data_val):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == data_val:
                self.list_widget.takeItem(i)
                break
        for i, b in enumerate(self.bookmarks):
            if b.get('line') == data_val:
                self.bookmarks.pop(i)
                break
