from vendor.Qt.QtCore import QPoint, Qt, Signal, QTimer
from vendor.Qt.QtGui import QColor, QFont, QFontMetrics, QTextCursor, QTextFormat, QTextOption, QTextDocument
from vendor.Qt.QtWidgets import QTextEdit
import re

from widgets.pythonSyntax import syntaxHighLighter
from widgets import completeWidget
from core.settings_model import SettingsModel
import managers
from widgets.pythonSyntax import design

import re
addEndBracket = True

indentLen = 4
minimumFontSize = 10
escapeButtons = [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Delete, Qt.Key_Insert, Qt.Key_Escape]
# font_name = 'Courier'
font_name = 'Consolas'
# font_name = 'Lucida Console'


class inputClass(QTextEdit):
    executeSignal = Signal()
    saveSignal = Signal()
    inputSignal = Signal()
    def __init__(self, parent, desk=None):

        # https://github.com/davidhalter/jedi
        # http://jedi.jedidjah.ch/en/latest/
        super(inputClass, self).__init__(parent)

        self.setMouseTracking(True)  # Enable mouse tracking

        self.p = parent
        self.desk = desk
        self.setLineWrapMode(QTextEdit.NoWrap)
        if managers.context == 'hou':
            self.setCursorWidth(2)
        font = QFont(font_name)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        default_font = QFont(font_name, minimumFontSize)
        default_font.setStyleHint(QFont.Monospace)
        self.document().setDefaultFont(default_font)
        metrics = QFontMetrics(self.document().defaultFont())
        width = metrics.horizontalAdvance(' ') if hasattr(metrics, 'horizontalAdvance') else metrics.width(' ')
        if hasattr(self, 'setTabStopDistance'):
            self.setTabStopDistance(4 * width)
        else:
            self.setTabStopWidth(4 * width)
        self.setAcceptDrops(True)
        self.fs = 12
        self.completer = completeWidget.completeMenuClass(parent, self)
        self.data = SettingsModel().read_settings()
        self.applyHightLighter(self.data.get('theme'))
        self.set_start_font()
        self.changeFontSize(True)
        self.highlight_current_line()

        # Performance optimization: Use a debounced timer for jedi autocompletion parsing to prevent UI lag on fast typing
        self.autocomplete_timer = QTimer(self)
        self.autocomplete_timer.setSingleShot(True)
        self.autocomplete_timer.timeout.connect(self.parseText)
        self.syntax_errors = {}
        self.multi_cursors = []
        self._highlight_color_cache = None
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self.autocomplete_timer.start(200)

    def set_start_font(self, font_d=None):
        if font_d is None:
            font_d = self.data.get('font', {})
        family = font_d.get('family', 'Courier')
        pointSize = font_d.get('pointSize', 10)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1.0)
        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        self.setFont(editor_font)

    def focusOutEvent(self, event):
        self.saveSignal.emit()
        QTextEdit.focusOutEvent(self,event)

    def hideEvent(self, event):
        self.completer.updateCompleteList()
        try:
            QTextEdit.hideEvent(self,event)
        except:
            pass

    def applyHightLighter(self, theme=None, qss=None):
        self.blockSignals(True)
        colors = None
        self._highlight_color_cache = None
        if theme or not theme =='default':
            colors = design.getColors(theme)
            if self.completer:
                self.completer.updateStyle(colors)
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        st = design.editorStyle(theme)
        self.setStyleSheet(st)
        self.blockSignals(False)

    def applyPreviewStyle(self, colors):
        self.blockSignals(True)
        self._highlight_color_cache = colors.get('highlight_line', (85,85,85)) if colors else None
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        qss = design.applyColorToEditorStyle(colors)
        self.setStyleSheet(qss)
        self.completer.setStyleSheet(qss)
        self.blockSignals(False)

    def parseText(self, force=False):
        if self.completer:
            if not force and hasattr(self.p, 'autocomplete_act') and not self.p.autocomplete_act.isChecked():
                self.completer.hide()
                self.runLinter()
                return
            if getattr(self, '_skip_autocomplete_once', False):
                self._skip_autocomplete_once = False
                self.completer.hide()
                self.runLinter()
                return
            text = self.toPlainText()
            self.moveCompleter()
            if text or force:
                tc = self.textCursor()
                pos = tc.position()
                
                # Check if we should autocomplete
                if force or (pos > 0 and re.match('[a-zA-Z0-9_.]', text[pos-1])):
                    bl = tc.blockNumber() + 1
                    col = tc.columnNumber()
                    namespace = self.p.namespace if hasattr(self.p, 'namespace') else None
                    use_fuzzy = self.p.fuzzy_autocomplete_act.isChecked() if hasattr(self.p, 'fuzzy_autocomplete_act') else True
                    
                    try:
                        comps = self.p._presenter.request_autocomplete(
                            text=text,
                            line=bl,
                            column=col,
                            namespace=namespace,
                            fuzzy=use_fuzzy,
                            context=managers.context
                        )
                        self.completer.updateCompleteList(comps)
                    except Exception as e:
                        print(e)
                        self.completer.updateCompleteList()
                else:
                    self.completer.updateCompleteList()
            else:
                self.completer.updateCompleteList()
        self.runLinter()

    def runLinter(self):
        main_win = self.p
        check_syntax = True
        if hasattr(main_win, 'syntaxCheck_act'):
            check_syntax = main_win.syntaxCheck_act.isChecked()

        code = self.toPlainText()
        if check_syntax and code.strip():
            # Delegate linting to the presenter
            self.p._presenter.request_lint(code)
        else:
            # Clear errors if check_syntax is disabled or code is empty
            self.syntax_errors = {}
            if hasattr(self.p, 'show_syntax_errors'):
                self.p.show_syntax_errors({})

    def moveCompleter(self):
        rec = self.cursorRect()
        pt = self.mapToGlobal(rec.bottomRight())
        y=x=0
        if self.completer.isVisible():
            if self.desk:
                currentScreen = self.desk.screenGeometry(self.mapToGlobal(rec.bottomRight()))
            else:
                from vendor.Qt.QtGui import QGuiApplication
                screen = QGuiApplication.screenAt(self.mapToGlobal(rec.bottomRight()))
                if screen is None:
                    screen = QGuiApplication.primaryScreen()
                currentScreen = screen.geometry()
            futureCompGeo = self.completer.geometry()
            futureCompGeo.moveTo(pt)
            if not currentScreen.contains(futureCompGeo):
                try:
                    i = currentScreen.intersect(futureCompGeo)
                except:
                    i = currentScreen.intersected(futureCompGeo)
                x = futureCompGeo.width() - i.width()
                y = futureCompGeo.height()+self.completer.lineHeight if (futureCompGeo.height()-i.height())>0 else 0

        pt = self.mapToGlobal(rec.bottomRight()) + QPoint(10-x, -y)
        self.completer.move(pt)

    def charBeforeCursor(self, cursor):
        pos = cursor.position()
        if pos:
            text = self.toPlainText()
            return text[pos-1]

    def getCurrentIndent(self):
        cursor = self.textCursor()
        auto = self.charBeforeCursor(cursor) == ':'
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        result = ''
        if line.strip():
            p = r"(^\s*)"
            m = re.search(p, line)
            if m:
                result = m.group(0)
            if auto:
                result += '    '
        return result

    def keyPressEvent(self, event):
        self.inputSignal.emit()
        if self.handle_multi_cursor_key(event):
            return
        parse = 0

        # for tab cycling
        tabWidget = self.parent().parent().parent()
        current_tab_index = tabWidget.currentIndex()
        tab_count = tabWidget.count()

        # force autocomplete, Ctrl+Space
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:
            self.parseText(force=True)
            return

        # apply complete
        if event.modifiers() == Qt.NoModifier and event.key() in [Qt.Key_Return , Qt.Key_Enter]:
            if self.completer and self.completer.isVisible():
                self._skip_autocomplete_once = True
                self.completer.applyCurrentComplete()
                return
            
            self._skip_autocomplete_once = True
            
            # auto indent
            add = self.getCurrentIndent()
            if add:
                QTextEdit.keyPressEvent(self, event)
                cursor = self.textCursor()
                cursor.insertText(add)
                self.setTextCursor(cursor)
                return
        # comment, Alt+C
        elif event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_C:
            self.p.tab.comment()
            return
        # shuffle lines, Alt+up, Alt+down
        elif event.modifiers() == Qt.AltModifier:
            if event.key() == Qt.Key_Up:
                self._skip_autocomplete_once = True
                self.move_line_up()
                return
            elif event.key() == Qt.Key_Down:
                self._skip_autocomplete_once = True
                self.move_line_down()
                return
        # remove 4 spaces
        elif event.modifiers() == Qt.NoModifier and event.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine,QTextCursor.KeepAnchor)
            line = cursor.selectedText()
            if line:
                p = r"    $"
                m = re.search(p, line)
                if m:
                    cursor.removeSelectedText()
                    line = line[:-3]
                    cursor.insertText(line)
                    self.setTextCursor(cursor)
            parse = 1
        # execute all/selected on pressing Enter key (numpad)
        elif event.key() == Qt.Key_Enter:
            selection = self.getSelection()
            if selection:
                self.executeSignal.emit()
            else:
                self.p.executeAll()
            event.ignore()
            return
        # execute selected
        elif event.modifiers() == Qt.ControlModifier and event.key() in [Qt.Key_Return , Qt.Key_Enter]:
            if self.completer:
                self.completer.updateCompleteList()
            self.executeSignal.emit()
            return
        # focus previous tab with Ctrl+Shift+Tab
        elif (event.modifiers() & Qt.ControlModifier) and (event.modifiers() & Qt.ShiftModifier) and event.key() == Qt.Key_Backtab:
            previous_tab_index = (current_tab_index - 1) if current_tab_index > 0 else (tab_count - 1)
            tabWidget.setCurrentIndex(previous_tab_index)
            return
        # focus previous tab with Ctrl+PageUp
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_PageUp:
            previous_tab_index = (current_tab_index - 1) if current_tab_index > 0 else (tab_count - 1)
            tabWidget.setCurrentIndex(previous_tab_index)
            return
        # focus next tab with Ctrl+Tab
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Tab:
            next_tab_index = (current_tab_index + 1) if current_tab_index < (tab_count - 1) else 0
            tabWidget.setCurrentIndex(next_tab_index)
            return
        # focus next tab with Ctrl+PageDown
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_PageDown:
            next_tab_index = (current_tab_index + 1) if current_tab_index < (tab_count - 1) else 0
            tabWidget.setCurrentIndex(next_tab_index)
            return
        # ignore Shift + Enter
        elif event.modifiers() == Qt.ShiftModifier and event.key() in [Qt.Key_Return , Qt.Key_Enter]:
            return
        # duplicate
        elif (event.modifiers() & Qt.ControlModifier) and (event.modifiers() & Qt.ShiftModifier) and event.key() == Qt.Key_D:
            self.duplicate()
            self.update()
            return
        # delete
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
            self.deleteLine()
            self.update()
            return
        # increase indent
        elif event.key() == Qt.Key_Tab:
            if self.completer:
                if self.completer.isVisible():
                    self._skip_autocomplete_once = True
                    self.completer.applyCurrentComplete()
                    return
            if self.textCursor().selection().toPlainText():
                self.selectBlocks()
                self.moveSelected(True)
                return
            else:
                self.insertPlainText (' ' * indentLen)
                return
        # decrease indent
        elif event.key() == Qt.Key_Backtab:
            self.selectBlocks()
            self.moveSelected(False)
            if self.completer:
                self.completer.updateCompleteList()
            return
        # close completer
        elif event.key() in escapeButtons:
            if self.completer:
                self.completer.updateCompleteList()
            self.setFocus()
        # go to completer
        elif event.key() == Qt.Key_Down or event.key() == Qt.Key_Up:
            if self.completer.isVisible():
                self.completer.activateCompleter(event.key())
                self.completer.setFocus()
                return
        # just close completer
        elif not event.modifiers() == Qt.NoModifier and not event.modifiers() == Qt.ShiftModifier:
            self.completer.updateCompleteList()
        else:
            parse = 1

        QTextEdit.keyPressEvent(self, event)

        # start parse text (Debounced to prevent lag on keypress)
        # Note: We now rely on textChanged signal for more reliable updates,
        # but if we needed key-specific parsing, it would go here.

        self.highlight_current_line()

    def move_line_up(self):
        self.move_selected_lines(-1)

    def move_line_down(self):
        self.move_selected_lines(1)

    def selected_line_range(self):
        cursor = self.textCursor()
        document = self.document()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        end_lookup = end
        if cursor.hasSelection() and end > start:
            end_lookup = end - 1
        start_block = document.findBlock(start)
        end_block = document.findBlock(end_lookup)
        return start_block.blockNumber(), end_block.blockNumber()

    def line_position(self, line):
        block = self.document().findBlockByNumber(line)
        if block.isValid():
            return block.position()
        return len(self.toPlainText())

    def move_selected_lines(self, direction):
        start_line, end_line = self.selected_line_range()
        text = self.toPlainText()
        lines = text.split('\n')
        if direction < 0:
            if start_line <= 0:
                return
            moving = lines[start_line:end_line + 1]
            lines[start_line:end_line + 1] = []
            insert_at = start_line - 1
            lines[insert_at:insert_at] = moving
        else:
            if end_line >= len(lines) - 1:
                return
            moving = lines[start_line:end_line + 1]
            lines[start_line:end_line + 1] = []
            insert_at = start_line + 1
            lines[insert_at:insert_at] = moving

        # Save cursor details relative to their blocks to restore position and selection correctly
        cursor = self.textCursor()
        anchor = cursor.anchor()
        position = cursor.position()

        anchor_block = self.document().findBlock(anchor)
        anchor_col = anchor - anchor_block.position()
        anchor_block_num = anchor_block.blockNumber()

        pos_block = self.document().findBlock(position)
        pos_col = position - pos_block.position()
        pos_block_num = pos_block.blockNumber()

        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText('\n'.join(lines))
        cursor.endEditBlock()

        # Reconstruct cursor with original selection and column position shifted by direction
        new_cursor = self.textCursor()
        new_anchor_block = self.document().findBlockByNumber(anchor_block_num + direction)
        new_pos_block = self.document().findBlockByNumber(pos_block_num + direction)

        if new_anchor_block.isValid() and new_pos_block.isValid():
            new_anchor = new_anchor_block.position() + anchor_col
            new_pos = new_pos_block.position() + pos_col
            new_cursor.setPosition(new_anchor)
            new_cursor.setPosition(new_pos, QTextCursor.KeepAnchor)
            self.setTextCursor(new_cursor)

        self.highlight_current_line()

    def highlight_current_line(self):
        selections = []

        # set background color of current line
        cursor = self.textCursor()
        selection = QTextEdit.ExtraSelection()
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)

        if getattr(self, '_highlight_color_cache', None) is None:
            data = SettingsModel().read_settings() or {}
            theme = data.get('theme', 'default')
            theme_colors = data.get("colors", {}).get(theme, {})
            self._highlight_color_cache = theme_colors.get('highlight_line', (85,85,85))

        selection.format.setBackground(QColor.fromRgb(*self._highlight_color_cache))  # set the background color
        selection.cursor = cursor
        selections.append(selection)

        # Draw multi-cursors
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            for mc in self.multi_cursors:
                sel = QTextEdit.ExtraSelection()
                if mc.hasSelection():
                    sel.cursor = mc
                    # Use a semi-transparent selection color
                    sel.format.setBackground(QColor(40, 100, 200, 120))
                else:
                    # Simulated cursor block: highlight next character if possible
                    c_copy = QTextCursor(mc)
                    if not c_copy.atEnd():
                        c_copy.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                        sel.cursor = c_copy
                        # Draw simulated cursor color
                        sel.format.setBackground(QColor(128, 128, 255, 180))
                    else:
                        # At the end of the line/document, we can format the cursor directly or highlight
                        sel.cursor = c_copy
                        sel.format.setBackground(QColor(128, 128, 255, 180))
                selections.append(sel)

        self.setExtraSelections(selections)

    def moveSelected(self, inc):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.document().documentLayout().blockSignals(True)
            self.selectBlocks()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            text = cursor.selection().toPlainText()
            cursor.removeSelectedText()
            if inc:
                newText = self.addTabs(text)
            else:
                newText = self.removeTabs(text)
            cursor.beginEditBlock()
            cursor.insertText(newText)
            cursor.endEditBlock()
            newEnd = cursor.position()
            cursor.setPosition(start)
            cursor.setPosition(newEnd, QTextCursor.KeepAnchor)
            self.document().documentLayout().blockSignals(False)
            self.setTextCursor(cursor)
            self.update()

    def addQuotesSelected(self):
        cursor = self.textCursor()
        self.document().documentLayout().blockSignals(True)
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        text = cursor.selection().toPlainText()
        if text:
            cursor.insertText('"' + text + '"')
        self.document().documentLayout().blockSignals(False)
        self.setTextCursor(cursor)
        self.update()

    def commentSelected(self):
        cursor = self.textCursor()
        self.document().documentLayout().blockSignals(True)
        self.selectBlocks()
        pos = cursor.position()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.setPosition(end,QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
        text = cursor.selection().toPlainText()
        self.document().documentLayout().blockSignals(False)
        text, offset = self.addRemoveComments(text)
        cursor.insertText(text)
        cursor.setPosition(min(pos+offset, len(self.toPlainText())))
        self.setTextCursor(cursor)
        self.update()

    def addRemoveComments(self, text):
        result = text
        ofs = 0
        if text.strip():
            lines = text.split('\n')
            ind = 0
            while not lines[ind].strip():
                ind += 1
            if lines[ind].strip()[0] == '#': # remove comment
                result = '\n'.join([x.replace('#','',1) for x in lines])
                ofs = -1
            else:   # add comment
                result = '\n'.join(['#'+x for x in lines ])
                ofs = 1
        return result, ofs

    def insertText(self, comp):
        cursor = self.textCursor()
        self.document().documentLayout().blockSignals(True)
        if comp.complete:
            cursor.insertText(comp.complete)
        cursor = self.fixLine(cursor, comp)
        self.document().documentLayout().blockSignals(False)
        self.setTextCursor(cursor)
        self.update()

    def fixLine(self, cursor, comp):
        pos = cursor.position()
        linePos = cursor.positionInBlock()

        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        cursor.removeSelectedText()

        start = line[:linePos]
        end = line[linePos:]
        to_remove = len(comp.name)
        if hasattr(comp, 'get_completion_prefix_length'):
            comp_len = len(comp.complete) if comp.complete else 0
            to_remove = comp.get_completion_prefix_length() + comp_len
            
        before = start[:-to_remove] if to_remove > 0 else start
        br = ''
        ofs = 0
        if hasattr(comp, 'end_char'):
            if addEndBracket and before and comp.end_char:
                brackets = {'"':'"', "'":"'"}#, '(':')', '[':']'}
                if before[-1] in brackets:
                    ofs = 1
                    br = brackets[before[-1]]
                    if end and end[0] == brackets[before[-1]]:
                        br = ''

        # Auto-add parenthesis for functions/methods/classes
        if hasattr(comp, 'type') and comp.type in ('function', 'class', 'method'):
            is_import = bool(re.match(r'^\s*(from|import)\b', start))
            if not end.startswith('(') and not is_import:
                br += '()'
                ofs += 1 # Move cursor inside the parenthesis

        res = before + comp.name + br + end

        cursor.beginEditBlock()
        cursor.insertText(res)
        cursor.endEditBlock()
        cursor.clearSelection()
        new_pos = pos - linePos + len(before) + len(comp.name) + ofs
        cursor.setPosition(new_pos, QTextCursor.MoveAnchor)
        return cursor

    def duplicate(self):
        cursor = self.textCursor()
        current_cursor_pos = cursor.position()

        if cursor.hasSelection(): # duplicate selected
            sel = cursor.selectedText()
            end = cursor.selectionEnd()
            cursor.setPosition(end)
            cursor.insertText(sel)
            cursor.setPosition(end,QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        else: # duplicate line
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
            line = cursor.selectedText()
            cursor.clearSelection()
            cursor.insertText('\n'+line)
            cursor.setPosition(current_cursor_pos + len(line) + 1)
            self.setTextCursor(cursor)

        self.highlight_current_line()

    def deleteLine(self):
        cursor = self.textCursor()
        current_cursor_pos = cursor.position()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
        selected_text = cursor.selectedText()
        cursor.removeSelectedText();
        cursor.deleteChar();
        cursor.setPosition(current_cursor_pos)
        self.setTextCursor(cursor)
        self.highlight_current_line()

    def removeTabs(self, text):
        lines = text.split('\n')
        new = []
        pat = re.compile("^ .*")
        for line in lines:
            line = line.replace('\t', ' '*indentLen)
            for _ in range(4):
                if pat.match(line):
                    line = line[1:]
            new.append(line)
        return '\n'.join(new)

    def addTabs(self, text):
        lines = [(' '*indentLen)+x for x in text.split('\n')]
        return '\n'.join(lines)

    def selectBlocks(self):
        self.document().documentLayout().blockSignals(True)
        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.document().documentLayout().blockSignals(False)

    def getSelection(self):
        cursor = self.textCursor()
        text = cursor.selection().toPlainText()
        return text

    def addText(self, text):
        if self.completer:
                self.completer.updateCompleteList()
        self.blockSignals(True)
        self.append(text)
        self.blockSignals(False)

    ########################### DROP
    def dragEnterEvent(self, event):
        event.acceptProposedAction()
        QTextEdit.dragEnterEvent(self,event)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        QTextEdit.dragMoveEvent(self,event)

    def dragLeaveEvent(self, event):
        event.accept()
        QTextEdit.dragLeaveEvent(self,event)

    def dropEvent(self, event):
        event.acceptProposedAction()
        if managers.context in managers.dropEvents and event.mimeData().hasText():
            mim = event.mimeData()
            text = mim.text()
            namespace = self.p.namespace
            text = managers.dropEvents[managers.context](namespace, text, event)
            mim.setText(text)
            QTextEdit.dropEvent(self,event)
        else:
            QTextEdit.dropEvent(self,event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if self.completer:
                self.completer.updateCompleteList()
            if event.angleDelta().y() > 0:
                self.changeFontSize(True)
            else:
                self.changeFontSize(False)
        else:
            QTextEdit.wheelEvent(self, event)

    def changeFontSize(self, up):
        if managers.context == 'hou':
            if up:
                self.fs = min(30, self.fs+1)
            else:
                self.fs = max(8, self.fs - 1)
            self.setTextEditFontSize(self.fs)
        else:
            f = self.font()
            size = f.pointSize()
            if up:
                size = min(30, size+1)
            else:
                size = max(8, size - 1)
            f.setPointSize(size)
            f.setFamily(font_name)
            self.setFont(f)

    def setTextEditFontSize(self, size):
        style = self.styleSheet() +'''QTextEdit
    {
        font-size: %spx;
        font-family: %s;
    }''' % (size, font_name)
        self.setStyleSheet(style)
        f = self.font()
        f.setPointSize(size)
        f.setFamily(font_name)
        self.setFont(f)

    def insertFromMimeData (self, source ):
        text = source.text()
        self.insertPlainText(text)

    def getFontSize(self):
        s = self.font().pointSize()
        return s

    def setFontSize(self,size):
        if size > minimumFontSize:
            if managers.context == 'hou':
                self.fs = size
                self.setTextEditFontSize(self.fs)
            else:
                f = self.font()
                f.setPointSize(size)
                self.setFont(f)

    def mousePressEvent(self, event):
        self.completer.updateCompleteList()
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
        super(inputClass, self).mousePressEvent(event)
        self.highlight_current_line()

    def function_cmd(self, function):
        selectedText = self.get_current_word()
        cmd = '{0}({1})'.format(function, selectedText)
        return cmd

    def get_current_word(self):
        cursor = self.textCursor()
        selectedText = cursor.selection().toPlainText()
        if not selectedText:
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)
            selectedText = cursor.selection().toPlainText()
        return selectedText

    def selectWord(self, pattern, number, replace=None, case_sensitive=False):
        text = self.toPlainText()
        flags = 0 if case_sensitive else re.IGNORECASE
        
        indexis = [(m.start(0), m.end(0)) for m in re.finditer(re.escape(pattern), text, flags=flags)]
        if not indexis:
            return number
            
        if number > len(indexis)-1:
            number = 0
            
        cursor = self.textCursor()
        cursor.setPosition(indexis[number][0])
        cursor.setPosition(indexis[number][1], QTextCursor.KeepAnchor)
        if replace is not None:
            cursor.removeSelectedText()
            cursor.insertText(replace)
        self.setTextCursor(cursor)
        self.setFocus()
        return number

    def replaceAll(self, find, rep, case_sensitive=False):
        if not find:
            return
            
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Start from beginning
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)
        
        options = QTextDocument.FindCaseSensitively if case_sensitive else QTextDocument.FindFlags()
        
        while self.find(find, options):
            self.textCursor().insertText(rep)
            
        cursor.endEditBlock()
        self.completer.updateCompleteList()

    def wordWrap(self, state):
        if state:
            self.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QTextEdit.NoWrap)

    def render_whitespace(self, state):
        text_option = QTextOption()
        if state:
            text_option.setFlags(QTextOption.ShowTabsAndSpaces)
            self.document().setDefaultTextOption(text_option)
        else:
            self.document().setDefaultTextOption(text_option)

    # --- Multi-Cursor / Multi-Selection Support ---

    def handle_multi_cursor_key(self, event):
        if not hasattr(self, 'multi_cursors') or not self.multi_cursors:
            return False

        key = event.key()
        modifiers = event.modifiers()

        # Escape key clears multi-cursor mode
        if key == Qt.Key_Escape:
            self.multi_cursors = []
            self.highlight_current_line()
            return True

        # Clear on Ctrl+A
        if key == Qt.Key_A and (modifiers & Qt.ControlModifier):
            self.multi_cursors = []
            self.highlight_current_line()
            return False

        # Check navigation keys
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

            # Ctrl + Left/Right moves word by word
            if key == Qt.Key_Left and (modifiers & Qt.ControlModifier):
                op = QTextCursor.WordLeft
            elif key == Qt.Key_Right and (modifiers & Qt.ControlModifier):
                op = QTextCursor.WordRight

            # Apply movement to all cursors
            for cursor in self.multi_cursors:
                cursor.movePosition(op, mode)

            self.deduplicate_and_sort_cursors()

            # Keep main cursor in sync with the first cursor in our list
            if self.multi_cursors:
                self.setTextCursor(self.multi_cursors[0])
            self.highlight_current_line()
            return True

        # Text edits (typing, backspace, delete, return, tab)
        is_edit = False
        text = event.text()

        # Sort cursors descending by position so edits at the bottom do not affect offsets of top cursors
        sorted_cursors = sorted(self.multi_cursors, key=lambda c: c.position(), reverse=True)

        main_cursor = self.textCursor()
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
                self.setTextCursor(self.multi_cursors[0])
            self.highlight_current_line()
            # Trigger autocomplete parsing (with debounce)
            self.autocomplete_timer.start(200)
            return True

        return False

    def deduplicate_and_sort_cursors(self):
        if not hasattr(self, 'multi_cursors') or not self.multi_cursors:
            return
        seen = set()
        unique_cursors = []
        # Sort by position, anchor to maintain stable order and identify duplicates
        sorted_c = sorted(self.multi_cursors, key=lambda c: (c.position(), c.anchor()))
        for c in sorted_c:
            key = (c.position(), c.anchor())
            if key not in seen:
                seen.add(key)
                unique_cursors.append(c)
        self.multi_cursors = unique_cursors

    def select_next_occurrence(self):
        cursor = self.textCursor()

        # If no selection on the current cursor, select the word under the cursor first
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)

        if not cursor.hasSelection():
            return

        target_text = cursor.selectedText()
        if not target_text:
            return

        if not hasattr(self, 'multi_cursors') or not self.multi_cursors:
            self.multi_cursors = [cursor]

        # Find starting position for the next search
        last_cursor = self.multi_cursors[-1]
        start_pos = last_cursor.position()

        # Search forward
        found_cursor = self.document().find(target_text, start_pos)

        # Wrap around if not found
        if found_cursor.isNull() or found_cursor.position() <= start_pos:
            found_cursor = self.document().find(target_text, 0)

        if not found_cursor.isNull():
            # Check if already selected
            already_selected = False
            for mc in self.multi_cursors:
                if mc.selectionStart() == found_cursor.selectionStart() and mc.selectionEnd() == found_cursor.selectionEnd():
                    already_selected = True
                    break

            if not already_selected:
                self.multi_cursors.append(found_cursor)
                self.setTextCursor(found_cursor)

        self.highlight_current_line()

    def select_all_occurrences(self):
        cursor = self.textCursor()

        # If no selection on the current cursor, select the word under the cursor first
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)

        if not cursor.hasSelection():
            return

        target_text = cursor.selectedText()
        if not target_text:
            return

        self.multi_cursors = []
        start_pos = 0
        while True:
            found_cursor = self.document().find(target_text, start_pos)
            if found_cursor.isNull():
                break
            if found_cursor.position() <= start_pos:
                break
            self.multi_cursors.append(found_cursor)
            start_pos = found_cursor.position()

        self.highlight_current_line()

    # Clear multi-cursor selections on standard clipboard and undo/redo operations
    def undo(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
            self.highlight_current_line()
        super(inputClass, self).undo()

    def redo(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
            self.highlight_current_line()
        super(inputClass, self).redo()

    def cut(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
            self.highlight_current_line()
        super(inputClass, self).cut()

    def copy(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
            self.highlight_current_line()
        super(inputClass, self).copy()

    def paste(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self.multi_cursors = []
            self.highlight_current_line()
        super(inputClass, self).paste()
