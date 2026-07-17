from vendor.Qt.QtWidgets import QListWidgetItem, QStyledItemDelegate, QApplication, QStyle
from vendor.Qt.QtGui import QTextDocument
from vendor.Qt.QtCore import Qt, QSize, QRectF

class HtmlDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = option
        self.initStyleOption(options, index)

        painter.save()

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setDefaultFont(options.font)

        # Clear text to prevent default painting
        options.text = ""

        style = options.widget.style() if options.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter, options.widget)

        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options, options.widget)
        # Translate to the correct text rectangle so it respects the icon offset
        painter.translate(textRect.left(), textRect.top())
        clip = QRectF(0, 0, textRect.width(), textRect.height())
        doc.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index):
        options = option
        self.initStyleOption(options, index)
        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setDefaultFont(options.font)
        
        base_size = super(HtmlDelegate, self).sizeHint(option, index)
        width = int(doc.idealWidth()) + 4 # base margin
        height = int(doc.size().height())
        
        if not options.icon.isNull():
            icon_size = options.icon.actualSize(options.decorationSize)
            width += icon_size.width() + 8 # margin
            height = max(height, icon_size.height() + 4)
            
        return QSize(width, max(base_size.height(), height))

def create_symbol_item(sym, theme_colors=None, font=None, ext='.py'):
    """
    Creates and formats a QListWidgetItem for a given symbol,
    applying appropriate indentation, colors, and fonts based on file extension.
    Uses HTML for multi-color support inside the item.
    """
    name = sym.get('name', '')
    indent = sym.get('indent', 0)

    item = QListWidgetItem()
    item.setData(Qt.UserRole, sym.get('line', 1))

    if font:
        item.setFont(font)

    if not theme_colors:
        theme_colors = {}

    sym_type = sym.get('type')

    def rgb2hex(rgb):
        if not isinstance(rgb, (list, tuple)) or len(rgb) < 3:
            return "#ffffff"
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

    c_def = rgb2hex(theme_colors.get('definition', (255, 160, 250)))
    c_meth = rgb2hex(theme_colors.get('methods', (120, 190, 205)))
    c_kw = rgb2hex(theme_colors.get('keywords', (65, 255, 130)))
    c_str = rgb2hex(theme_colors.get('string', (128, 255, 128)))
    c_text = rgb2hex(theme_colors.get("tab_selected_text", (128, 255, 128)))

    html_name = name

    if ext in ['.usd', '.usda']:
        parts = name.split(' ', 2)
        if len(parts) >= 2:
            kw = parts[0]
            node_type = parts[1]
            rest = parts[2] if len(parts) > 2 else ''
            html_name = f'<span style="color:{c_kw}">{kw}</span> <span style="color:{c_meth}">{node_type}</span> <span style="color:{c_str}">{rest}</span>'
    elif ext in ['.yaml', '.yml']:
        html_name = f'<span style="color:{c_kw}">{name}</span>'
    elif ext == '.json':
        html_name = f'<span style="color:{c_kw}">{name}</span>'
    elif ext in ['.html', '.htm']:
        parts = name.split(' ', 1)
        if len(parts) == 2:
            html_name = f'<span style="color:{c_kw}">{parts[0]}</span> <span style="color:{c_meth}">{parts[1]}</span>'
    elif ext in ['.css', '.scss', '.less']:
        html_name = f'<span style="color:{c_kw}">{name}</span>'
    elif ext in ['.md', '.markdown', '.generic']:
        html_name = f'<span style="color:{c_text}">{name}</span>'
    else:
        # Programming languages (Python, JS, C++, etc)
        first_space = name.find(' ')
        if first_space != -1:
            kw = name[:first_space]
            rest = name[first_space+1:]

            # Python 'class' and 'def' use definition color in editor
            if ext == '.py' and kw in ['def', 'class']:
                kw_html = f'<span style="color:{c_def}">{kw}</span>'
            else:
                kw_html = f'<span style="color:{c_kw}">{kw}</span>'

            # Class and function names are colored using methods color
            rest_html = f'<span style="color:{c_meth}">{rest}</span>'

            html_name = f'{kw_html} {rest_html}'
        else:
            html_name = f'<span style="color:{c_text}">{name}</span>'

    # Add HTML non-breaking spaces for indentation
    display_name = ("&nbsp;&nbsp;" * indent) + html_name
    item.setText(display_name)

    if 'icon' in sym:
        from vendor.Qt.QtGui import QIcon
        icon = sym['icon']
        if isinstance(icon, QIcon):
            item.setIcon(icon)
        else:
            item.setIcon(QIcon(icon))

    return item
