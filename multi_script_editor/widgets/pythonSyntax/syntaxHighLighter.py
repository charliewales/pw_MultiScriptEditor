from vendor.Qt.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import re
from widgets.pythonSyntax import design, keywords

class PythonHighlighterClass(QSyntaxHighlighter):
    def __init__(self, document, colors=None):
        if colors:
            self.colors = colors
        else:
            self.colors = design.getColors()

        # Multi line comments
        self.tri_single = (re.compile("'''"), 1, self.getStyle(self.colors['docstring']))
        self.tri_double = (re.compile('"""'), 2, self.getStyle(self.colors['docstring']))

        rules = []
        # Keywords
        keywords_pattern = r'\b(' + '|'.join(keywords.syntax['keywords']) + r')\b'
        rules.append((keywords_pattern, 0, self.getStyle(self.colors['keywords'], True)))

        # Methods
        rules.append((r"\b[A-Za-z0-9_]+(?=\()", 0, self.getStyle(self.colors['methods'], False)))

        # Operators
        rules.append((r'[~!@$%^&*()-+=]', 0, self.getStyle(self.colors['operator'])))

        # Braces
        braces_pattern = r'(' + '|'.join(keywords.syntax['braces']) + r')'
        rules.append((braces_pattern, 0, self.getStyle(self.colors['brace'])))

        # Definition
        definitions_pattern = r'\b(' + '|'.join(keywords.syntax['definition']) + r')\b'
        rules.append((definitions_pattern, 0, self.getStyle(self.colors['definition'], True)))

        # Extra
        extras_pattern = r'\b(' + '|'.join(keywords.syntax['extras']) + r')\b'
        rules.append((extras_pattern, 0, self.getStyle(self.colors['extra'])))

        # Digits
        rules.append((r"\b[\d]+\b", 0, self.getStyle(self.colors['digits'])))

        # Double-quoted string
        rules.append((r'[ru]?"[^"\\]*(\\.[^"\\]*)*"', 0, self.getStyle(self.colors['string'])))

        # Single-quoted string
        rules.append((r"[ru]?'[^'\\]*(\\.[^'\\]*)*'", 0, self.getStyle(self.colors['string'])))

        # Whitespace, \s
        rules.append((r"\s", 0, self.getStyle(self.colors['whitespace'])))

        # Build a compiled regex for each pattern
        self.rules = [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules]
        
        # Cache formats used dynamically in highlightBlock to avoid repeated getStyle calls
        self.default_format = self.getStyle(self.colors['default'])
        self.comment_format = self.getStyle(self.colors['comment'])
        
        # Pre-compile regex for rapid string extraction to safely detect comments
        self.string_pattern = re.compile(r'(".*?"|\'.*?\')')
        
        # Whitespace
        self.whitespace_regex = re.compile(r"\s")
        self.whitespace_format = self.getStyle(self.colors['whitespace'])
        
        QSyntaxHighlighter.__init__(self, document)

    def getStyle(self, color, bold=False):
        brush = QBrush(QColor(*color))
        f = QTextCharFormat()
        if bold:
            f.setFontWeight(QFont.Bold)
        f.setForeground(brush)
        return f

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        self.setFormat(0, len(text), self.default_format)

        # Do other syntax formatting using fast compiled Python regexes
        for expression, nth, format in self.rules:
            for match in expression.finditer(text):
                try:
                    index = match.start(nth)
                    length = match.end(nth) - index
                    if length > 0:
                        self.setFormat(index, length, format)
                except IndexError:
                    pass

        if '#' in text:
            # Safely replace all strings with underscores to avoid matching '#' inside strings
            copy = self.string_pattern.sub(lambda m: '_' * len(m.group(0)), text)
            if '#' in copy:
                index = copy.index('#')
                length = len(copy) - index
                self.setFormat(index, length, self.comment_format)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

        # Re-apply whitespace formatting on top of multiline strings
        for match in self.whitespace_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.whitespace_format)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings."""
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            match = delimiter.search(text)
            start = match.start() if match else -1
            add = match.end() - match.start() if match else 0

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            match = delimiter.search(text, start + add)
            end = match.start() if match else -1
            matchedLength = match.end() - match.start() if match else 0
                
            # Ending delimiter on this line?
            if end >= 0:
                length = end - start + matchedLength
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start
            
            # Apply formatting
            self.setFormat(start, length, style)
            
            # Look for the next match
            match = delimiter.search(text, start + length)
            start = match.start() if match else -1
            add = match.end() - match.start() if match else 0

        # Return True if still inside a multi-line string, False otherwise
        return self.currentBlockState() == in_state
