from vendor.Qt.QtWidgets import QListWidgetItem
from vendor.Qt.QtGui import QColor
from vendor.Qt.QtCore import Qt

def create_symbol_item(sym, theme_colors=None, font=None, ext='.py'):
    """
    Creates and formats a QListWidgetItem for a given symbol,
    applying appropriate indentation, colors, and fonts based on file extension.
    """
    name = sym.get('name', '')
    indent = sym.get('indent', 0)
    display_name = ("  " * indent) + name
    
    item = QListWidgetItem(display_name)
    item.setData(Qt.UserRole, sym.get('line', 1))
    
    if font:
        item.setFont(font)

    if not theme_colors:
        theme_colors = {}
        
    sym_type = sym.get('type')
    
    c_def = theme_colors.get('definition', (255, 160, 250))
    c_meth = theme_colors.get('methods', (120, 190, 205))
    c_kw = theme_colors.get('keywords', (65, 255, 130))
    
    if ext == '.py':
        if sym_type == 'class':
            item.setForeground(QColor(*c_def))
        else:
            item.setForeground(QColor(*c_meth))
            
    elif ext in ['.js', '.jsx', '.ts', '.tsx', '.cpp', '.c', '.h', '.hpp', '.vex', '.mel']:
        if sym_type == 'class':
            item.setForeground(QColor(*c_kw))
        else:
            item.setForeground(QColor(*c_meth))
            
    elif ext in ['.usd', '.usda']:
        item.setForeground(QColor(*c_meth))
        
    else:
        # Markdown headers, HTML tags, CSS selectors, YAML keys all use keywords color in extraSyntaxes
        item.setForeground(QColor(*c_kw))

    return item
