import re

from vendor.Qt.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from widgets.pythonSyntax import design


class BaseHighlighterClass(QSyntaxHighlighter):
    def __init__(self, document, colors=None):
        if colors:
            self.colors = colors
        else:
            self.colors = design.getColors()
        
        self.default_format = self.getStyle(self.colors.get('default', (200, 200, 200)))
        self.whitespace_format = self.getStyle(self.colors.get('whitespace', (100, 100, 100)))
        self.whitespace_regex = re.compile(r"\s")
        
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

        if hasattr(self, 'whitespace_regex'):
            for match in self.whitespace_regex.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.whitespace_format)

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
        rules.append((r'^\s*([\w\-]+\s*:)', 1, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        # Strings
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        # Booleans and Nulls
        rules.append((r'\b(true|false|null)\b', 0, self.getStyle(self.colors.get('extra', (0,128,255)))))
        # Numbers
        rules.append((r"\b[\d.]+\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        # Comments
        rules.append((r'#.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]


class UsdHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(UsdHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Multiline strings """
        self.tri_double = (re.compile('"""'), 2, self.getStyle(self.colors.get('string', (128,255,128))))
        
        # Keywords
        usd_keywords = ['def', 'class', 'over', 'rel', 'custom', 'uniform', 'variantSet', 'asset', 'token', 'int', 'float', 'double', 'string', 'bool', 'matrix4d', 'double3', 'float3', 'color3f', 'quatf', 'timecode', 'dictionary', 'references', 'payload', 'inherits', 'specializes', 'subLayers', 'upAxis', 'metersPerUnit', 'defaultPrim', 'doc', 'config']
        keywords_pattern = r'\b(' + '|'.join(usd_keywords) + r')\b'
        rules.append((keywords_pattern, 0, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        
        # Node Types (after def, class, over)
        rules.append((r'\b(?:def|class|over)\s+([A-Za-z0-9_]+)', 1, self.getStyle(self.colors.get('methods', (0,255,0)))))
        
        # Strings
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        
        # Numbers
        rules.append((r"\b[-+]?[\d.]+\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        
        # Comments
        rules.append((r'#.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        super(UsdHighlighterClass, self).highlightBlock(text)
        
        self.setCurrentBlockState(0)
        self.match_multiline(text, *self.tri_double)

        if hasattr(self, 'whitespace_regex'):
            for match in self.whitespace_regex.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.whitespace_format)

    def match_multiline(self, text, delimiter, in_state, style):
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            match = delimiter.search(text)
            start = match.start() if match else -1
            add = match.end() - match.start() if match else 0

        while start >= 0:
            match = delimiter.search(text, start + add)
            end = match.start() if match else -1
            matchedLength = match.end() - match.start() if match else 0
                
            if end >= 0:
                length = end - start + matchedLength
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start
            
            self.setFormat(start, length, style)
            
            match = delimiter.search(text, start + length)
            start = match.start() if match else -1
            add = match.end() - match.start() if match else 0

        return self.currentBlockState() == in_state



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
        rules.append((r'^\s*([^\{]+?)(?=\{)', 1, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
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

class LogHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(LogHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Log Levels
        rules.append((r'\b(ERROR|CRITICAL|FATAL|Exception|Failed)\b', 0, self.getStyle(self.colors.get('error', (255, 80, 80)), True)))
        rules.append((r'\b(WARNING|WARN)\b', 0, self.getStyle(self.colors.get('warning', (255, 165, 0)), True)))
        rules.append((r'\b(INFO|DEBUG|TRACE)\b', 0, self.getStyle(self.colors.get('info', (0, 200, 255)), False)))
        
        # Dates and Times
        rules.append((r'\b\d{4}[-/]\d{2}[-/]\d{2}\b', 0, self.getStyle(self.colors.get('digits', (255, 255, 0)))))
        rules.append((r'\b\d{2}:\d{2}:\d{2}(?:[,.]\d{3})?\b', 0, self.getStyle(self.colors.get('digits', (255, 255, 0)))))
        
        # Strings and paths
        rules.append((r'".*?"|\'.*?\'', 0, self.getStyle(self.colors.get('string', (128, 255, 128)))))
        
        # Numbers
        rules.append((r"\b\d+\b", 0, self.getStyle(self.colors.get('digits', (255, 255, 0)))))
        
        self.rules = [(re.compile(pat, re.IGNORECASE), index, fmt) for (pat, index, fmt) in rules]


class JsonHighlighterClass(BaseHighlighterClass):
    def __init__(self, document, colors=None):
        super(JsonHighlighterClass, self).__init__(document, colors)
        rules = []
        
        # Strings (put first so they get overwritten by Keys if they match)
        rules.append((r'"[^"\\]*(?:\\.[^"\\]*)*"', 0, self.getStyle(self.colors.get('string', (128,255,128)))))
        # Keys (strings before colon)
        rules.append((r'("[^"\\]*(?:\\.[^"\\]*)*")\s*:', 1, self.getStyle(self.colors.get('keywords', (255,128,0)), True)))
        # Booleans and Nulls
        rules.append((r'\b(true|false|null)\b', 0, self.getStyle(self.colors.get('extra', (0,128,255)))))
        # Numbers
        rules.append((r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b", 0, self.getStyle(self.colors.get('digits', (255,255,0)))))
        # Comments (put last so they override any string/key/number formatting)
        rules.append((r'//.*', 0, self.getStyle(self.colors.get('comment', (128,128,128)))))
        
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]

