import re

from vendor.Qt.QtGui import QTextCursor, QTextDocument


class SearchService:
    def __init__(self, editor):
        self.editor = editor
        self._match_cache_key = None
        self._match_cache = None

    def _matches(self, pattern, case_sensitive):
        document = self.editor.document()
        cache_key = (
            pattern,
            case_sensitive,
            document.revision(),
        )
        if cache_key == self._match_cache_key:
            return self._match_cache

        text = self.editor.toPlainText()
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = [
            (match.start(), match.end())
            for match in re.finditer(re.escape(pattern), text, flags=flags)
        ]
        self._match_cache_key = cache_key
        self._match_cache = matches
        return matches

    def select_word(self, pattern, number, replace=None, case_sensitive=False):
        matches = self._matches(pattern, case_sensitive)
        if not matches:
            return number

        if number > len(matches) - 1:
            number = 0

        cursor = self.editor.textCursor()
        cursor.setPosition(matches[number][0])
        cursor.setPosition(matches[number][1], QTextCursor.KeepAnchor)

        if replace is not None:
            cursor.removeSelectedText()
            cursor.insertText(replace)

        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()
        return number

    def replace_all(self, find_text, rep_text, case_sensitive=False):
        if not find_text:
            return

        document = self.editor.document()
        options = (
            QTextDocument.FindCaseSensitively
            if case_sensitive
            else QTextDocument.FindFlags()
        )
        edit_cursor = QTextCursor(document)
        search_cursor = QTextCursor(document)
        last_cursor = None

        edit_cursor.beginEditBlock()
        try:
            while True:
                found_cursor = document.find(
                    find_text,
                    search_cursor,
                    options,
                )
                if found_cursor.isNull():
                    break
                found_cursor.insertText(rep_text)
                search_cursor = found_cursor
                last_cursor = QTextCursor(found_cursor)
        finally:
            edit_cursor.endEditBlock()

        if last_cursor is not None:
            self.editor.setTextCursor(last_cursor)

        self._match_cache_key = None
        self._match_cache = None

        # Trigger autocomplete update if present
        if hasattr(self.editor, 'completer') and self.editor.completer:
            self.editor.completer.updateCompleteList()
