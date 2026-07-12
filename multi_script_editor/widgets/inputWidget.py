from vendor.Qt.QtCore import QPoint, Qt, Signal, QTimer
from vendor.Qt.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QTextCursor,
    QTextFormat,
    QGuiApplication,
)
from vendor.Qt.QtWidgets import QTextEdit, QApplication
import re
import os

from widgets.pythonSyntax import syntaxHighLighter, extraSyntaxes
from widgets import completeWidget
from core.settings_model import SettingsModel
from core.base_text_widget import BaseTextWidgetMixin
from core.multi_cursor import MultiCursorManager
from core.search_service import SearchService
import managers
from widgets.pythonSyntax import design

import re
addEndBracket = True

indentLen = 4
minimumFontSize = 8
escapeButtons = [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Delete, Qt.Key_Insert, Qt.Key_Escape]
# font_name = 'monospace'
font_name = 'Consolas'
# font_name = 'Lucida Console'


class inputClass(BaseTextWidgetMixin, QTextEdit):
    executeSignal = Signal()
    saveSignal = Signal()
    inputSignal = Signal()
    messageSignal = Signal(str)
    def __init__(self, parent, desk=None):

        # https://github.com/davidhalter/jedi
        # http://jedi.jedidjah.ch/en/latest/
        super(inputClass, self).__init__(parent)

        self.setMouseTracking(True)  # Enable mouse tracking

        self.p = parent
        self.desk = desk
        self.search_service = SearchService(self)
        self.multi_cursor_manager = MultiCursorManager(self)
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

        self._lint_timer = QTimer(self)
        self._lint_timer.setSingleShot(True)
        self._lint_timer.timeout.connect(self.runLinter)

        self.multi_cursors = []
        self._highlight_color_cache = None
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.selectionChanged.connect(self.auto_select_all_occurrences)

        # Flag to prevent recursion
        self._is_auto_selecting = False
        self._is_undo_redo = False

    def _on_text_changed(self):
        if hasattr(self, 'multi_cursor_manager') and self.multi_cursor_manager.has_cursors():
            pass
        elif getattr(self, '_is_undo_redo', False):
            pass
        else:
            self.autocomplete_timer.start(200)

    def set_start_font(self, font_d=None):
        if not font_d:
            self.data = SettingsModel().read_settings()
            theme_name = self.data.get('theme', 'Multi Script Editor')
            colors = design.getColors(theme_name)
            font_d = colors.get('font')
            if not font_d:
                font_d = self.data.get('font', {})
        family = font_d.get('family', 'monospace')
        pointSize = font_d.get('pointSize', 10)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1.0)


        try:
            families = QFontDatabase.families()
        except TypeError:
            db = QFontDatabase()
            families = db.families()

        if family not in families:
            variations = [
                family.replace(" NFM", " Nerd Font Mono"),
                family.replace(" Nerd Font Mono", " NFM"),
                family.replace(" NFP", " Nerd Font Propo"),
                family.replace(" Nerd Font Propo", " NFP"),
                family.replace(" NF", " Nerd Font"),
                family.replace(" Nerd Font", " NF"),
                family.replace(" Nerd Font Mono", " Nerd Font"),
                family.replace(" Nerd Font Propo", " Nerd Font"),
                family.replace(" Nerd Font", " Nerd Font Mono"),
                family.replace(" Nerd Font", " Nerd Font Propo")
            ]
            for alt in variations:
                if alt in families:
                    family = alt
                    break

        editor_font = QFont(family, pointSize, weight, italic)
        editor_font.setStyleHint(QFont.Monospace)
        self.blockSignals(True)
        self.setFont(editor_font)
        self.blockSignals(False)

    def setFont(self, font):
        super(inputClass, self).setFont(font)
        if hasattr(self, 'completer') and self.completer:
            use_theme_font = True
            colors = {}
            if hasattr(self, 'p') and self.p and hasattr(self.p, '_current_colors_cache'):
                colors = self.p._current_colors_cache
                use_theme_font = colors.get('use_theme_font_on_completer', True)
            if use_theme_font:
                new_font = QFont(font)
            else:
                new_font = QApplication.font("QListWidget")
                
            if 'completer_text_size' in colors:
                new_font.setPointSize(max(1, int(colors['completer_text_size'])))
            else:
                new_font.setPointSize(max(1, int(font.pointSize() * 0.9)))
                
            self.completer.setFont(new_font)
            if hasattr(self.completer, 'doc_tooltip') and self.completer.doc_tooltip:
                self.completer.doc_tooltip.setFont(new_font)

    def focusOutEvent(self, event):
        self.saveSignal.emit()
        QTextEdit.focusOutEvent(self,event)
        QTimer.singleShot(10, self._check_focus_loss)

    def _check_focus_loss(self):
        focus_w = QApplication.focusWidget()
        main_window = self.window()

        # Hide symbol widget if focus didn't move to it
        is_symbol = False
        if hasattr(main_window, 'symbol_widget') and main_window.symbol_widget:
            if focus_w and (focus_w == main_window.symbol_widget or main_window.symbol_widget.isAncestorOf(focus_w)):
                is_symbol = True

        if not is_symbol and hasattr(main_window, 'symbol_widget') and main_window.symbol_widget:
            main_window.symbol_widget.hide()

        # Hide completer and docstrings
        is_completer = False
        if hasattr(self, 'completer') and self.completer:
            if focus_w and (focus_w == self.completer or self.completer.isAncestorOf(focus_w) or focus_w == getattr(self.completer, 'doc_tooltip', None)):
                is_completer = True

        if not is_completer and hasattr(self, 'completer') and self.completer:
            if hasattr(self.completer, 'hideMe'):
                self.completer.hideMe()
            else:
                self.completer.hide()

    def hideEvent(self, event):
        self.completer.updateCompleteList()
        try:
            QTextEdit.hideEvent(self,event)
        except:
            pass

    def applyHightLighter(self, theme=None, ext=None):
        self.blockSignals(True)
        colors = None
        if theme or not theme =='Multi Script Editor':
            colors = design.getColors(theme)
            if self.completer:
                self.completer.updateStyle(colors)
        self._highlight_color_cache = colors.get('highlight_line', (85,85,85)) if colors else None
        self._line_num_text_cache = colors.get('line_num_text', colors.get('tab_selected_text', (200,200,200))) if colors else None
        self._line_num_size_cache = colors.get('line_numbers_text_size', None) if colors else None
        highlighter_class = syntaxHighLighter.PythonHighlighterClass

        if not ext and hasattr(self.parent(), 'file_path') and self.parent().file_path:
            ext = os.path.splitext(self.parent().file_path)[1]

        if ext:
            ext = ext.lower()
            if ext == '.js':
                highlighter_class = extraSyntaxes.JavascriptHighlighterClass
            elif ext in ['.html', '.htm']:
                highlighter_class = extraSyntaxes.HtmlHighlighterClass
            elif ext in ['.yaml', '.yml']:
                highlighter_class = extraSyntaxes.YamlHighlighterClass
            elif ext == '.md':
                highlighter_class = extraSyntaxes.MarkdownHighlighterClass
            elif ext == '.css':
                highlighter_class = extraSyntaxes.CssHighlighterClass
            elif ext == '.txt':
                highlighter_class = extraSyntaxes.TextHighlighterClass
            elif ext in ['.usd', '.usda']:
                highlighter_class = extraSyntaxes.UsdHighlighterClass

        self.hgl = highlighter_class(self, colors)
        st = design.editorStyle(theme)
        self.setStyleSheet(st)
        self.blockSignals(False)
        self.highlight_current_line()

    def applyPreviewStyle(self, colors):
        self.blockSignals(True)
        self._highlight_color_cache = colors.get('highlight_line', (85,85,85)) if colors else None
        self._line_num_text_cache = colors.get('line_num_text', colors.get('tab_selected_text', (200,200,200))) if colors else None
        self._line_num_size_cache = colors.get('line_numbers_text_size', None) if colors else None
        self.hgl = syntaxHighLighter.PythonHighlighterClass(self, colors)
        qss = design.applyColorToMainStyle(colors)
        self.setStyleSheet(qss)
        self.completer.setStyleSheet(qss)
        self.blockSignals(False)
        self.highlight_current_line()

    def parseText(self, force=False):
        if self.completer:
            if not force and hasattr(self.p, 'autocomplete_act') and not self.p.autocomplete_act.isChecked():
                self.completer.hide()
                self._lint_timer.start(500)
                return
            if getattr(self, '_suppress_autocomplete', False) and not force:
                self.completer.hide()
                self._lint_timer.start(500)
                return
            if getattr(self, '_skip_autocomplete_once', False):
                self._skip_autocomplete_once = False
                self.completer.hide()
                self._lint_timer.start(500)
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
                        if hasattr(self.p, '_presenter'):
                            comps = self.p._presenter.request_autocomplete(
                                text=text,
                                line=bl,
                                column=col,
                                namespace=namespace,
                                fuzzy=use_fuzzy,
                                context=managers.context
                            )
                            self.completer.updateCompleteList(comps)
                        else:
                            self.completer.updateCompleteList()
                    except Exception as e:
                        print(e)
                        self.completer.updateCompleteList()
                else:
                    self.completer.updateCompleteList()
            else:
                self.completer.updateCompleteList()
        self._lint_timer.start(500)

    def runLinter(self):
        main_win = self.p
        check_syntax = True
        if hasattr(main_win, 'syntaxCheck_act'):
            check_syntax = main_win.syntaxCheck_act.isChecked()

        code = self.toPlainText()
        if check_syntax and code.strip():
            # Delegate linting to the presenter
            if hasattr(self.p, '_presenter'):
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
        # unsuppress autocomplete if alphanumeric or dot/underscore
        text = event.text()
        if text and (text.isalnum() or text in ['.', '_']):
            self._suppress_autocomplete = False

        # Multi-cursor interception
        if self.multi_cursor_manager.handle_key_press(event):
            return
        self.inputSignal.emit()
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

            if hasattr(self.p, 'trimAutoWhitespace_act') and self.p.trimAutoWhitespace_act.isChecked():
                cursor = self.textCursor()
                block = cursor.block()
                text = block.text()
                stripped = text.rstrip(' \t')
                diff = len(text) - len(stripped)
                if diff > 0:
                    c = QTextCursor(block)
                    c.movePosition(QTextCursor.EndOfBlock)
                    c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, diff)
                    c.removeSelectedText()

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
            if event.key() == Qt.Key_Escape:
                self._suppress_autocomplete = True
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
            theme = data.get('theme', 'Multi Script Editor')
            theme_colors = data.get("colors", {}).get(theme, {})
            self._highlight_color_cache = theme_colors.get('highlight_line', (85,85,85))

        selection.format.setBackground(QColor.fromRgb(*self._highlight_color_cache))  # set the background color
        selection.cursor = cursor
        selections.append(selection)

        # Draw multi-cursors
        selections.extend(self.multi_cursor_manager.get_extra_selections())

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

        if cursor.hasSelection():
            text = cursor.selection().toPlainText()
            is_quoted = False
            if len(text) >= 6 and (text.startswith("'''") and text.endswith("'''") or text.startswith('"""') and text.endswith('"""')):
                is_quoted = True
            elif len(text) >= 2 and (text.startswith("'") and text.endswith("'") or text.startswith('"') and text.endswith('"')):
                is_quoted = True

            if not is_quoted:
                doc = self.document()
                start = cursor.selectionStart()
                end = cursor.selectionEnd()

                cursor_copy = QTextCursor(cursor)
                text_before_3 = ""
                text_after_3 = ""
                if start >= 3:
                    cursor_copy.setPosition(start - 3)
                    cursor_copy.setPosition(start, QTextCursor.KeepAnchor)
                    text_before_3 = cursor_copy.selectedText()
                if end <= doc.characterCount() - 1 - 3:
                    cursor_copy.setPosition(end)
                    cursor_copy.setPosition(end + 3, QTextCursor.KeepAnchor)
                    text_after_3 = cursor_copy.selectedText()

                if (text_before_3 == '"""' and text_after_3 == '"""') or \
                   (text_before_3 == "'''" and text_after_3 == "'''"):
                    is_quoted = True
                else:
                    text_before_1 = ""
                    text_after_1 = ""
                    if start >= 1:
                        cursor_copy.setPosition(start - 1)
                        cursor_copy.setPosition(start, QTextCursor.KeepAnchor)
                        text_before_1 = cursor_copy.selectedText()
                    if end <= doc.characterCount() - 1 - 1:
                        cursor_copy.setPosition(end)
                        cursor_copy.setPosition(end + 1, QTextCursor.KeepAnchor)
                        text_after_1 = cursor_copy.selectedText()

                    if (text_before_1 == '"' and text_after_1 == '"') or \
                       (text_before_1 == "'" and text_after_1 == "'"):
                        is_quoted = True

            if not is_quoted:
                self.document().documentLayout().blockSignals(True)
                cursor.insertText('"' + text + '"')
                self.document().documentLayout().blockSignals(False)
                self.setTextCursor(cursor)
                self.update()
            return

        text = self.toPlainText()
        pos = cursor.position()
        pattern = r"('''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:[^\\']|\\.)*?'|\"(?:[^\\\"]|\\.)*?\")"

        best_match = None
        for match in re.finditer(pattern, text):
            start, end = match.span()
            if start <= pos <= end:
                if match.group(1).startswith("'''") or match.group(1).startswith('"""'):
                    inner_start, inner_end = start + 3, end - 3
                else:
                    inner_start, inner_end = start + 1, end - 1
                best_match = (inner_start, inner_end)
                break

        if best_match:
            inner_start, inner_end = best_match
            cursor.setPosition(inner_start)
            cursor.setPosition(inner_end, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.document().documentLayout().blockSignals(True)
            cursor.select(QTextCursor.WordUnderCursor)
            sel_text = cursor.selection().toPlainText()
            if sel_text:
                cursor.insertText('"' + sel_text + '"')
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
        has_selection = cursor.hasSelection()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        block_start = cursor.position()
        cursor.setPosition(end,QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,QTextCursor.KeepAnchor)
        text = cursor.selection().toPlainText()
        self.document().documentLayout().blockSignals(False)

        new_text, offset, shifts = self.addRemoveComments(text)

        def map_pos(p):
            rel_p = p - block_start
            lines = text.split('\n')
            current_old_len = 0
            current_new_len = 0
            for i, line in enumerate(lines):
                line_len = len(line) + 1 # +1 for \n
                if rel_p < current_old_len + line_len:
                    offset_in_line = rel_p - current_old_len
                    idx, shift = shifts[i]
                    if idx != -1 and offset_in_line > idx:
                        offset_in_line = max(idx, offset_in_line + shift)
                    return block_start + current_new_len + offset_in_line
                current_old_len += line_len
                idx, shift = shifts[i] if i < len(shifts) else (-1, 0)
                current_new_len += line_len + shift
            return block_start + current_new_len

        new_start = map_pos(start)
        new_end = map_pos(end)
        new_pos = map_pos(pos)

        cursor.beginEditBlock()
        cursor.insertText(new_text)
        cursor.endEditBlock()

        if has_selection:
            if pos == end:
                cursor.setPosition(new_start)
                cursor.setPosition(new_end, QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(new_end)
                cursor.setPosition(new_start, QTextCursor.KeepAnchor)
        else:
            cursor.setPosition(new_pos)

        self.setTextCursor(cursor)

        # Prevent autocomplete dialog from popping up due to textChanged
        if hasattr(self, 'autocomplete_timer'):
            self.autocomplete_timer.stop()
        if hasattr(self, 'completer') and self.completer:
            self.completer.hide()

        self.update()

    def addRemoveComments(self, text):
        result = text
        ofs = 0
        shifts = []
        if text.strip():
            lines = text.split('\n')
            ind = 0
            while ind < len(lines) and not lines[ind].strip():
                ind += 1
            if ind < len(lines) and lines[ind].strip()[0] == '#': # remove comment
                new_lines = []
                for i, x in enumerate(lines):
                    idx = x.find('#')
                    shift = 0
                    if idx != -1:
                        if len(x) > idx + 1 and x[idx+1] == ' ':
                            new_lines.append(x[:idx] + x[idx+2:])
                            shift = -2
                            if i == ind: ofs = -2
                        else:
                            new_lines.append(x[:idx] + x[idx+1:])
                            shift = -1
                            if i == ind: ofs = -1
                    else:
                        new_lines.append(x)
                    shifts.append((idx, shift))
                result = '\n'.join(new_lines)
            else:   # add comment
                result = '\n'.join(['# ' + x for x in lines ])
                shifts = [(0, 2)] * len(lines)
                ofs = 2
        else:
            shifts = [(0, 0)] * (text.count('\n') + 1)
        return result, ofs, shifts

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
        cursor.beginEditBlock()

        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()

            if end > start:
                cursor.setPosition(end)
                if cursor.atBlockStart():
                    end -= 1

            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)

            cursor.removeSelectedText()
            if cursor.atEnd() and cursor.position() > 0:
                cursor.deletePreviousChar()
            else:
                cursor.deleteChar()
        else:
            current_cursor_pos = cursor.position()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)

            cursor.removeSelectedText()
            if cursor.atEnd() and cursor.position() > 0:
                cursor.deletePreviousChar()
            else:
                cursor.deleteChar()

            max_pos = self.document().characterCount() - 1
            if current_cursor_pos > max_pos:
                current_cursor_pos = max_pos
            cursor.setPosition(current_cursor_pos)

        cursor.endEditBlock()
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
        self.setPlainText(text)
        self.document().clearUndoRedoStacks()
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
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        if hasattr(self.p, 'openRecentFile'):
                            self.p.openRecentFile(file_path)
            return

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


    def insertFromMimeData (self, source ):
        text = source.text()
        self.insertPlainText(text)

    def getFontSize(self):
        s = self.font().pointSize()
        return s

    def setFontSize(self,size):
        if size >= minimumFontSize:
            if managers.context == 'hou':
                self.fs = size
                self.setTextEditFontSize(self.fs)
            else:
                f = self.font()
                f.setPointSize(size)
                self.setFont(f)

    def mousePressEvent(self, event):
        self.completer.updateCompleteList()

        if event.modifiers() & Qt.ControlModifier:
            # Add cursor on Ctrl+Click
            cursor = self.cursorForPosition(event.pos())
            self.multi_cursor_manager.add_cursor_at(cursor)
            self.highlight_current_line()
            return

        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()

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
        return self.search_service.select_word(pattern, number, replace, case_sensitive)

    def replaceAll(self, find, rep, case_sensitive=False):
        self.search_service.replace_all(find, rep, case_sensitive)

    # --- Multi-Cursor / Multi-Selection Support ---
    def select_next_occurrence(self):
        self._is_manual_multi_selecting = True
        try:
            self.multi_cursor_manager.select_next_occurrence()
        finally:
            self._is_manual_multi_selecting = False

    def select_all_occurrences(self):
        self._is_manual_multi_selecting = True
        try:
            self.multi_cursor_manager.select_all_occurrences()
        finally:
            self._is_manual_multi_selecting = False

    def next_selection(self):
        self._is_manual_multi_selecting = True
        try:
            self.multi_cursor_manager.next_selection()
        finally:
            self._is_manual_multi_selecting = False

    def previous_selection(self):
        self._is_manual_multi_selecting = True
        try:
            self.multi_cursor_manager.previous_selection()
        finally:
            self._is_manual_multi_selecting = False

    def auto_select_all_occurrences(self):
        if self._is_auto_selecting or getattr(self, '_is_manual_multi_selecting', False):
            return

        data = SettingsModel().read_settings() or {}
        if data.get('highlight_all_occurrences', True):
            cursor = self.textCursor()
            if cursor.hasSelection():
                # Avoid selecting just empty spaces
                text = cursor.selectedText()
                if text and '\u2029' not in text and text.strip():
                    self._is_auto_selecting = True
                    self.select_all_occurrences()
                    self._is_auto_selecting = False
            else:
                if self.multi_cursor_manager.has_cursors() and getattr(self.multi_cursor_manager, 'is_auto_populated', False):
                    self.multi_cursor_manager.clear()
                    self.highlight_current_line()

    # Clear multi-cursor selections on standard clipboard and undo/redo operations
    def undo(self):
        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()
        self._is_undo_redo = True
        super(inputClass, self).undo()
        self._is_undo_redo = False

    def redo(self):
        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()
        self._is_undo_redo = True
        super(inputClass, self).redo()
        self._is_undo_redo = False

    def cut(self):
        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()
            self.highlight_current_line()
        super(inputClass, self).cut()

    def copy(self):
        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()
            self.highlight_current_line()
        super(inputClass, self).copy()

    def paste(self):
        if self.multi_cursor_manager.has_cursors():
            self.multi_cursor_manager.clear()
            self.highlight_current_line()
        super(inputClass, self).paste()
