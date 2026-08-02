from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QColor, QTextCursor, QTextDocument
from vendor.Qt.QtWidgets import QTextEdit


class MultiCursorManager:
    def __init__(self, editor):
        self.editor = editor
        self.multi_cursors = []
        self.is_auto_populated = False
        self._occurrence_cache_key = None
        self._extra_selections_cache = None

    def clear(self):
        self.multi_cursors = []
        self.is_auto_populated = False
        self._occurrence_cache_key = None
        self._extra_selections_cache = None
        if hasattr(self.editor, 'messageSignal'):
            self.editor.messageSignal.emit("")

    def has_cursors(self):
        return len(self.multi_cursors) > 0

    def _occurrences_case_sensitive(self):
        action = getattr(
            getattr(self.editor, 'p', None),
            'occurrencesCaseSensitive_act',
            None,
        )
        if action is not None:
            return action.isChecked()
        try:
            from core.settings_model import SettingsModel
            data = SettingsModel().read_settings() or {}
            return data.get('occurrences_case_sensitive', False)
        except ImportError:
            return False

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
            self._extra_selections_cache = None
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
        self._extra_selections_cache = None

    def get_extra_selections(self):
        if self._extra_selections_cache is not None:
            return self._extra_selections_cache

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
        self._extra_selections_cache = selections
        return selections

    def handle_key_press(self, event):
        if not self.multi_cursors:
            return False

        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return False

        if (
            modifiers == Qt.AltModifier
            and key in (Qt.Key_C, Qt.Key_Up, Qt.Key_Down)
        ):
            return False

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
            self._extra_selections_cache = None

        last_cursor = self.multi_cursors[-1]
        start_pos = last_cursor.position()
        case_sensitive = self._occurrences_case_sensitive()

        options = QTextDocument.FindCaseSensitively if case_sensitive else QTextDocument.FindFlags()

        found_cursor = self.editor.document().find(target_text, start_pos, options)

        if found_cursor.isNull() or found_cursor.position() <= start_pos:
            found_cursor = self.editor.document().find(target_text, 0, options)

        if not found_cursor.isNull():
            already_selected = False
            for mc in self.multi_cursors:
                if mc.selectionStart() == found_cursor.selectionStart() and mc.selectionEnd() == found_cursor.selectionEnd():
                    already_selected = True
                    break

            if not already_selected:
                self.multi_cursors.append(found_cursor)
                self._extra_selections_cache = None
                self.editor.setTextCursor(found_cursor)
                self.editor.ensureCursorVisible()

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

        document = self.editor.document()
        is_auto_populated = getattr(
            self.editor,
            '_is_auto_selecting',
            False,
        )
        case_sensitive = self._occurrences_case_sensitive()
        cache_key = (
            target_text,
            document.revision(),
            case_sensitive,
            is_auto_populated,
        )
        if cache_key == self._occurrence_cache_key:
            return

        self.clear()
        self.is_auto_populated = is_auto_populated

        options = QTextDocument.FindCaseSensitively if case_sensitive else QTextDocument.FindFlags()

        start_pos = 0
        while True:
            found_cursor = document.find(target_text, start_pos, options)
            if found_cursor.isNull() or found_cursor.position() <= start_pos:
                break
            self.multi_cursors.append(found_cursor)
            start_pos = found_cursor.position()

        self._occurrence_cache_key = cache_key
        self.editor.highlight_current_line()
        if hasattr(self.editor, 'messageSignal'):
            count = len(self.multi_cursors) if self.multi_cursors else 1
            if getattr(self, 'is_auto_populated', False):
                self.editor.messageSignal.emit(f"{count} occurrences")
            else:
                self.editor.messageSignal.emit(f"{count} occurrences selected")

    def next_selection(self):
        if not self.multi_cursors:
            return
        
        main_cursor = self.editor.textCursor()
        current_idx = -1
        for i, mc in enumerate(self.multi_cursors):
            if mc.position() == main_cursor.position() and mc.anchor() == main_cursor.anchor():
                current_idx = i
                break
        
        if current_idx == -1:
            # If main cursor is not in the list, just go to the first one
            next_idx = 0
        else:
            next_idx = (current_idx + 1) % len(self.multi_cursors)
            
        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = True
        self.editor.setTextCursor(self.multi_cursors[next_idx])
        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = False
        self.editor.highlight_current_line()
        self._center_cursor_in_editor()

    def previous_selection(self):
        if not self.multi_cursors:
            return
            
        main_cursor = self.editor.textCursor()
        current_idx = -1
        for i, mc in enumerate(self.multi_cursors):
            if mc.position() == main_cursor.position() and mc.anchor() == main_cursor.anchor():
                current_idx = i
                break
        
        if current_idx == -1:
            prev_idx = len(self.multi_cursors) - 1
        else:
            prev_idx = (current_idx - 1) % len(self.multi_cursors)
            
        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = True
        self.editor.setTextCursor(self.multi_cursors[prev_idx])
        if hasattr(self.editor, '_is_auto_selecting'):
            self.editor._is_auto_selecting = False
        self.editor.highlight_current_line()
        self._center_cursor_in_editor()

    def _center_cursor_in_editor(self):
        self.editor.ensureCursorVisible()

    def add_cursors_to_line_ends(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            # If no selection, place cursor at the end of the current line
            c = QTextCursor(cursor)
            c.movePosition(QTextCursor.EndOfBlock)
            self.clear()
            self.multi_cursors = [c]
            self.editor.setTextCursor(c)
            self.editor.highlight_current_line()
            return

        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()

        doc = self.editor.document()
        start_block = doc.findBlock(start_pos)
        end_block = doc.findBlock(end_pos)

        # If selection ends at the start of a block, exclude it if it is not the only block
        if end_pos == end_block.position() and end_block != start_block:
            end_block = end_block.previous()

        self.clear()

        # Iterate through all blocks in the selection and add a cursor at the end of each block
        block = start_block
        while block.isValid():
            c = QTextCursor(block)
            c.movePosition(QTextCursor.EndOfBlock)
            self.multi_cursors.append(c)
            if block == end_block:
                break
            block = block.next()

        self.deduplicate_and_sort_cursors()

        if self.multi_cursors:
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = True
            self.editor.setTextCursor(self.multi_cursors[-1])
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = False

        self.editor.highlight_current_line()

    def add_cursor_above(self):
        if not self.multi_cursors:
            cursor = self.editor.textCursor()
            self.multi_cursors.append(QTextCursor(cursor))
            self._extra_selections_cache = None

        top_cursor = min(self.multi_cursors, key=lambda c: c.blockNumber())
        new_cursor = QTextCursor(top_cursor)
        
        moved = new_cursor.movePosition(QTextCursor.Up)

        if moved and new_cursor.blockNumber() < top_cursor.blockNumber():
            self.add_cursor_at(new_cursor)
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = True
            self.editor.setTextCursor(new_cursor)
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = False
            self.editor.highlight_current_line()

    def add_cursor_below(self):
        if not self.multi_cursors:
            cursor = self.editor.textCursor()
            self.multi_cursors.append(QTextCursor(cursor))
            self._extra_selections_cache = None

        bottom_cursor = max(self.multi_cursors, key=lambda c: c.blockNumber())
        new_cursor = QTextCursor(bottom_cursor)
        
        moved = new_cursor.movePosition(QTextCursor.Down)

        if moved and new_cursor.blockNumber() > bottom_cursor.blockNumber():
            self.add_cursor_at(new_cursor)
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = True
            self.editor.setTextCursor(new_cursor)
            if hasattr(self.editor, '_is_auto_selecting'):
                self.editor._is_auto_selecting = False
            self.editor.highlight_current_line()
