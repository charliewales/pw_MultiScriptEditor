from vendor.Qt.QtWidgets import QListWidgetItem
from vendor.Qt.QtGui import QColor
from vendor.Qt.QtCore import Qt

def create_symbol_item(sym, theme_colors=None, font=None):
    """
    Creates and formats a QListWidgetItem for a given symbol,
    applying appropriate indentation, colors, and fonts.
    """
    name = sym.get('name', '')
    indent = sym.get('indent', 0)
    display_name = ("  " * indent) + name
    
    item = QListWidgetItem(display_name)
    item.setData(Qt.UserRole, sym.get('line', 1))
    
    if font:
        item.setFont(font)

    if sym.get('type') == 'yaml':
        colors = ["#E06C75", "#D19A66", "#E5C07B", "#98C379", "#56B6C2", "#61AFEF", "#C678DD"]
        color = colors[indent % len(colors)]
        item.setForeground(QColor(color))
    else:
        if theme_colors:
            if sym.get('type') == 'class':
                c = theme_colors.get('keywords', (78, 201, 176))
                item.setForeground(QColor(*c))
            elif sym.get('type') == 'usd':
                c = theme_colors.get('methods', (120, 190, 205))
                item.setForeground(QColor(*c))
            else:
                c = theme_colors.get('methods', (220, 220, 170))
                item.setForeground(QColor(*c))
        else:
            if sym.get('type') == 'class':
                item.setForeground(QColor("#4EC9B0"))
            elif sym.get('type') == 'usd':
                item.setForeground(QColor("#78BECD"))
            else:
                item.setForeground(QColor("#DCDCAA"))
                
    return item
