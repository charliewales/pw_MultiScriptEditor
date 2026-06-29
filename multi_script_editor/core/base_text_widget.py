from vendor.Qt.QtGui import QFont, QTextOption

class BaseTextWidgetMixin:
    """
    Mixin class that provides common text editing functionalities 
    such as font size manipulation, word wrap, and whitespace rendering.
    Expects to be mixed into a QTextEdit or QTextBrowser.
    """
    def changeFontSize(self, up):
        import managers
        if managers.context == 'hou':
            if not hasattr(self, 'fs'):
                self.fs = self.font().pointSize()
            if up:
                self.fs = min(30, self.fs + 1)
            else:
                self.fs = max(8, self.fs - 1)
            self.setTextEditFontSize(self.fs)
        else:
            f = self.font()
            size = f.pointSize()
            if up:
                size = min(30, size + 1)
            else:
                size = max(8, size - 1)
            f.setPointSize(size)
            self.setFont(f)

    def setTextEditFontSize(self, size):
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)
        import managers
        if managers.context == 'hou':
            family = f.family()
            style = self.styleSheet() + '''
            QTextEdit, QTextBrowser {
                font-size: %spx;
                font-family: "%s";
            }''' % (size, family)
            self.setStyleSheet(style)

    def wordWrap(self, state):
        from vendor.Qt.QtWidgets import QTextEdit
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
        family = font_d.get('family', 'Courier')
        pointSize = font_d.get('pointSize', 14)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)
        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        self.setFont(editor_font)
        
        import managers
        if managers.context == 'hou':
            style = self.styleSheet() + '''
            QTextEdit, QTextBrowser {
                font-size: %spx;
                font-family: "%s";
            }''' % (pointSize, family)
            self.setStyleSheet(style)
