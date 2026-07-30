from icons import icons
from vendor.Qt.QtCore import QRectF, QSize, Qt
from vendor.Qt.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QTextDocument
from vendor.Qt.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QTreeWidgetItem,
)


_SYMBOL_ICON_KEYS = {
    'class': 'sym_class',
    'method': 'sym_method',
    'function': 'sym_function',
    'variable': 'sym_variable',
    'constant': 'sym_constant',
    'yaml': 'sym_yaml',
    'json': 'sym_json',
    'usd': 'sym_usd',
    'xml': 'sym_xml',
    'ini_section': 'sym_ini_section',
    'ini_key': 'sym_ini_key',
}
_symbol_type_icon_cache = {}


def rgb_to_hex(rgb, default="#ffffff"):
    if not isinstance(rgb, (list, tuple)) or len(rgb) < 3:
        return default
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def color_to_str(color_val, default="#d4d4d4"):
    if not color_val:
        return default
    if isinstance(color_val, (list, tuple)) and len(color_val) >= 3:
        return rgb_to_hex(color_val, default)
    if hasattr(color_val, "name"):
        return color_val.name()
    return str(color_val)


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


def get_symbol_type_icon(sym_type, theme_colors=None):
    """
    Returns a cached QIcon representing the symbol type.
    """
    cache_key = sym_type or 'symbol'
    cached_icon = _symbol_type_icon_cache.get(cache_key)
    if cached_icon is not None:
        return cached_icon

    icon_key = _SYMBOL_ICON_KEYS.get(sym_type)
    icon_path = icons.get(icon_key) if icon_key else None
    if icon_path:
        icon = QIcon(icon_path)
        if not icon.isNull():
            _symbol_type_icon_cache[cache_key] = icon
            return icon

    size = 20
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    # Color map per symbol type
    color_map = {
        'class': QColor(160, 110, 220),       # Purple / Violet
        'method': QColor(80, 180, 220),       # Cyan / Blue
        'function': QColor(70, 200, 120),     # Green
        'variable': QColor(230, 160, 60),     # Orange
        'constant': QColor(220, 80, 100),     # Red / Magenta
        'yaml': QColor(210, 170, 70),
        'json': QColor(210, 170, 70),
        'usd': QColor(100, 170, 220),
        'xml': QColor(180, 120, 200),
        'ini_section': QColor(160, 110, 220),
        'ini_key': QColor(80, 180, 220),
    }
    bg_color = color_map.get(sym_type, QColor(130, 140, 150))

    # Draw rounded circle or rounded rect with good padding
    painter.setBrush(bg_color)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(1, 1, 18, 18, 5, 5)

    # Draw letter label inside badge
    label_map = {
        'class': 'C',
        'method': 'M',
        'function': 'F',
        'variable': 'V',
        'constant': 'K',
        'yaml': 'Y',
        'json': 'J',
        'usd': 'U',
        'xml': 'X',
        'ini_section': 'S',
        'ini_key': 'k',
    }
    letter = label_map.get(sym_type, 'S')

    font = QFont("Segoe UI", 9, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    # Apply -1px vertical offset so uppercase letters are optically centered inside the badge
    text_rect = QRectF(0, -1.5, size, size)
    painter.drawText(text_rect, Qt.AlignCenter, letter)
    painter.end()

    icon = QIcon(pix)
    _symbol_type_icon_cache[cache_key] = icon
    return icon


def format_html_symbol_name(name, sym_type, theme_colors=None, ext='.py'):
    """
    Formats the html string for symbol display based on syntax highlighting colors.
    Removes redundant 'class', 'def', and 'async def' prefixes since the icon badge indicates symbol type.
    """
    if not theme_colors:
        theme_colors = {}

    c_def = rgb_to_hex(theme_colors.get('definition', (255, 160, 250)))
    c_meth = rgb_to_hex(theme_colors.get('methods', (120, 190, 205)))
    c_kw = rgb_to_hex(theme_colors.get('keywords', (65, 255, 130)))
    c_str = rgb_to_hex(theme_colors.get('string', (128, 255, 128)))
    c_text = rgb_to_hex(theme_colors.get("tab_selected_text", (200, 200, 200)))
    c_num = rgb_to_hex(theme_colors.get("numbers", (220, 140, 100)))

    # Strip prefixes like class, async def, def, etc.
    clean_name = name
    for prefix in ['class ', 'async def ', 'def ', 'function ', 'struct ', 'enum ']:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
            break

    # Strip trailing '=' or ' =' from variable and constant symbol names
    if clean_name.endswith('='):
        clean_name = clean_name.rstrip('=').rstrip()

    if sym_type == 'constant':
        return f'<span style="color:{c_num}">{clean_name}</span>'
    elif sym_type == 'variable':
        return f'<span style="color:{c_text}">{clean_name}</span>'
    elif sym_type == 'class':
        return f'<span style="color:{c_def}">{clean_name}</span>'
    elif sym_type in ['method', 'function']:
        return f'<span style="color:{c_meth}">{clean_name}</span>'

    if ext in ['.usd', '.usda']:
        parts = clean_name.split(' ', 2)
        if len(parts) >= 2:
            kw = parts[0]
            node_type = parts[1]
            rest = parts[2] if len(parts) > 2 else ''
            return f'<span style="color:{c_kw}">{kw}</span> <span style="color:{c_meth}">{node_type}</span> <span style="color:{c_str}">{rest}</span>'
    elif ext in ['.yaml', '.yml', '.json']:
        return f'<span style="color:{c_kw}">{clean_name}</span>'
    elif ext in ['.html', '.htm']:
        parts = clean_name.split(' ', 1)
        if len(parts) == 2:
            p0 = parts[0].replace('<', '&lt;').replace('>', '&gt;')
            return f'<span style="color:{c_kw}">{p0}</span> <span style="color:{c_meth}">{parts[1]}</span>'
    elif ext == '.xml':
        escaped = clean_name.replace('<', '&lt;').replace('>', '&gt;')
        return f'<span style="color:{c_kw}">{escaped}</span>'
    elif ext == '.ini':
        if sym_type == 'ini_section':
            return f'<span style="color:{c_kw}">{clean_name}</span>'
        else:
            return f'<span style="color:{c_meth}">{clean_name}</span>'
    elif ext in ['.css', '.scss', '.less']:
        return f'<span style="color:{c_kw}">{clean_name}</span>'
    elif ext in ['.md', '.markdown', '.generic']:
        return f'<span style="color:{c_text}">{clean_name}</span>'

    return f'<span style="color:{c_text}">{clean_name}</span>'


def create_symbol_item(sym, theme_colors=None, font=None, ext='.py'):
    """
    Creates and formats a QListWidgetItem for a given symbol.
    """
    name = sym.get('name', '')
    indent = sym.get('indent', 0)
    sym_type = sym.get('type', 'function')

    item = QListWidgetItem()
    item.setData(Qt.UserRole, sym.get('line', 1))

    if font:
        item.setFont(font)

    html_name = format_html_symbol_name(name, sym_type, theme_colors, ext=ext)
    display_name = ("&nbsp;&nbsp;" * indent) + html_name
    item.setText(display_name)

    if 'icon' in sym:
        icon = sym['icon']
        if isinstance(icon, QIcon):
            item.setIcon(icon)
        else:
            item.setIcon(QIcon(icon))
    else:
        item.setIcon(get_symbol_type_icon(sym_type, theme_colors))

    return item


def create_tree_symbol_item(sym, theme_colors=None, font=None, ext='.py'):
    """
    Creates and formats a QTreeWidgetItem for a given symbol in the tree Outline panel.
    """
    name = sym.get('name', '')
    sym_type = sym.get('type', 'function')

    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, sym.get('line', 1))
    item.setData(0, Qt.UserRole + 1, sym_type)
    item.setData(0, Qt.UserRole + 2, sym)

    if font:
        item.setFont(0, font)

    html_name = format_html_symbol_name(name, sym_type, theme_colors, ext=ext)
    item.setText(0, html_name)

    if 'icon' in sym:
        icon = sym['icon']
        if isinstance(icon, QIcon):
            item.setIcon(0, icon)
        else:
            item.setIcon(0, QIcon(icon))
    else:
        item.setIcon(0, get_symbol_type_icon(sym_type, theme_colors))

    return item
