import os
import sys
import webbrowser
from functools import partial

# Set preferred binding
if not os.environ.get("QT_PREFERRED_BINDING"):
    os.environ["QT_PREFERRED_BINDING"] = os.pathsep.join(["PySide2", "PySide6", "PyQt5", "PySide", "PyQt4"])
# Disable High Dpi Scaling in PySide6
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

mse_version = "6.0.0"

import managers
from core.execution_manager import ExecutionManager
from presenters.main_presenter import MainPresenter
import vendor.Qt
from icons import *
from vendor.help import get_help
import ast
import re

from vendor.Qt.QtCore import QCoreApplication, QPoint, QSize, Qt, QTimer, Signal
from vendor.Qt.QtGui import QColor, QFont, QIcon, QKeySequence, QPalette, QTextCursor
from vendor.Qt.QtWidgets import QAction, QApplication, QFileDialog, QFontDialog, QMainWindow, QShortcut, QStyle, QSplitter, QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QMenu
from widgets import about, findWidget, outputWidget, shortcuts, tabWidget, themeEditor
from widgets import scriptEditor_UIs as ui
from widgets.pythonSyntax import design


class scriptEditorClass(QMainWindow, ui.Ui_scriptEditor):
    execute_command_requested = Signal(str, bool, bool)
    update_outline_requested = Signal(str)
    save_settings_requested = Signal(dict)
    load_settings_requested = Signal()

    def __init__(self, parent=None):
        super(scriptEditorClass, self).__init__(parent)
        # ui
        py_ver = sys.version.split(' ')[0]
        self.ver = f"{mse_version} · Python-{py_ver} · {vendor.Qt.__binding__}-{vendor.Qt.__binding_version__}"
        self.setupUi(self)
        self.icon_path = os.path.dirname(__file__)
        window_icon = QIcon(icons["pw"])
        self.setWindowIcon(QIcon(window_icon))
        self.setWindowTitle('Multi Script Editor v%s' % self.ver)
        self.setObjectName('pw_scriptEditor')
        # widgets
        self.out = outputWidget.outputClass()
        self.out_ly.addWidget(self.out)
        self.tab = tabWidget.tabWidgetClass(self)
        self.tab.session_save_requested.connect(self.saveSession)
        self.tab.execute_selected_requested.connect(self.executeSelected)

        # Horizontal QSplitter for outline sidebar and editor tabs
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.outline_panel = QWidget()
        self.outline_ly = QVBoxLayout(self.outline_panel)
        self.outline_ly.setContentsMargins(0, 0, 0, 0)
        self.outline_title = QLabel("Outline")
        self.outline_title.setStyleSheet("font-weight: bold; padding: 4px;")
        self.outline_list = QListWidget()
        self.outline_list.setObjectName("outlineList")
        self.outline_list.itemClicked.connect(self.outlineItemClicked)
        self.outline_ly.addWidget(self.outline_title)
        self.outline_ly.addWidget(self.outline_list)

        self.horizontal_splitter.addWidget(self.outline_panel)
        self.horizontal_splitter.addWidget(self.tab)
        self.in_ly.addWidget(self.horizontal_splitter)
        self.horizontal_splitter.setSizes([0, 800])  # Start with outline panel collapsed

        for m in self.file_menu, self.tools_menu, self.options_menu, self.run_menu, self.help_menu:
            m.setWindowTitle('MSE {0}'.format(self.ver))
        # variables
        self._current_settings = {}
        self.namespace = __import__('__main__').__dict__
        self.dial = None

        self.updateNamespace(
            {
                'self_main': self,
                'self_version': self.ver,
                'self_output': self.out,
                'self_help': self.mse_help,
                'self_context': managers.context,
            }
        )
        from widgets.main_window_builder import ScriptEditorUIBuilder
        ScriptEditorUIBuilder.setup_ui(self)

        # Auto-Save timer (every 60 seconds)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autoSave)
        self.autosave_timer.start(60000)

        # Tab current change triggers outline refresh
        self.tab.currentChanged.connect(self.updateOutline)

        # start
        self._exec_manager = ExecutionManager()
        self._presenter = MainPresenter(self, self._exec_manager)
        self.fillSessionsMenu()
        self.loadSession()
        if self.tab.count() > 0:
            QTimer.singleShot(100, lambda: self.tab.widget(self.tab.currentIndex()).edit.setFocus() if self.tab.widget(self.tab.currentIndex()) else None)
        self.loadSettings()
        self.fillThemeMenu()
        self.setWindowStyle()
        self.appContextMenu()
        self.addArgs()

    def render_whitespace(self, state):
        wrap_state = self.wordWrap_act.isChecked()
        out_wrap_state = self.out_wordWrap_act.isChecked()
        self.tab.render_whitespace(state)
        self.out.render_whitespace(state)
        self.tab.wordWrap(not wrap_state)
        self.out.wordWrap(not out_wrap_state)
        self.tab.wordWrap(wrap_state)
        self.out.wordWrap(out_wrap_state)

    def toggle_word_wrap(self):
        state = not self.wordWrap_act.isChecked()
        self.wordWrap_act.setChecked(state)
        self.tab.wordWrap(state)

    def choose_font(self):
        editor_font = self.tab.widget(0).edit.font()
        font_dialog = QFontDialog(self)
        font_dialog.setCurrentFont(editor_font)
        font_dialog.resize(self.width() * 0.8, self.height() * 0.7)
        if hasattr(font_dialog, 'exec'):
            accept_dialog = getattr(font_dialog, 'exec')()
        else:
            accept_dialog = font_dialog.exec_()

        if accept_dialog:
            font = font_dialog.currentFont()
            for index in range(0, self.tab.count()):
                self.tab.widget(index).edit.setFont(font)
            self.out.set_font(font)

            outline_font = QFont(font)
            if outline_font.pointSize() > 0:
                outline_font.setPointSize(max(1, outline_font.pointSize() - 1))
            elif outline_font.pixelSize() > 0:
                outline_font.setPixelSize(max(1, outline_font.pixelSize() - 1))
            self.outline_list.setFont(outline_font)
            self.saveSettings()

    def clear_exec(self, exec_func):
        self.clearHistory()
        exec_func()

    def show_clear_exec(self):
        if self.clear_exec_act.isChecked():
            self.toolBar.setStyleSheet('QToolBar {background-color: indianred;}')
        else:
            self.toolBar.setStyleSheet('QToolBar {}')

    def get_builtin_icon(self, icon=QStyle.SP_DialogOpenButton):
        builtin_icon = icon
        action_icon = self.style().standardIcon(builtin_icon)
        return action_icon

    def __del__(self):
        if hasattr(self, 'tab'):
            self.saveSession()

    def mse_help(self):
        src = os.path.join(os.path.dirname(__file__), 'helpText.txt')
        if os.path.exists(src):
            txt = open(src).read() % self.ver
        else:
            txt = '<h3>File not found: helpText.txt</h3><br>'
        old = self.out.toPlainText().replace('\n', '<br>')
        self.out.setHtml(old + txt)
        self.out.moveCursor(QTextCursor.End)
        self.out.ensureCursorVisible()

    def showEvent(self, event):
        data = self._current_settings
        if not data:
            self.saveSettings()

    def closeEvent(self, event):
        self.saveSession()
        self.saveSettings()
        if hasattr(self, '_presenter'):
            self._presenter.remove_backup()
        event.accept()

    def appContextMenu(self):
        if managers.context in managers.contextMenus:
            menu = managers.contextMenus[managers.context](self)
            self.menubar.insertMenu(self.menubar.actions()[0], menu)
            return menu

    def addArgs(self):
        if sys.argv:
            f = sys.argv[-1]
            if os.path.exists(f):
                if not os.path.basename(f) == os.path.basename(__file__):
                    if os.path.splitext(f)[-1] in ['.txt', '.py']:
                        self.out.showMessage(os.path.splitext(f)[-1])
                        self.out.showMessage('Open File: ' + f)
                        text = open(f).read()
                        self.tab.addNewTab(os.path.basename(f), text)

    def fillThemeMenu(self):
        self.theme_menu.clear()
        self.theme_menu.addAction(QAction('Edit...', self, triggered=self.openThemeEditor))
        self.theme_menu.addSeparator()
        current_theme = self._current_settings.get('theme', 'Multi Script Editor')
        for t in sorted(design.predefinedThemes.keys()):
            act = QAction(t, self, triggered=lambda checked=False, x=t: self.applyTheme(x))
            act.setCheckable(True)
            act.setChecked(t == current_theme)
            self.theme_menu.addAction(act)
        data = self._current_settings
        if data.get('colors'):
            added_separator = False
            for t in data.get('colors').keys():
                if t not in design.predefinedThemes:
                    if not added_separator:
                        self.theme_menu.addSeparator()
                        added_separator = True
                    act = QAction(t, self, triggered=lambda checked=False, x=t: self.applyTheme(x))
                    act.setCheckable(True)
                    act.setChecked(t == current_theme)
                    self.theme_menu.addAction(act)

    def applyTheme(self, name):
        qss = design.editorStyle(name)
        o = self.out
        o.applyHightLighter(name)
        o.setStyleSheet(qss)
        self.outline_list.setStyleSheet(qss)

        for act in self.theme_menu.actions():
            if act.isCheckable():
                act.setChecked(act.text() == name)

        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            w.edit.applyHightLighter(name)
            w.edit.completer.setStyleSheet(qss)
            w.edit.setStyleSheet(qss)
        s = self._current_settings
        s['theme'] = name
        self.save_settings_requested.emit(s)

    def setWindowStyle(self):
        if __name__ == '__main__':
            qss = os.path.join(os.path.dirname(__file__), 'style', 'style.css')
            if os.path.exists(qss):
                self.setStyleSheet(open(qss).read())
                self.setWindowIcon(QIcon(icons['pw']))

    def show_syntax_errors(self, errors):
        # Pass the errors to the active tab's input widget (for highlighting line numbers if needed)
        w = self.tab.currentWidget()
        if w and hasattr(w, 'edit'):
            w.edit.syntax_errors = errors
            if hasattr(w, 'lineNum'):
                w.lineNum.update()

        # Update Outline
        if hasattr(self, 'updateOutline'):
            self.updateOutline()

        # Update StatusBar
        if self.statusBar():
            if errors:
                first_err_line = list(errors.keys())[0]
                msg = errors[first_err_line]
                self.statusBar().showMessage("Syntax Error on line {0}: {1}".format(first_err_line, msg))
            else:
                self.statusBar().clearMessage()

    def getShortcut(self, action):
        settings = self._presenter.settings_model.load_settings()
        return settings.get('shortcuts', {}).get(action, None)

    def loadSession(self):
        sessions = self._presenter.get_session_tabs()
        self.tab.clear()
        active_index = -1
        if sessions:
            for i, s in enumerate(sessions):
                w = self.tab.addNewTab(s.get('name', 'tab'), s.get('text'), file_path=s.get('file_path'))
                if s.get('active'):
                    active_index = i
                if s.get('size'):
                    w.setFontSize(s.get('size'))
            if active_index != -1:
                self.tab.setCurrentIndex(active_index)
        if self.tab.count() == 0:
            self.tab.addNewTab()

    def saveSession(self, verbos=False):
        if not hasattr(self, '_presenter'):
            return
        tabs = []
        index = self.tab.currentIndex()
        for item in range(self.tab.count()):
            widget = self.tab.widget(item)
            if not widget:
                continue
            name = self.tab.tabText(item)
            text = self.tab.getTabText(item)
            if managers.context == 'hou':
                size = widget.edit.fs
            else:
                size = widget.edit.font().pointSize()
            tab = {'name': name, 'text': text, 'active': item == index, 'size': size, 'file_path': getattr(widget, 'file_path', None)}
            tabs.append(tab)
        path = self._presenter.save_session(tabs)
        if verbos:
            self.out.showMessage('>>> Session saved: %s' % path.replace('\\', '/'))

    def closeAllTabsWithConfirm(self):
        res = QMessageBox.question(
            self,
            "Close All Tabs",
            "Are you sure you want to close all tabs?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self.tab.clear()
            self.tab.addNewTab()

    def executeAll(self):
        allText = self.tab.getCurrentText()
        if self.print_command_act.isChecked():
            allText += '\n# Execute All'
        if allText:
            self.execute_command_requested.emit(allText.strip(), self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def executeLine(self):
        text = self.tab.getCurrentLine()
        if self.print_command_act.isChecked():
            text += '\n# Execute Line'
        if text:
            self.execute_command_requested.emit(text, self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def executeSelected(self):
        text = self.tab.getCurrentSelectedText()
        if self.print_command_act.isChecked():
            text += '\n# Execute Selected'
        if text:
            self.execute_command_requested.emit(text, self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def get_word_help(self):
        i = self.tab.currentIndex()
        text = self.tab.widget(i).edit.get_current_word()
        get_help(text)

    def function_cmd(self, function):
        i = self.tab.currentIndex()
        text = self.tab.widget(i).edit.function_cmd(function)
        if text:
            self.execute_command_requested.emit(text, self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def updateNamespace(self, namespace):
        self.namespace.update(namespace)

    def get_namespace(self):
        return self.namespace

    def clear_output(self):
        self.clearHistory()

    def append_output_message(self, text):
        self.out.showMessage(text)

    def clearHistory(self):
        self.out.setText('')

    def saveScript(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        cont = self.tab.widget(index)
        text = self.tab.getCurrentText()

        # Check if the tab already has an associated file path
        if hasattr(cont, 'file_path') and cont.file_path and os.path.exists(os.path.dirname(cont.file_path)):
            try:
                with open(cont.file_path, 'w') as f:
                    f.write(text)
                self.out.showMessage('Saved to: %s' % cont.file_path)
            except Exception as e:
                self.out.showMessage('Error saving file: %s (%s)' % (cont.file_path, str(e)))
            return

        # Otherwise do Save As
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getSaveFileName(self, 'Save script', d, "PY Files (*.py)")
        if path[0]:
            try:
                with open(path[0], 'w') as f:
                    f.write(text)
                self.addRecentFile(path[0])
                if hasattr(cont, 'file_path'):
                    cont.file_path = path[0]
                self.tab.setTabText(index, os.path.basename(path[0]))
                self.out.showMessage('Saved to: %s' % path[0])
            except:
                self.out.showMessage('Error save file; %s' % path[0])

    def loadScript(self):
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getOpenFileName(self, 'Open script', d, "PY Files (*.py)")
        if path[0]:
            if os.path.exists(path[0]):
                text = open(path[0]).read()
                self.tab.addNewTab(os.path.basename(path[0]), text, file_path=path[0])
                self.addRecentFile(path[0])

    def addRecentFile(self, path):
        data = self._current_settings
        recent = data.get('recent_files', [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:20]
        data['recent_files'] = recent
        self.save_settings_requested.emit(data)
        self.updateRecentFilesMenu()

    def updateRecentFilesMenu(self):
        if not hasattr(self, 'recent_files_menu'): return
        self.recent_files_menu.clear()
        data = self._current_settings
        recent = data.get('recent_files', [])
        if not recent:
            a = self.recent_files_menu.addAction("No recent files")
            a.setEnabled(False)
            return
        for path in recent:
            if os.path.exists(path):
                act = QAction(os.path.basename(path), self)
                act.setToolTip(path)
                act.triggered.connect(partial(self.openRecentFile, path))
                self.recent_files_menu.addAction(act)
        self.recent_files_menu.addSeparator()
        clear_act = QAction("Clear Recent", self)
        clear_act.triggered.connect(self.clearRecentFiles)
        self.recent_files_menu.addAction(clear_act)

    def clearRecentFiles(self):
        data = self._current_settings
        data['recent_files'] = []
        self.save_settings_requested.emit(data)
        self.updateRecentFilesMenu()

    def openRecentFile(self, path):
        if os.path.exists(path):
            text = open(path).read()
            self.tab.addNewTab(os.path.basename(path), text, file_path=path)
            self.addRecentFile(path)

    def tabsToSpaces(self):
        text = self.tab.getCurrentText()
        text = text.replace('\t', '    ')
        self.tab.setCurrentText(text)

    def insertText(self, text):
        self.tab.addToCurrent(text)

    def always_ontop(self):
        """Set the window to always be on top or turn off the feature."""
        state = self.always_ontop_act.isChecked()
        if state:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def apply_settings(self, settings):
        self._current_settings = settings
        self.loadSettings()

    def loadSettings(self):
        data = self._current_settings

        always_ontop = data.get('always_ontop', False)
        center = data.get('center', None)
        clear_exec = data.get('clear_execute', None)
        echo_exec = data.get('echo_execute', None)
        geo = data.get('geometry', None)
        out_wrap = data.get('out_wrap', None)
        outFontSize = data.get('outFontSize', 10)
        splitter = data.get('splitter', None)
        wrap = data.get('wrap', None)
        show_whitespace = data.get('show_whitespace', False)
        font = data.get('font', False)
        autocomplete = data.get('autocomplete', True)
        fuzzy_autocomplete = data.get('fuzzy_autocomplete', True)
        show_docstrings = data.get('show_docstrings', True)

        if geo:
            self.move(geo[0], geo[1])
            self.resize(geo[2], geo[3])
        if center:
            x, y = center
            geo = self.geometry()
            geo.moveCenter(QPoint(x, y))
            self.setGeometry(geo)
        if splitter:
            self.splitter.setSizes(splitter)
        if out_wrap is not None:
            self.out_wordWrap_act.setChecked(out_wrap)
            self.out.wordWrap(out_wrap)
        if wrap is not None:
            self.wordWrap_act.setChecked(wrap)
            self.tab.wordWrap(wrap)
        if clear_exec:
            self.clear_exec_act.setChecked(clear_exec)
            self.show_clear_exec()
        if echo_exec:
            self.print_command_act.setChecked(echo_exec)
        self.always_ontop_act.setChecked(always_ontop)
        if always_ontop:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        if show_whitespace is not None:
            self.tab.render_whitespace(show_whitespace)
            self.out.render_whitespace(show_whitespace)
            self.whitespace_act.setChecked(show_whitespace)
        if font:
            self.tab.set_start_font(font)
            self.out.set_start_font(font)

            outline_font = QFont(self.out.font())
            if outline_font.pointSize() > 0:
                outline_font.setPointSize(max(1, outline_font.pointSize() - 1))
            elif outline_font.pixelSize() > 0:
                outline_font.setPixelSize(max(1, outline_font.pixelSize() - 1))
            self.outline_list.setFont(outline_font)
        self.autocomplete_act.setChecked(autocomplete)
        self.fuzzy_autocomplete_act.setChecked(fuzzy_autocomplete)
        self.show_docstrings_act.setChecked(show_docstrings)

        f = self.out.font()
        f.setPointSize(outFontSize)
        self.out.setFont(f)

        show_outline = data.get('show_outline', False)
        self.showOutline_act.setChecked(show_outline)
        self.toggleOutline(show_outline)

        syntax_check = data.get('syntax_check', True)
        self.syntaxCheck_act.setChecked(syntax_check)
        self.toggleSyntaxCheck(syntax_check)

        output_bottom = data.get('output_bottom', False)
        self.outputBottom_act.setChecked(output_bottom)
        self.toggleOutputBottom(output_bottom)

        self.updateRecentFilesMenu()

        theme = data.get('theme', 'Multi Script Editor')
        if theme == 'default':
            theme = 'Multi Script Editor'
            self._current_settings['theme'] = theme
        self.applyTheme(theme)

    def saveSettings(self):
        settings = self._current_settings
        geo = self.geometry()
        sGeo = [geo.x(), geo.y(), geo.width(), geo.height()]
        center = [geo.center().x(), geo.center().y()]
        out_pt = self.out.font().pointSize()
        if out_pt == -1:
            if hasattr(self.out, 'fs'):
                out_pt = self.out.fs
            else:
                out_pt = self.out.font().pixelSize()
        size = max(8, out_pt)
        split_sizes = self.splitter.sizes()
        out_word_wrap = self.out_wordWrap_act.isChecked()
        clear_execute = self.clear_exec_act.isChecked()
        echo_execute = self.print_command_act.isChecked()
        word_wrap = self.wordWrap_act.isChecked()
        always_ontop = self.always_ontop_act.isChecked()
        show_whitespace = self.whitespace_act.isChecked()
        show_outline = self.showOutline_act.isChecked()
        syntax_check = self.syntaxCheck_act.isChecked()
        output_bottom = self.outputBottom_act.isChecked()
        autocomplete = self.autocomplete_act.isChecked()
        fuzzy_autocomplete = self.fuzzy_autocomplete_act.isChecked()
        show_docstrings = self.show_docstrings_act.isChecked()

        font_data = dict()
        if self.tab.count() > 0 and self.tab.widget(0) and hasattr(self.tab.widget(0), 'edit'):
            editor_font = self.tab.widget(0).edit.font()
            pt_size = editor_font.pointSize()
            if pt_size == -1:
                if hasattr(self.tab.widget(0).edit, 'fs'):
                    pt_size = self.tab.widget(0).edit.fs
                else:
                    pt_size = editor_font.pixelSize()

            font_data.update({
                "family": editor_font.family(),
                "pointSize": pt_size,
                "weight": editor_font.weight(),
                "italic": editor_font.italic()
            })
        else:
            font_data = settings.get('font', {})

        data = dict(
            geometry=sGeo,
            center=center,
            outFontSize=size,
            splitter=split_sizes,
            wrap=word_wrap,
            out_wrap=out_word_wrap,
            echo_execute=echo_execute,
            clear_execute=clear_execute,
            always_ontop=always_ontop,
            show_whitespace=show_whitespace,
            font=font_data,
            show_outline=show_outline,
            syntax_check=syntax_check,
            output_bottom=output_bottom,
            autocomplete=autocomplete,
            fuzzy_autocomplete=fuzzy_autocomplete,
            show_docstrings=show_docstrings,
        )
        settings.update(data)
        self.save_settings_requested.emit(settings)

    def openSettingsFile(self):
        from core.settings_model import SettingsModel
        path = SettingsModel()._get_user_pref_folder()
        self.out.showMessage('>>> Settings folder: %s' % path.replace('\\', '/'))

        if os.path.exists(path):
            self.openFolder(path)
        else:
            self.out.showMessage('>>> Not created!')

    def openThemeEditor(self):
        self.dial = themeEditor.themeEditorClass(self, self.tab.desk)
        getattr(self.dial, 'exec', self.dial.exec_)()
        self.fillThemeMenu()

    def moveEvent(self, event):
        self.adjustColmpeters()
        super(scriptEditorClass, self).moveEvent(event)

    def adjustColmpeters(self):
        for i in range(self.tab.count()):
            w = self.tab.widget(i).edit
            if w.completer.isVisible():
                w.moveCompleter()

    def resizeEvent(self, event):
        self.adjustColmpeters()
        super(scriptEditorClass, self).resizeEvent(event)

    def openLink(self, name, extra=""):
        from style.links import links

        webbrowser.open(f"{links[name]}{extra}")

    def openDocumentation(self):
        doc_path = os.path.join(os.path.dirname(__file__), 'docs', 'documentation.html')
        webbrowser.open('file://' + doc_path.replace('\\', '/'))

    def about(self):
        dial = about.aboutClass(self)
        dial.exec_()

    def shortcuts(self):
        dial = shortcuts.shortcutsClass(self)
        dial.exec_()

    def findWidget(self):
        focus_widget = QApplication.focusWidget()
        target = 'input'

        if focus_widget == self.out or self.out.isAncestorOf(focus_widget):
            target = 'output'

        if target == 'output':
            # Searching in log, center on editor (self.tab)
            center_widget = self.tab
        else:
            # Searching in editor, center on log (self.out)
            center_widget = self.out

        w = findWidget.findWidgetClass(self.out, center_widget)

        # Restore case sensitive state
        is_case_sensitive = self._current_settings.get('search_case_sensitive', False)
        w.case_cb.setChecked(is_case_sensitive)

        # Save case sensitive state when toggled
        def on_case_toggled(checked):
            self._current_settings['search_case_sensitive'] = checked
            self.saveSettings()

        w.case_cb.toggled.connect(on_case_toggled)

        if target == 'output':
            w.setReplaceEnabled(False)
            w.searchSignal.connect(self.out.search)
            w.setWindowTitle("Find in Log")
        else:
            w.setReplaceEnabled(True)
            w.searchSignal.connect(self.tab.search)
            w.replaceSignal.connect(self.tab.replace)
            w.replaceAllSignal.connect(self.tab.replaceAll)
            w.setWindowTitle("Find in Editor")

        w.show()
        w.activateWindow()

    def openFolder(self, path):
        if os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix':
            os.system('xdg-open "%s"' % path)
        elif os.name == 'os2':
            os.system('open "%s"' % path)

    # NEW FEATURES METHODS
    def toggleOutline(self, state):
        if state:
            self.horizontal_splitter.setSizes([200, 600])
            self.updateOutline()
        else:
            self.horizontal_splitter.setSizes([0, 800])

    def toggleOutputBottom(self, state=None):
        if state is None:
            state = self.outputBottom_act.isChecked()
        sizes = self.splitter.sizes()
        if state:
            self.splitter.insertWidget(0, self.verticalLayoutWidget_2)
            self.splitter.insertWidget(1, self.verticalLayoutWidget)
        else:
            self.splitter.insertWidget(0, self.verticalLayoutWidget)
            self.splitter.insertWidget(1, self.verticalLayoutWidget_2)

        if sum(sizes) > 0:
            self.splitter.setSizes(sizes[::-1])

    def toggleSyntaxCheck(self, state=None):
        if state is None:
            state = self.syntaxCheck_act.isChecked()
        self.statusBar().setVisible(state)

        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            if hasattr(w, 'edit'):
                w.edit.runLinter()

        if not state:
            self.statusBar().clearMessage()
    def updateOutline(self):
        if not hasattr(self, 'showOutline_act') or not self.showOutline_act.isChecked():
            return
        if hasattr(self, 'horizontal_splitter') and self.horizontal_splitter.sizes()[0] == 0:
            return
        self.outline_timer.start(500)

    def _updateOutlineNow(self):
        if not hasattr(self, 'showOutline_act') or not self.showOutline_act.isChecked():
            return
        if hasattr(self, 'horizontal_splitter') and self.horizontal_splitter.sizes()[0] == 0:
            return
        edit = self.tab.current()
        if not edit:
            return
        code = edit.toPlainText()
        self.update_outline_requested.emit(code)

    def set_outline_symbols(self, symbols):
        self.outline_list.clear()
        for sym in symbols:
            indent_spaces = "  " * sym['indent']
            item = QListWidgetItem("{0}{1}".format(indent_spaces, sym['name']))
            item.setData(Qt.UserRole, sym['line'])
            if sym['type'] == 'class':
                item.setForeground(QColor("#56B6C2"))
            else:
                item.setForeground(QColor("#E06C75"))
            self.outline_list.addItem(item)

    def outlineItemClicked(self, item):
        line = item.data(Qt.UserRole)
        if line:
            edit = self.tab.current()
            cursor = edit.textCursor()
            block = edit.document().findBlockByNumber(line - 1)
            cursor.setPosition(block.position())
            edit.setTextCursor(cursor)
            edit.setFocus()

    def autoSave(self):
        tabs = []
        index = self.tab.currentIndex()
        for item in range(self.tab.count()):
            name = self.tab.tabText(item)
            text = self.tab.getTabText(item)
            if managers.context == 'hou':
                size = self.tab.widget(item).edit.fs
            else:
                size = self.tab.widget(item).edit.font().pointSize()
            tab = {'name': name, 'text': text, 'active': item == index, 'size': size}
            tabs.append(tab)
        self._presenter.save_backup(tabs)

    def fillSessionsMenu(self):
        self.sessions_menu.clear()

        save_act = QAction("Save Current Session As...", self)
        save_act.setIcon(QIcon(icons['save']))
        save_act.triggered.connect(self.saveNamedSession)
        self.sessions_menu.addAction(save_act)

        restore_backup_act = QAction("Restore Crash Backup", self)
        restore_backup_act.setIcon(QIcon(icons['restore_backup']))
        restore_backup_act.triggered.connect(self.restoreBackupSession)
        if not self._presenter.backup_exists():
            restore_backup_act.setEnabled(False)
        self.sessions_menu.addAction(restore_backup_act)

        self.delete_session_menu = QMenu("Delete Session", self)
        self.delete_session_menu.setIcon(QIcon(icons["clear"]))
        self.sessions_menu.addMenu(self.delete_session_menu)

        self.sessions_menu.addSeparator()

        names = self._presenter.get_named_sessions()
        if names:
            for name in names:
                act = QAction(name, self)
                act.triggered.connect(lambda checked=False, n=name: self.loadNamedSession(n))
                self.sessions_menu.addAction(act)

                del_act = QAction(name, self)
                del_act.triggered.connect(lambda checked=False, n=name: self.deleteNamedSession(n))
                self.delete_session_menu.addAction(del_act)
        else:
            no_sessions_act = QAction("No saved sessions", self)
            no_sessions_act.setEnabled(False)
            self.sessions_menu.addAction(no_sessions_act)

            no_del_act = QAction("No saved sessions", self)
            no_del_act.setEnabled(False)
            self.delete_session_menu.addAction(no_del_act)

    def saveNamedSession(self):
        name, ok = QInputDialog.getText(self, "Save Named Session", "Enter session name:")
        if ok and name.strip():
            name = name.strip()
            tabs = []
            index = self.tab.currentIndex()
            for item in range(self.tab.count()):
                name_tab = self.tab.tabText(item)
                text = self.tab.getTabText(item)
                widget = self.tab.widget(item)
                if managers.context == 'hou':
                    size = widget.edit.fs
                else:
                    size = widget.edit.font().pointSize()
                tab = {'name': name_tab, 'text': text, 'active': item == index, 'size': size, 'file_path': getattr(widget, 'file_path', None)}
                tabs.append(tab)
            self._presenter.save_named_session(name, tabs)
            self.out.showMessage(">>> Named session '{0}' saved successfully.".format(name))
            self.fillSessionsMenu()

    def loadNamedSession(self, name):
        res = QMessageBox.question(
            self,
            "Load Session",
            "Loading session '{0}' will replace all current tabs. Do you want to proceed?".format(name),
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            sessions = self._presenter.get_named_session_tabs(name)
            self.tab.clear()
            if sessions:
                for i, s in enumerate(sessions):
                    w = self.tab.addNewTab(s.get('name', 'tab'), s.get('text'), file_path=s.get('file_path'))
                    if s.get('active'):
                        self.tab.setCurrentIndex(i)
                    w.setFontSize(s.get('size', None))
            if self.tab.count() == 0:
                self.tab.addNewTab()
            self.out.showMessage(">>> Loaded named session '{0}'.".format(name))

    def deleteNamedSession(self, name):
        res = QMessageBox.question(
            self,
            "Delete Session",
            "Are you sure you want to delete session '{0}'?".format(name),
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self._presenter.delete_named_session(name)
            self.out.showMessage(">>> Deleted named session '{0}'.".format(name))
            self.fillSessionsMenu()

    def restoreBackupSession(self):
        if self._presenter.backup_exists():
            sessions = self._presenter.get_backup_tabs()
            if sessions:
                self.tab.clear()
                active = 0
                for i, s in enumerate(sessions):
                    w = self.tab.addNewTab(s['name'], s['text'])
                    if s['active']:
                        active = i
                    w.setFontSize(s.get('size', None))
                self.tab.setCurrentIndex(active)
                self.out.showMessage("Crash backup restored successfully.")
            else:
                self.out.showMessage("Crash backup is empty or invalid.")
        else:
            self.out.showMessage("No crash backup found.")


try:
    from PySide2.QtCore import QTextCodec
    QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
except:
    try:
        from PySide.QtCore import QTextCodec
        QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
    except:
        pass


def show():
    app = QApplication.instance()
    if not app:
        app = QApplication()
    # Set the dark theme
    font_color = Qt.white
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, font_color)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, font_color)
    palette.setColor(QPalette.ToolTipText, font_color)
    palette.setColor(QPalette.Text, font_color)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, font_color)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    w = create_editor_instance()
    w.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()


def create_editor_instance(parent=None):
    w = scriptEditorClass(parent)
    return w

if __name__ == '__main__':
    show()
