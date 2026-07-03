from vendor.Qt.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import re
from widgets.pythonSyntax import design

class BaseHighlighterClass(QSyntaxHighlighter):
    def __init__(self, document, colors=None):
        if colors:
            self.colors = colors
        else:
            self.colors = design.getColors()
        
        self.default_format = self.getStyle(self.colors.get('default', (200, 200, 200)))
        
        # We will populate self.rules in subclasses
        self.rules = []
        QSyntaxHighlighter.__init__(self, document)

    def getStyle(self, color, bold=False):
        brush = QBrush(QColor(*color))
        f = QTextCharFormat()
        if bold:
            f.setFontWeight(QFont.Bold)
        f.setForeground(brush)
        return f

    def highlightBlock(self, text):
        self.setFormat(0, len(text), self.default_format)

        for expression, nth, format in self.rules:
            for match in expression.finditer(text):
                try:
                    index = match.start(nth)
                    length = match.end(nth) - index
                    if length > 0:
                        self.setFormat(index, length, format)
                except IndexError:
                    pass

        self.applyExtraHighlighting(text)

    def applyExtraHighlighting(self, text):
        pass


class JavascriptHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(JavascriptHighlighterClass, self).__init__(document, colors)
        rules = []
        
        keywords = ['break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
                    'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
                    'for', 'function', 'if', 'import', 'in', 'instanceof', 'new', 'return',
                    'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void',
                    'while', 'with', 'yield', 'let', 'static', 'enum', 'await', 'async']
        
        rules.append((r'\b(' + '|'.join(keywords) + r')\b', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        rules.append((r'\b(true|false|null|undefined)\b', 0, self.getStyle(self.colors.get('extra', (0,128,255)))))
        rules.append((r"\b[A-Za-z0-9_]+(?=\()", 0, self.getStyle(self.colors.get('methods', (0,255,0)), False)))
        rules.append((r"\b[\d.]+\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        rules.append((r'`.*?`', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        rules.append((r'//.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))

        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]

    def applyExtraHighlighting(self, text):
        pass

class HtmlHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(HtmlHighlighterClass, self).__init__(document, colors)
        rules = []
        
        rules.append((r'<[/]?[A-Za-z0-9_]+', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        rules.append((r'[/]?>', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        rules.append((r'\b[A-Za-z0-9_\-]+(?=\=)', 0, self.getStyle(self.colors.get('methods', (0,255,0)), False)))
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        rules.append((r'<!--.*?-->', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]


class YamlHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(YamlHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Keys
        rules.append((r'^\s*[\w\-]+\s*:', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        # Strings
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        # Booleans and Nulls
        rules.append((r'\b(true|false|null)\b', 0, self.getStyle(self.colors.get('extra', (0,128,255)))))
        # Numbers
        rules.append((r"\b[\d.]+\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        # Comments
        rules.append((r'#.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]


class MarkdownHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(MarkdownHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Headers
        rules.append((r'^#{1,6}\s.*', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        # Bold and Italic
        rules.append((r'(\*\*|__).*?\1', 0, self.getStyle(self.colors.get('methods', (0,255,0)), True)))
        rules.append((r'(\*|_).*?\1', 0, self.getStyle(self.colors.get('extra', (0,128,255)), False)))
        # Links
        rules.append((r'\[.*?\]\(.*?\)', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        # Code blocks
        rules.append((r'`.*?`', 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        # Blockquotes
        rules.append((r'^>.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]


class CssHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(CssHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Selectors
        rules.append((r'^[^\{]+(?=\{)', 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        # Properties
        rules.append((r'\b[a-zA-Z\-]+(?=\s*:)', 0, self.getStyle(self.colors.get('methods', (0,255,0)))))
        # Values (Numbers)
        rules.append((r"\b[\d.]+(px|em|rem|%|vh|vw|s)?\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        # Strings
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        # Hex Colors
        rules.append((r'#[0-9a-fA-F]{3,6}\b', 0, self.getStyle(self.colors.get('extra', (0,128,255)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]

class TextHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(TextHighlighterClass, self).__init__(document, colors)
        self.rules = []
