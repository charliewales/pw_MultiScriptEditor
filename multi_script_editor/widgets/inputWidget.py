from vendor.Qt.QtCore import QPoint, Qt, Signal, QTimer
from vendor.Qt.QtGui import QColor, QFont, QFontMetrics, QTextCursor, QTextFormat, QTextOption
from vendor.Qt.QtWidgets import QTextEdit
import re
import jedi
from widgets.pythonSyntax import syntaxHighLighter
from widgets import completeWidget
import settingsManager
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
        self.setTabStopWidth(4 * metrics.width(' '))
        self.setAcceptDrops(True)
        self.fs = 12
        self.completer = completeWidget.completeMenuClass(parent, self)
        self.data = settingsManager.scriptEditorClass().readSettings()
        self.applyHightLighter(self.data.get('theme'))
        self.set_start_font()
        self.changeFontSize(True)
        self.highlight_current_line()

        # Performance optimization: Use a debounced timer for jedi autocompletion parsing to prevent UI lag on fast typing
        self.autocomplete_timer = QTimer(self)
        self.autocomplete_timer.setSingleShot(True)
        self.autocomplete_timer.timeout.connect(self.parseText)
        self.syntax_errors = {}

    def set_start_font(self):
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
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        qss = design.applyColorToEditorStyle(colors)
        self.setStyleSheet(qss)
        self.completer.setStyleSheet(qss)
        self.blockSignals(False)

    def parseText(self):
        if self.completer:
            text = self.toPlainText()
            self.moveCompleter()
            if text:
                tc = self.textCursor()
                context_completer = False
                pos = tc.position()
                if managers.context in managers.contextCompleters:
                    line = text[:pos].split('\n')[-1]
                    comp, extra = managers.contextCompleters[managers.context ](line, self.p.namespace)
                    if comp or extra:
                        context_completer = True
                        self.completer.updateCompleteList(comp, extra)
                if not context_completer:
                    if pos > 0 and re.match('[a-zA-Z0-9_.]', text[pos-1]):
                        offs = 0
                        if managers.context in managers.autoImport:
                            autoImp = managers.autoImport.get(managers.context, '')
                            text = autoImp + text
                            offs = len(autoImp.split('\n'))-1
                        bl = tc.blockNumber() + 1 + offs
                        col = tc.columnNumber()
                        script = jedi.Script(code=text)
                        try:
                            self.completer.updateCompleteList(script.complete(line=bl, column=col))
                        except:
                            self.completer.updateCompleteList()
                    else:
                        self.completer.updateCompleteList()
            else:
                self.completer.updateCompleteList()
        self.runLinter()

    def runLinter(self):
        code = self.toPlainText()
        self.syntax_errors = {}
        if code.strip():
            try:
                compile(code.encode('utf-8'), '<string>', 'exec')
            except SyntaxError as e:
                self.syntax_errors[e.lineno] = e.msg
            except Exception:
                pass

        if hasattr(self.parent(), 'lineNum'):
            self.parent().lineNum.update()

        main_win = self.p
        if hasattr(main_win, 'updateOutline'):
            main_win.updateOutline()
        if hasattr(main_win, 'statusBar') and main_win.statusBar():
            if self.syntax_errors:
                first_err_line = list(self.syntax_errors.keys())[0]
                msg = self.syntax_errors[first_err_line]
                main_win.statusBar().showMessage("Syntax Error on line {0}: {1}".format(first_err_line, msg))
            else:
                main_win.statusBar().clearMessage()

    def moveCompleter(self):
        rec = self.cursorRect()
        pt = self.mapToGlobal(rec.bottomRight())
        y=x=0
        if self.completer.isVisible() and self.desk:
            currentScreen = self.desk.screenGeometry(self.mapToGlobal(rec.bottomRight()))
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
        parse = 0

        # for tab cycling
        tabWidget = self.parent().parent().parent()
        current_tab_index = tabWidget.currentIndex()
        tab_count = tabWidget.count()

        # apply complete
        if event.modifiers() == Qt.NoModifier and event.key() in [Qt.Key_Return , Qt.Key_Enter]:
            if self.completer and self.completer.isVisible():
                self.completer.applyCurrentComplete()
                return
            # auto indent
            else:
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
                self.move_line_up()
                return
            elif event.key() == Qt.Key_Down:
                self.move_line_down()
                return
            elif event.key() == Qt.Key_W:
                if hasattr(self.p, 'toggle_word_wrap'):
                    self.p.toggle_word_wrap()
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
        if parse and event.text():
            self.autocomplete_timer.start(200) # 200 ms debounce delay

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
        # set background color of current line
        cursor = self.textCursor()
        selection = QTextEdit.ExtraSelection()
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        data = settingsManager.scriptEditorClass().readSettings() or {}
        theme = data.get('theme', 'default')
        theme_colors = data.get("colors", {}).get(theme, {})
        highlight_color = theme_colors.get('highlight_line', (85,85,85))
        selection.format.setBackground(QColor.fromRgb(*highlight_color))  # set the background color
        selection.cursor = cursor
        self.setExtraSelections([selection])

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
        before = start[:-len(comp.name)]
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

        res = before + comp.name + br + end

        cursor.beginEditBlock()
        cursor.insertText(res)
        cursor.endEditBlock()
        cursor.clearSelection()
        cursor.setPosition(pos+ofs,QTextCursor.MoveAnchor)
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

    def selectWord(self, pattern, number, replace=None):
        text = self.toPlainText()
        if not pattern in text:
            return number
        cursor = self.textCursor()
        indexis = [(m.start(0), m.end(0)) for m in re.finditer(self.fixRegextSymbols(pattern), text)]
        if number > len(indexis)-1:
            number = 0
        cursor.setPosition(indexis[number][0])
        cursor.setPosition(indexis[number][1], QTextCursor.KeepAnchor)
        if replace:
            cursor.removeSelectedText()
            cursor.insertText(replace)
        self.setTextCursor(cursor)
        self.setFocus()
        return number

    def fixRegextSymbols(self, pattern):
        for s in ['[',']','(',')','*','^', '.', ',', '{', '}','$']:
            pattern = pattern.replace(s, '\\'+s)
        return pattern

    def replaceAll(selfold, new):
        pass

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
