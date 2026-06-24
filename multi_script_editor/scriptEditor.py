import os
import sys
import traceback
import webbrowser
from functools import partial

# Set preferred binding
if not os.environ.get("QT_PREFERRED_BINDING"):
    os.environ["QT_PREFERRED_BINDING"] = os.pathsep.join(["PySide2", "PySide6", "PyQt5", "PySide", "PyQt4"])
# Disable High Dpi Scaling in PySide6
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

mse_version = "5.1.0"

import managers
import sessionManager
import settingsManager
import vendor.Qt
from icons import *
from vendor.help import get_help
import ast
import re

from vendor.Qt.QtCore import QCoreApplication, QPoint, QSize, Qt, QTimer
from vendor.Qt.QtGui import QColor, QIcon, QKeySequence, QPalette, QTextCursor
from vendor.Qt.QtWidgets import QAction, QApplication, QFileDialog, QFontDialog, QMainWindow, QShortcut, QStyle, QSplitter, QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QMenu
from widgets import about, findWidget, outputWidget, shortcuts, tabWidget, themeEditor
from widgets import scriptEditor_UIs as ui
from widgets.pythonSyntax import design


def parse_outline(code):
    try:
        tree = ast.parse(code)
    except:
        return parse_outline_regex(code)

    symbols = []

    class OutlineVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            symbols.append({
                'name': "class {0}".format(node.name),
                'line': node.lineno,
                'indent': 0,
                'type': 'class'
            })
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            symbols.append({
                'name': "def {0}()".format(node.name),
                'line': node.lineno,
                'indent': 1,
                'type': 'function'
            })

    OutlineVisitor().visit(tree)
    symbols.sort(key=lambda x: x['line'])
    return symbols


def parse_outline_regex(code):
    symbols = []
    lines = code.split('\n')
    for i, line in enumerate(lines):
        line_num = i + 1
        class_match = re.match(r'^(\s*)class\s+(\w+)', line)
        if class_match:
            indent = len(class_match.group(1)) // 4
            name = class_match.group(2)
            symbols.append({
                'name': "class {0}".format(name),
                'line': line_num,
                'indent': indent,
                'type': 'class'
            })
            continue
        def_match = re.match(r'^(\s*)def\s+(\w+)', line)
        if def_match:
            indent = len(def_match.group(1)) // 4
            name = def_match.group(2)
            symbols.append({
                'name': "def {0}()".format(name),
                'line': line_num,
                'indent': indent,
                'type': 'function'
            })
    return symbols


class scriptEditorClass(QMainWindow, ui.Ui_scriptEditor):
    def __init__(self, parent=None):
        super(scriptEditorClass, self).__init__(parent)
        # ui
        py_ver = sys.version.split(' ')[0]
        self.ver = '{0} · Python-{1} · {2}-{3}'.format(
            mse_version, py_ver, vendor.Qt.__binding__, vendor.Qt.__binding_version__
        )
        self.setupUi(self)
        self.icon_path = os.path.dirname(__file__)
        window_icon = QIcon(icons["pw"])
        self.setWindowIcon(QIcon(window_icon))

        self.setWindowTitle('Multi Script Editor v%s' % self.ver)
        self.setObjectName('cw_scriptEditor')
        # widgets
        self.out = outputWidget.outputClass()
        self.out_ly.addWidget(self.out)
        self.tab = tabWidget.tabWidgetClass(self)

        # Horizontal QSplitter for outline sidebar and editor tabs
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.outline_panel = QWidget()
        self.outline_ly = QVBoxLayout(self.outline_panel)
        self.outline_ly.setContentsMargins(0, 0, 0, 0)
        self.outline_title = QLabel("Outline")
        self.outline_title.setStyleSheet("font-weight: bold; padding: 4px; color: #fff; background-color: #333;")
        self.outline_list = QListWidget()
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
        self.s = settingsManager.scriptEditorClass()
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
        self.session = sessionManager.sessionManagerClass()
        self.execAll_act.setIcon(QIcon(icons['all']))
        self.execLine_act.setIcon(QIcon(icons['line']))
        self.execSel_act.setIcon(QIcon(icons['sel']))
        self.clearHistory_act.setIcon(QIcon(icons['clear']))
        self.toolBar.setIconSize(QSize(32, 32))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setStyleSheet("QMenu {icon-size: 20px;}")

        # connects
        self.load_act.triggered.connect(self.loadScript)
        self.load_act.setIcon(QIcon(icons['open']))
        self.load_act.setShortcut("Ctrl+O")
        self.save_act.triggered.connect(self.saveScript)
        self.save_act.setIcon(QIcon(icons['save']))
        self.save_act.setShortcut("Ctrl+S")

        self.recent_files_menu = QMenu("Recent Files", self)
        self.recent_files_menu.setIcon(QIcon(icons["file_recent"]))
        self.file_menu.insertMenu(self.saveSeccion_act, self.recent_files_menu)
        self.updateRecentFilesMenu()

        self.saveSeccion_act.triggered.connect(lambda: self.saveSession(True))
        self.saveSeccion_act.setIcon(QIcon(icons['save']))
        self.saveSeccion_act.setShortcut("Ctrl+Shift+S")
        self.exit_act.triggered.connect(self.close)
        self.tabToSpaces_act.triggered.connect(self.tabsToSpaces)
        self.quit_act.triggered.connect(self.close)
        self.quit_act.setShortcut("Ctrl+Q")
        self.quit_act.setIcon(QIcon(icons['quit']))
        self.quit_act.setShortcut("Ctrl+Q")

        self.duplicateLine_act.setShortcut('Ctrl+Shift+D')
        self.duplicateLine_act.setShortcutContext(Qt.WidgetShortcut)
        self.duplicateLine_act.setIcon(QIcon(icons['duplicate_line']))
        self.deleteLine_act.setShortcut('Ctrl+D')
        self.deleteLine_act.setShortcutContext(Qt.WidgetShortcut)
        self.deleteLine_act.setIcon(QIcon(icons['delete_line']))

        self.set_font_act.triggered.connect(self.choose_font)
        self.set_font_act.setIcon(QIcon(icons['font']))

        self.settingsFile_act.triggered.connect(self.openSettingsFile)
        self.settingsFile_act.setIcon(QIcon(icons['settings']))

        self.theme_menu.setIcon(QIcon(icons['theme']))

        self.donate_act.triggered.connect(lambda: self.openLink('donate'))
        self.openManual_act.triggered.connect(lambda: self.openLink('manual'))
        self.openManual_act.setIcon(QIcon(icons['github']))

        self.python_act.triggered.connect(lambda: self.openLink('python{0}'.format(sys.version_info.major)))
        self.python_act.setIcon(QIcon(icons['python']))

        self.houdini_hou_act.triggered.connect(lambda: self.openLink('houdini_hou'))
        self.houdini_hou_act.setIcon(QIcon(icons['houdini']))
        self.houdini_envs_act.triggered.connect(lambda: self.openLink('houdini_envs'))
        self.houdini_envs_act.setIcon(QIcon(icons['houdini']))
        self.maya_cmds_act.triggered.connect(lambda: self.openLink('maya_cmds'))
        self.maya_cmds_act.setIcon(QIcon(icons['maya']))
        self.nuke_dev_guide_act.triggered.connect(lambda: self.openLink('nuke_dev_guide'))
        self.nuke_dev_guide_act.setIcon(QIcon(icons['nuke']))

        self.qt_docs_act.triggered.connect(lambda: self.openLink('qt_docs'))
        self.qt_docs_act.setIcon(QIcon(icons['qt']))
        self.qt_modules_act.triggered.connect(lambda: self.openLink('qt_modules'))
        self.qt_modules_act.setIcon(QIcon(icons['qt']))

        self.about_act.triggered.connect(self.about)
        self.about_act.setIcon(QIcon(icons['about']))
        self.help_act.setIcon(QIcon(icons['sel']))
        self.shortcuts_act.triggered.connect(self.shortcuts)
        self.shortcuts_act.setIcon(QIcon(icons['shortcut']))
        self.printHelp_act.triggered.connect(self.mse_help)
        self.printHelp_act.setIcon(QIcon(icons['print_help']))
        # editor
        # c = Qt.WindowShortcut
        self.undo_act.triggered.connect(self.tab.undo)
        self.undo_act.setShortcut('Ctrl+Z')
        self.undo_act.setShortcutContext(Qt.WidgetShortcut)
        self.undo_act.setIcon(QIcon(icons['undo']))

        self.redo_act.triggered.connect(self.tab.redo)
        self.redo_act.setShortcut('Ctrl+Y')
        self.redo_act.setShortcutContext(Qt.WidgetShortcut)
        self.redo_act.setIcon(QIcon(icons['redo']))

        self.copy_act.triggered.connect(self.tab.copy)
        self.copy_act.setShortcut('Ctrl+C')
        self.copy_act.setShortcutContext(Qt.WidgetShortcut)
        self.copy_act.setIcon(QIcon(icons['copy']))

        self.cut_act.triggered.connect(self.tab.cut)
        self.cut_act.setShortcut('Ctrl+X')
        self.cut_act.setShortcutContext(Qt.WidgetShortcut)
        self.cut_act.setIcon(QIcon(icons['cut']))

        self.paste_act.triggered.connect(self.tab.paste)
        self.paste_act.setShortcut('Ctrl+V')
        self.paste_act.setShortcutContext(Qt.WidgetShortcut)
        self.paste_act.setIcon(QIcon(icons['paste']))

        self.find_act.triggered.connect(self.findWidget)
        self.find_act.setShortcut('Ctrl+F')
        self.find_act.setShortcutContext(Qt.WindowShortcut)
        self.find_act.setIcon(QIcon(icons['replace']))

        self.tabToSpaces_act.setIcon(QIcon(icons['tabs_to_spaces']))

        self.print_command_act.setCheckable(True)

        self.clear_exec_act.triggered.connect(self.show_clear_exec)
        self.clear_exec_act.setShortcut('Ctrl+Alt+C')
        self.clear_exec_act.setShortcutContext(Qt.WindowShortcut)
        self.clear_exec_act.setCheckable(True)

        self.whitespace_act.triggered.connect(self.render_whitespace)
        self.whitespace_act.setShortcut('Ctrl+Shift+W')
        self.whitespace_act.setShortcutContext(Qt.WindowShortcut)
        self.whitespace_act.setCheckable(True)

        self.out_wordWrap_act.triggered.connect(self.out.wordWrap)
        self.out_wordWrap_act.setShortcut('Ctrl+Alt+W')
        self.out_wordWrap_act.setShortcutContext(Qt.WindowShortcut)
        self.out_wordWrap_act.setCheckable(True)

        self.wordWrap_act.triggered.connect(self.tab.wordWrap)
        self.wordWrap_act.setShortcut('Alt+W')
        self.wordWrap_act.setShortcutContext(Qt.WindowShortcut)
        self.wordWrap_act.setCheckable(True)

        self.moveLineUp_act.triggered.connect(self.tab.move_line_up)
        self.moveLineUp_act.setShortcut('Alt+Up')
        self.moveLineUp_act.setShortcutContext(Qt.WidgetShortcut)
        self.moveLineUp_act.setIcon(QIcon(icons["move_line_up"]))

        self.moveLineDown_act.triggered.connect(self.tab.move_line_down)
        self.moveLineDown_act.setShortcut('Alt+Down')
        self.moveLineDown_act.setShortcutContext(Qt.WidgetShortcut)
        self.moveLineDown_act.setIcon(QIcon(icons["move_line_down"]))

        self.comment_cat.triggered.connect(self.tab.comment)
        self.comment_cat.setShortcut('Alt+C')
        self.comment_cat.setShortcutContext(Qt.WidgetShortcut)
        self.comment_cat.setIcon(QIcon(icons['comment']))

        self.selectNextOccurrence_act.triggered.connect(self.tab.selectNextOccurrence)
        self.selectNextOccurrence_act.setShortcut('Ctrl+Alt+D')
        self.selectNextOccurrence_act.setShortcutContext(Qt.WindowShortcut)
        self.selectNextOccurrence_act.setIcon(QIcon(icons["replace"]))

        self.selectAllOccurrences_act.triggered.connect(self.tab.selectAllOccurrences)
        self.selectAllOccurrences_act.setShortcut('Ctrl+Shift+Alt+D')
        self.selectAllOccurrences_act.setShortcutContext(Qt.WindowShortcut)
        self.selectAllOccurrences_act.setIcon(QIcon(icons["replace"]))

        self.always_ontop_act.triggered.connect(self.always_ontop)
        self.always_ontop_act.setShortcutContext(Qt.WidgetShortcut)
        self.always_ontop_act.setCheckable(True)

        dir_f = partial(self.function_cmd, 'dir')
        self.dir_act.triggered.connect(dir_f)
        self.dir_act.setShortcut('Alt+D')
        self.dir_act.setIcon(QIcon(icons['sel']))
        self.dir_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+d'), self, dir_f)

        help_f = partial(self.function_cmd, 'help')
        self.help_act.triggered.connect(help_f)
        self.help_act.setShortcut('Alt+H')
        self.help_act.setIcon(QIcon(icons['sel']))
        self.help_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+h'), self, help_f)

        print_f = partial(self.function_cmd, "print")
        self.print_act.triggered.connect(print_f)
        self.print_act.setShortcut("Alt+e")
        self.print_act.setIcon(QIcon(icons["sel"]))
        self.print_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence("Alt+e"), self, print_f)

        type_f = partial(self.function_cmd, 'type')
        self.type_act.triggered.connect(type_f)
        self.type_act.setShortcut('Alt+T')
        self.type_act.setIcon(QIcon(icons['sel']))
        self.type_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+t'), self, type_f)

        self.quick_help_act.triggered.connect(self.get_word_help)
        self.quick_help_act.setShortcut('Alt+Q')
        self.quick_help_act.setIcon(QIcon(icons['help']))
        self.quick_help_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('F1'), self, self.get_word_help)
        QShortcut(QKeySequence('Alt+Q'), self, self.get_word_help)

        self.fillThemeMenu()

        # shortcuts
        if managers.context == 'nuke':
            import nuke

            if nuke.NUKE_VERSION_MAJOR > 8:
                self.execSel_act.setShortcut('Ctrl+Return')
                self.execSel_act.setShortcutContext(Qt.ApplicationShortcut)

        self.execSel_act.triggered.connect(self.executeSelected)
        self.execSel_act.setShortcut('Ctrl+Return')
        self.execSel_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)

        QShortcut(QKeySequence('Ctrl+Enter'), self, self.executeSelected)

        self.execAll_act.triggered.connect(self.executeAll)
        self.execAll_act.setShortcut('Alt+Return')
        self.execAll_act.setShortcutContext(Qt.ApplicationShortcut)

        QShortcut(QKeySequence('Alt+Enter'), self, self.executeAll)

        self.execLine_act.setShortcut('Ctrl+Shift+Return')
        self.execLine_act.triggered.connect(self.executeLine)
        self.execLine_act.setShortcutContext(Qt.ApplicationShortcut)

        QShortcut(QKeySequence('Ctrl+Shift+Enter'), self, self.executeLine)

        self.clearHistory_act.triggered.connect(self.clearHistory)
        self.clearHistory_act.setShortcut('Ctrl+Shift+C')

        # hide
        self.donate_act.setVisible(False)

        # Create status bar
        self.statusBar()

        # Outline toggle setup
        self.showOutline_act.setShortcut("Ctrl+Shift+O")
        self.showOutline_act.triggered.connect(self.toggleOutline)

        self.outline_timer = QTimer(self)
        self.outline_timer.setSingleShot(True)
        self.outline_timer.timeout.connect(self._updateOutlineNow)

        # Sessions Submenu in File menu
        self.sessions_menu = QMenu("Sessions", self)
        self.sessions_menu.setIcon(QIcon(icons['open']))
        self.file_menu.insertMenu(self.saveSeccion_act, self.sessions_menu)
        self.fillSessionsMenu()

        # Auto-Save timer (every 60 seconds)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autoSave)
        self.autosave_timer.start(60000)

        # Tab current change triggers outline refresh
        self.tab.currentChanged.connect(self.updateOutline)

        # start
        self.loadSession()
        self.loadSettings()
        self.setWindowStyle()
        self.tab.widget(0).edit.setFocus()
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
        accept_dialog = font_dialog.exec_()
        if accept_dialog:
            font = font_dialog.currentFont()
            # print("font", font)
            for index in range(0, self.tab.count()):
                self.tab.widget(index).edit.setFont(font)
            self.out.set_font(font)
            self.saveSettings()

    def clear_exec(self, exec_func):
        self.clearHistory()
        exec_func()

    def show_clear_exec(self):
        if self.clear_exec_act.isChecked():
            self.toolBar.setStyleSheet('QToolBar {background-color: indianred;}')
        else:
            self.toolBar.setStyleSheet('')

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
        data = self.s.readSettings()
        if not data:
            self.saveSettings()

    def closeEvent(self, event):
        self.saveSession()
        self.saveSettings()
        self.session.removeBackup()
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
        self.theme_menu.addAction(QAction('default', self, triggered=lambda: self.applyTheme('default')))
        data = self.s.readSettings()
        if data.get('colors'):
            for t in data.get('colors').keys():
                self.theme_menu.addAction(QAction(t, self, triggered=lambda x=t: self.applyTheme(x)))

    def applyTheme(self, name):
        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            o = self.out
            qss = design.editorStyle(name)
            # text color
            w.edit.applyHightLighter(name)
            o.applyHightLighter(name)
            # completer
            w.edit.completer.setStyleSheet(qss)
            # editor
            w.edit.setStyleSheet(qss)
            o.setStyleSheet(qss)
        s = self.s.readSettings()
        s['theme'] = name
        self.s.writeSettings(s)

    def setWindowStyle(self):
        if __name__ == '__main__':
            qss = os.path.join(os.path.dirname(__file__), 'style', 'style.css')
            if os.path.exists(qss):
                self.setStyleSheet(open(qss).read())
                self.setWindowIcon(QIcon(icons['pw']))

    def loadSession(self):
        sessions = self.session.readSession()

        self.tab.clear()
        active = 0
        if sessions:
            for i, s in enumerate(sessions):
                w = self.tab.addNewTab(s['name'], s['text'])
                if s['active']:
                    active = i
                w.setFontSize(s.get('size', None))
        else:
            self.tab.addNewTab()
        self.tab.setCurrentIndex(active)

    def saveSession(self, verbos=False):
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
        path = self.session.writeSession(tabs)
        if verbos:
            self.out.showMessage('>>> Session saved: %s' % path.replace('\\', '/'))

    def executeAll(self):
        allText = self.tab.getCurrentText()
        if self.print_command_act.isChecked():
            allText += '\n# Execute All'
        if allText:
            self.executeCommand(allText.strip())

    def executeLine(self):
        text = self.tab.getCurrentLine()
        if self.print_command_act.isChecked():
            text += '\n# Execute Line'
        if text:
            self.executeCommand(text)

    def executeSelected(self):
        text = self.tab.getCurrentSelectedText()
        if self.print_command_act.isChecked():
            text += '\n# Execute Selected'
        if text:
            self.executeCommand(text)

    def get_word_help(self):
        i = self.tab.currentIndex()
        text = self.tab.widget(i).edit.get_current_word()
        get_help(text)

    def function_cmd(self, function):
        i = self.tab.currentIndex()
        text = self.tab.widget(i).edit.function_cmd(function)
        if text:
            self.executeCommand(text)

    def updateNamespace(self, namespace):
        self.namespace.update(namespace)

    def executeCommand(self, cmd):
        if self.clear_exec_act.isChecked():
            self.clearHistory()
        self.out.showMessage(cmd)
        self.runCommand(cmd)

    def runCommand(self, command=None):
        if command:
            tmp_stdout = sys.stdout

            class stdoutProxy:
                def __init__(self, write_func):
                    self.write_func = write_func
                    self.skip = False

                def write(self, text):
                    if not self.skip:
                        stripped_text = text.rstrip('\n')
                        self.write_func(stripped_text)
                        QCoreApplication.processEvents()
                    self.skip = not self.skip

                def flush(self):
                    pass

            sys.stdout = stdoutProxy(self.out.showMessage)
            try:
                try:
                    result = eval(command, self.namespace, self.namespace)
                    if result is not None:
                        #if command.startswith("dir("):
                        #    result = "['" + "',\n'".join(result) + "']"
                        #    self.out.showMessage(result)
                        #else:
                        #    self.out.showMessage(repr(result))
                        self.out.showMessage(repr(result))
                except SyntaxError:
                    exec(command, self.namespace)
            except SystemExit:
                self.close()
            except:
                traceback_lines = traceback.format_exc().split('\n')
                for i in (3, 2, 1, -1):
                    traceback_lines.pop(i)
                self.out.showMessage('\n'.join(traceback_lines))
            finally:
                sys.stdout = tmp_stdout

    def clearHistory(self):
        self.out.setText('')

    def saveScript(self):
        text = self.tab.getCurrentText()
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getSaveFileName(self, 'Save script', d, "PY Files (*.py)")
        if path[0]:
            try:
                with open(path[0], 'w') as f:
                    f.write(text)
                self.addRecentFile(path[0])
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
                self.tab.addNewTab(os.path.basename(path[0]), text)
                self.addRecentFile(path[0])

    def addRecentFile(self, path):
        data = self.s.readSettings()
        recent = data.get('recent_files', [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:20]
        data['recent_files'] = recent
        self.s.writeSettings(data)
        self.updateRecentFilesMenu()

    def updateRecentFilesMenu(self):
        if not hasattr(self, 'recent_files_menu'): return
        self.recent_files_menu.clear()
        data = self.s.readSettings()
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
        data = self.s.readSettings()
        data['recent_files'] = []
        self.s.writeSettings(data)
        self.updateRecentFilesMenu()

    def openRecentFile(self, path):
        if os.path.exists(path):
            text = open(path).read()
            self.tab.addNewTab(os.path.basename(path), text)
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
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        self.show()

    def loadSettings(self):
        data = self.s.readSettings()

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
        fuzzy_autocomplete = data.get('fuzzy_autocomplete', False)
        show_docstrings = data.get('show_docstrings', False)

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
        if out_wrap:
            self.out_wordWrap_act.setChecked(out_wrap)
            self.out.wordWrap(out_wrap)
        if wrap:
            self.wordWrap_act.setChecked(wrap)
            self.tab.wordWrap(wrap)
        if clear_exec:
            self.clear_exec_act.setChecked(clear_exec)
            self.show_clear_exec()
        if echo_exec:
            self.print_command_act.setChecked(echo_exec)
        if always_ontop:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.always_ontop_act.setChecked(always_ontop)
        if show_whitespace:
            self.tab.render_whitespace(show_whitespace)
            self.out.render_whitespace(show_whitespace)
            self.whitespace_act.setChecked(show_whitespace)
        if font:
            self.tab.set_start_font(font)
            self.out.set_start_font(font)
        self.fuzzy_autocomplete_act.setChecked(fuzzy_autocomplete)
        self.show_docstrings_act.setChecked(show_docstrings)

        self.tab.wordWrap(not wrap)
        self.tab.wordWrap(wrap)

        f = self.out.font()
        f.setPointSize(outFontSize)
        self.out.setFont(f)

        show_outline = data.get('show_outline', False)
        self.showOutline_act.setChecked(show_outline)
        self.toggleOutline(show_outline)

    def saveSettings(self):
        settings = self.s.readSettings()
        geo = self.geometry()
        sGeo = [geo.x(), geo.y(), geo.width(), geo.height()]
        center = [geo.center().x(), geo.center().y()]
        size = max(8, self.out.font().pointSize())
        split_sizes = self.splitter.sizes()
        out_word_wrap = self.out_wordWrap_act.isChecked()
        clear_execute = self.clear_exec_act.isChecked()
        echo_execute = self.print_command_act.isChecked()
        word_wrap = self.wordWrap_act.isChecked()
        always_ontop = self.always_ontop_act.isChecked()
        show_whitespace = self.whitespace_act.isChecked()
        editor_font = self.tab.widget(0).edit.font()
        show_outline = self.showOutline_act.isChecked()
        fuzzy_autocomplete = self.fuzzy_autocomplete_act.isChecked()
        show_docstrings = self.show_docstrings_act.isChecked()

        font_data = dict()
        font_family = editor_font.family()
        font_size = editor_font.pointSize()
        font_italic = editor_font.italic()
        font_weight = editor_font.weight()
        font_data.update({"family": font_family})
        font_data.update({"pointSize": font_size})
        font_data.update({"weight": font_weight})
        font_data.update({"italic": font_italic})

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
            fuzzy_autocomplete=fuzzy_autocomplete,
            show_docstrings=show_docstrings,
        )
        settings.update(data)
        self.s.writeSettings(settings)

    def openSettingsFile(self):
        path = settingsManager.userPrefFolder()
        self.out.showMessage('>>> Settings folder: %s' % path.replace('\\', '/'))

        if os.path.exists(path):
            self.openFolder(path)
        else:
            self.out.showMessage('>>> Not created!')

    def openThemeEditor(self):
        self.dial = themeEditor.themeEditorClass(self, self.tab.desk)
        self.dial.exec_()
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

    def openLink(self, name):
        from style.links import links

        webbrowser.open(links[name])

    def about(self):
        dial = about.aboutClass(self)
        dial.exec_()

    def shortcuts(self):
        dial = shortcuts.shortcutsClass(self)
        dial.exec_()

    def findWidget(self):
        w = findWidget.findWidgetClass(self.out)
        w.searchSignal.connect(self.tab.search)
        w.replaceSignal.connect(self.tab.replace)
        w.replaceAllSignal.connect(self.tab.replaceAll)
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

    def updateOutline(self):
        if not hasattr(self, 'showOutline_act') or not self.showOutline_act.isChecked():
            return
        self.outline_timer.start(500)

    def _updateOutlineNow(self):
        if not hasattr(self, 'showOutline_act') or not self.showOutline_act.isChecked():
            return
        self.outline_list.clear()
        edit = self.tab.current()
        if not edit:
            return
        code = edit.toPlainText()
        symbols = parse_outline(code)
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
        self.session.writeBackup(tabs)

    def fillSessionsMenu(self):
        self.sessions_menu.clear()

        save_act = QAction("Save Current Session As...", self)
        save_act.setIcon(QIcon(icons['save']))
        save_act.triggered.connect(self.saveNamedSession)
        self.sessions_menu.addAction(save_act)

        restore_backup_act = QAction("Restore Crash Backup", self)
        restore_backup_act.triggered.connect(self.restoreBackupSession)
        if not self.session.backupExists():
            restore_backup_act.setEnabled(False)
        self.sessions_menu.addAction(restore_backup_act)

        self.delete_session_menu = QMenu("Delete Session", self)
        self.delete_session_menu.setIcon(QIcon(icons["clear"]))
        self.sessions_menu.addMenu(self.delete_session_menu)

        self.sessions_menu.addSeparator()

        names = self.session.listNamedSessions()
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
                if managers.context == 'hou':
                    size = self.tab.widget(item).edit.fs
                else:
                    size = self.tab.widget(item).edit.font().pointSize()
                tab = {'name': name_tab, 'text': text, 'active': item == index, 'size': size}
                tabs.append(tab)
            self.session.writeNamedSession(name, tabs)
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
            sessions = self.session.readNamedSession(name)
            self.tab.clear()
            active = 0
            if sessions:
                for i, s in enumerate(sessions):
                    w = self.tab.addNewTab(s['name'], s['text'])
                    if s['active']:
                        active = i
                    w.setFontSize(s.get('size', None))
            else:
                self.tab.addNewTab()
            self.tab.setCurrentIndex(active)
            self.out.showMessage(">>> Loaded named session '{0}'.".format(name))

    def deleteNamedSession(self, name):
        res = QMessageBox.question(
            self,
            "Delete Session",
            "Are you sure you want to delete session '{0}'?".format(name),
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self.session.deleteNamedSession(name)
            self.out.showMessage(">>> Deleted named session '{0}'.".format(name))
            self.fillSessionsMenu()

    def restoreBackupSession(self):
        if self.session.backupExists():
            sessions = self.session.readBackup()
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
    w = scriptEditorClass()
    w.show()
    app.exec_()


if __name__ == '__main__':
    app = QApplication([])
    w = scriptEditorClass()
    w.show()
    app.exec_()
    # show()
