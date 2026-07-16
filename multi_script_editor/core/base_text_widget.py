from vendor.Qt.QtGui import QFont, QTextOption, QFontDatabase
from vendor.Qt.QtWidgets import QTextEdit, QPlainTextEdit

class BaseTextWidgetMixin:
    """
    Mixin class that provides common text editing functionalities
    such as font size manipulation, word wrap, and whitespace rendering.
    Expects to be mixed into a QTextEdit or QTextBrowser.
    """
    def getFontSize(self):
        if hasattr(self, 'fs') and self.fs > 0:
            return self.fs
        
        size = self.font().pointSize()
        if size > 0:
            return size
            
        return 10 # Safe fallback

    def setFontSize(self, size):
        if size >= 8: # Assuming minimumFontSize is around 8-10.
            self.fs = size
            self.setTextEditFontSize(self.fs)

    def changeFontSize(self, up):
        size = self.getFontSize()
            
        if up:
            size = min(30, size + 1)
        else:
            size = max(8, size - 1)
            
        self.setFontSize(size)

    def setTextEditFontSize(self, size):
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)

    def wordWrap(self, state):
        if isinstance(self, QPlainTextEdit):
            if state:
                self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            else:
                self.setLineWrapMode(QPlainTextEdit.NoWrap)
        else:
            if state:
                self.setLineWrapMode(QTextEdit.WidgetWidth)
            else:
                self.setLineWrapMode(QTextEdit.NoWrap)

    def set_font(self, font):
        self.setFont(font)

    def render_whitespace(self, state):
        text_option = self.document().defaultTextOption()
        if state:
            text_option.setFlags(text_option.flags() | QTextOption.ShowTabsAndSpaces)
        else:
            text_option.setFlags(text_option.flags() & ~QTextOption.ShowTabsAndSpaces)
        self.document().setDefaultTextOption(text_option)

    def set_start_font(self, font_d=None):
        if not font_d:
            return
        family = font_d.get('family', 'monospace')
        pointSize = font_d.get('pointSize', 14)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)

        # Cross-compatibility patch for PySide2 (NF) vs PySide6 (Nerd Font)
        try:
            families = QFontDatabase.families()
        except TypeError:
            db = QFontDatabase()
            families = db.families()

        if family not in families:
            variations = [
                family.replace(" NFM", " Nerd Font Mono"),
                family.replace(" Nerd Font Mono", " NFM"),
                family.replace(" NFP", " Nerd Font Propo"),
                family.replace(" Nerd Font Propo", " NFP"),
                family.replace(" NF", " Nerd Font"),
                family.replace(" Nerd Font", " NF"),
                family.replace(" Nerd Font Mono", " Nerd Font"),
                family.replace(" Nerd Font Propo", " Nerd Font"),
                family.replace(" Nerd Font", " Nerd Font Mono"),
                family.replace(" Nerd Font", " Nerd Font Propo")
            ]
            for alt in variations:
                if alt in families:
                    family = alt
                    break

        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        self.setFont(editor_font)
        if hasattr(self, 'fs'):
            self.fs = pointSize
        
        if hasattr(self, 'completer') and self.completer:
            self.completer.setFont(editor_font)
            if hasattr(self.completer, 'doc_tooltip') and self.completer.doc_tooltip:
                self.completer.doc_tooltip.setFont(editor_font)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        main_win = self.window()
        if hasattr(main_win, 'menubar'):
            menu.setFont(main_win.menubar.font())
            menu.setStyleSheet(main_win.menubar.styleSheet())
        menu.exec_(event.globalPos())
        del menu
