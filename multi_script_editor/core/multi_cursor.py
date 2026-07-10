from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QTextCursor, QColor
from vendor.Qt.QtWidgets import QTextEdit

class MultiCursorManager:
    def __init__(self, editor):
        self.editor = editor
        self.multi_cursors = []
        self.is_auto_populated = False

    def clear(self):
        self.multi_cursors = []
        self.is_auto_populated = False
        if hasattr(self.editor, 'messageSignal'):
            self.editor.messageSignal.emit("")

    def has_cursors(self):
        return len(self.multi_cursors) > 0

    def add_cursor_at(self, cursor):
        """Adds a copy of the given cursor to the multi-cursors list."""
        if not self.multi_cursors:
            # If this is the first additional cursor, we must also store the main cursor's current state
            # but wait, the main cursor is added initially elsewhere or implicitly.
            # Usually, when Ctrl+Clicking, we add the current cursor to the list first if it's empty
            current = self.editor.textCursor()
            self.multi_cursors.append(QTextCursor(current))

        c = QTextCursor(cursor)
        self.multi_cursors.append(c)
        self.deduplicate_and_sort_cursors()

    def deduplicate_and_sort_cursors(self):
        if not self.multi_cursors:
            return
        seen = set()
        unique_cursors = []
        sorted_c = sorted(self.multi_cursors, key=lambda c: (c.position(), c.anchor()))
        for c in sorted_c:
            key = (c.position(), c.anchor())
            if key not in seen:
                seen.add(key)
                unique_cursors.append(c)
        self.multi_cursors = unique_cursors

    def get_extra_selections(self):
        selections = []
        for mc in self.multi_cursors:
            sel = QTextEdit.ExtraSelection()
            if mc.hasSelection():
                sel.cursor = mc
                sel.format.setBackground(QColor(40, 100, 200, 120))
            else:
                c_copy = QTextCursor(mc)
                if not c_copy.atEnd():
                    c_copy.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                    sel.cursor = c_copy
                    sel.format.setBackground(QColor(128, 128, 255, 180))
                else:
                    sel.cursor = c_copy
                    sel.format.setBackground(QColor(128, 128, 255, 180))
            selections.append(sel)
        return selections

    def handle_key_press(self, event):
        if not self.multi_cursors:
            return False

        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            self.clear()
            self.editor.highlight_current_line()
            return True

        if key == Qt.Key_A and (modifiers & Qt.ControlModifier):
            self.clear()
            self.editor.highlight_current_line()
            return False

        if getattr(self, 'is_auto_populated', False):
            self.clear()
            self.editor.highlight_current_line()
            return False

        nav_ops = {
            Qt.Key_Left: QTextCursor.Left,
            Qt.Key_Right: QTextCursor.Right,
            Qt.Key_Up: QTextCursor.Up,
            Qt.Key_Down: QTextCursor.Down,
            Qt.Key_Home: QTextCursor.StartOfLine,
            Qt.Key_End: QTextCursor.EndOfLine,
        }

        if key in nav_ops:
            op = nav_ops[key]
            mode = QTextCursor.KeepAnchor if (modifiers & Qt.ShiftModifier) else QTextCursor.MoveAnchor

            if key == Qt.Key_Left and (modifiers & Qt.ControlModifier):
                op = QTextCursor.WordLeft
            elif key == Qt.Key_Right and (modifiers & Qt.ControlModifier):
                op = QTextCursor.WordRight

            for cursor in self.multi_cursors:
                cursor.movePosition(op, mode)

            self.deduplicate_and_sort_cursors()

            if self.multi_cursors:
                if hasattr(self.editor, '_is_auto_selecting'):
                    self.editor._is_auto_selecting = True
                self.editor.setTextCursor(self.multi_cursors[0])
                if hasattr(self.editor, '_is_auto_selecting'):
                    self.editor._is_auto_selecting = False
            self.editor.highlight_current_line()
            return True

        is_edit = False
        text = event.text()

        sorted_cursors = sorted(self.multi_cursors, key=lambda c: c.position(), reverse=True)

        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = True

        main_cursor = self.editor.textCursor()
        main_cursor.beginEditBlock()
        try:
            if key == Qt.Key_Backspace:
                is_edit = True
                for cursor in sorted_cursors:
                    cursor.deletePreviousChar()
            elif key == Qt.Key_Delete:
                is_edit = True
                for cursor in sorted_cursors:
                    cursor.deleteChar()
            elif key in [Qt.Key_Return, Qt.Key_Enter]:
                is_edit = True
                for cursor in sorted_cursors:
                    cursor.insertText("\n")
            elif key == Qt.Key_Tab:
                is_edit = True
                for cursor in sorted_cursors:
                    cursor.insertText("    ")
            elif text and text.isprintable():
                is_edit = True
                for cursor in sorted_cursors:
                    cursor.insertText(text)
        finally:
            main_cursor.endEditBlock()

        if is_edit:
            self.deduplicate_and_sort_cursors()
            if self.multi_cursors:
                if hasattr(self.editor, '_is_auto_selecting'):
                    self.editor._is_auto_selecting = True
                self.editor.setTextCursor(self.multi_cursors[0])
                if hasattr(self.editor, '_is_auto_selecting'):
                    self.editor._is_auto_selecting = False
            self.editor.highlight_current_line()

        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = False

        if is_edit:
            return True

        return False

    def select_next_occurrence(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.editor.setTextCursor(cursor)

        if not cursor.hasSelection():
            return

        target_text = cursor.selectedText()
        if not target_text:
            return

        if getattr(self, 'is_auto_populated', False):
            self.clear()
            self.is_auto_populated = False

        if not self.multi_cursors:
            self.multi_cursors = [cursor]

        last_cursor = self.multi_cursors[-1]
        start_pos = last_cursor.position()
        found_cursor = self.editor.document().find(target_text, start_pos)

        if found_cursor.isNull() or found_cursor.position() <= start_pos:
            found_cursor = self.editor.document().find(target_text, 0)

        if not found_cursor.isNull():
            already_selected = False
            for mc in self.multi_cursors:
                if mc.selectionStart() == found_cursor.selectionStart() and mc.selectionEnd() == found_cursor.selectionEnd():
                    already_selected = True
                    break

            if not already_selected:
                self.multi_cursors.append(found_cursor)
                self.editor.setTextCursor(found_cursor)

        self.editor.highlight_current_line()
        if hasattr(self.editor, 'messageSignal'):
            count = len(self.multi_cursors) if self.multi_cursors else 1
            self.editor.messageSignal.emit(f"{count} occurrences selected")

    def select_all_occurrences(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.editor.setTextCursor(cursor)

        if not cursor.hasSelection():
            return

        target_text = cursor.selectedText()
        if not target_text:
            return

        self.clear()
        self.is_auto_populated = getattr(self.editor, '_is_auto_selecting', False)
        start_pos = 0
        while True:
            found_cursor = self.editor.document().find(target_text, start_pos)
            if found_cursor.isNull() or found_cursor.position() <= start_pos:
                break
            self.multi_cursors.append(found_cursor)
            start_pos = found_cursor.position()

        self.editor.highlight_current_line()
        if hasattr(self.editor, 'messageSignal'):
            count = len(self.multi_cursors) if self.multi_cursors else 1
            if getattr(self, 'is_auto_populated', False):
                self.editor.messageSignal.emit(f"{count} occurrences")
            else:
                self.editor.messageSignal.emit(f"{count} occurrences selected")
