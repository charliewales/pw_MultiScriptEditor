import re
from vendor.Qt.QtGui import QTextCursor, QTextDocument

class SearchService:
    def __init__(self, editor):
        self.editor = editor

    def select_word(self, pattern, number, replace=None, case_sensitive=False):
        text = self.editor.toPlainText()
        flags = 0 if case_sensitive else re.IGNORECASE
        
        indexis = [(m.start(0), m.end(0)) for m in re.finditer(re.escape(pattern), text, flags=flags)]
        if not indexis:
            return number
            
        if number > len(indexis) - 1:
            number = 0
            
        cursor = self.editor.textCursor()
        cursor.setPosition(indexis[number][0])
        cursor.setPosition(indexis[number][1], QTextCursor.KeepAnchor)
        
        if replace is not None:
            cursor.removeSelectedText()
            cursor.insertText(replace)
            
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        return number

    def replace_all(self, find_text, rep_text, case_sensitive=False):
        if not find_text:
            return
            
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        # Start from beginning
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        
        options = QTextDocument.FindCaseSensitively if case_sensitive else QTextDocument.FindFlags()
        
        while self.editor.find(find_text, options):
            self.editor.textCursor().insertText(rep_text)
            
        cursor.endEditBlock()
        
        # Trigger autocomplete update if present
        if hasattr(self.editor, 'completer') and self.editor.completer:
            self.editor.completer.updateCompleteList()
