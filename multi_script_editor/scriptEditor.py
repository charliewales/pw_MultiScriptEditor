import traceback
import sys
import webbrowser
import os
from functools import partial
from vendor.help import get_help
from vendor.Qt.QtCore import *
from vendor.Qt.QtGui import *
from vendor.Qt.QtWidgets import *
import sessionManager
import settingsManager
import managers
from widgets import scriptEditor_UIs as ui, tabWidget, outputWidget, about, shortcuts
from widgets.pythonSyntax import design
from widgets import themeEditor, findWidget
from icons import *

class scriptEditorClass(QMainWindow, ui.Ui_scriptEditor):
    def __init__(self, parent=None):
        super(scriptEditorClass, self).__init__(parent)
        # ui
        py_ver = sys.version.split(' ')[0]
        self.ver = '3.0.0 - Python {0}'.format(py_ver)
        self.setupUi(self)
        self.setWindowTitle('Multi Script Editor v%s' % self.ver)
        self.setObjectName('pw_scriptEditor')
        # widgets
        self.out = outputWidget.outputClass()
        self.out_ly.addWidget(self.out)
        self.tab = tabWidget.tabWidgetClass(self)
        self.in_ly.addWidget(self.tab)

        for m in self.file_menu, self.tools_menu, self.options_menu, self.run_menu, self.help_menu:
            m.setWindowTitle('MSE {0}'.format(self.ver))
        #variables
        self.s = settingsManager.scriptEditorClass()
        self.namespace = __import__('__main__').__dict__
        self.dial = None

        self.updateNamespace({'self_main':self,
                              'self_version':self.ver,
                              'self_output': self.out,
                              'self_help': self.mse_help,
                              'self_context':managers.context})
        self.session = sessionManager.sessionManagerClass()
        self.execAll_act.setIcon(QIcon(icons['all']))
        self.execLine_act.setIcon(QIcon(icons['line']))
        self.execSel_act.setIcon(QIcon(icons['sel']))
        self.clearHistory_act.setIcon(QIcon(icons['clear']))
        self.toolBar.setIconSize(QSize(32,32))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setStyleSheet("QMenu {icon-size: 20px;}")

        # connects
        self.load_act.triggered.connect(self.loadScript)
        self.load_act.setIcon(QIcon(icons['open']))
        self.load_act.setShortcut("Ctrl+O")
        self.save_act.triggered.connect(self.saveScript)
        self.save_act.setIcon(QIcon(icons['save']))
        self.save_act.setShortcut("Ctrl+S")
        self.saveSeccion_act.triggered.connect(lambda:self.saveSession(True))
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

        self.donate_act.triggered.connect(lambda :self.openLink('donate'))
        self.openManual_act.triggered.connect(lambda :self.openLink('manual'))
        self.openManual_act.setIcon(QIcon(icons['github']))

        self.python_act.triggered.connect(lambda :self.openLink('python{0}'.format(sys.version_info.major)))
        self.python_act.setIcon(QIcon(icons['python']))

        self.houdini_hou_act.triggered.connect(lambda :self.openLink('houdini_hou'))
        self.houdini_hou_act.setIcon(QIcon(icons['houdini']))
        self.houdini_envs_act.triggered.connect(lambda :self.openLink('houdini_envs'))
        self.houdini_envs_act.setIcon(QIcon(icons['houdini']))
        self.maya_cmds_act.triggered.connect(lambda :self.openLink('maya_cmds'))
        self.maya_cmds_act.setIcon(QIcon(icons['maya']))
        self.nuke_dev_guide_act.triggered.connect(lambda :self.openLink('nuke_dev_guide'))
        self.nuke_dev_guide_act.setIcon(QIcon(icons['nuke']))

        self.qt_docs_act.triggered.connect(lambda :self.openLink('qt_docs'))
        self.qt_docs_act.setIcon(QIcon(icons['qt']))
        self.qt_modules_act.triggered.connect(lambda :self.openLink('qt_modules'))
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

        self.comment_cat.triggered.connect(self.tab.comment)
        self.comment_cat.setShortcut('Alt+C')
        self.comment_cat.setShortcutContext(Qt.WidgetShortcut)
        self.comment_cat.setIcon(QIcon(icons['comment']))

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

        #shortcuts
        if managers.context == 'nuke':
            import nuke
            if nuke.NUKE_VERSION_MAJOR>8:
                self.execSel_act.setShortcut('Ctrl+Return')
                self.execSel_act.setShortcutContext(Qt.ApplicationShortcut)

        self.execSel_act.triggered.connect(self.executeSelected)
        self.execSel_act.setShortcut('Ctrl+Return')
        self.execSel_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)

        self.execAll_act.triggered.connect(self.executeAll)
        self.execAll_act.setShortcut('Alt+Return')
        self.execAll_act.setShortcutContext(Qt.ApplicationShortcut)

        self.execLine_act.setShortcut('Ctrl+Shift+Return')
        self.execLine_act.triggered.connect(self.executeLine)
        self.execLine_act.setShortcutContext(Qt.ApplicationShortcut)

        self.clearHistory_act.triggered.connect(self.clearHistory)
        self.clearHistory_act.setShortcut('Ctrl+Shift+C')

        # hide
        self.donate_act.setVisible(False)

        #start
        self.loadSession()
        self.loadSettings()
        self.setWindowStyle()
        self.tab.widget(0).edit.setFocus()
        self.appContextMenu()
        self.addArgs()

    def render_whitespace(self, state):
        wrap_state = self.wordWrap_act.isChecked()
        self.tab.wordWrap(not wrap_state)
        self.tab.render_whitespace(state)
        self.out.render_whitespace(state)
        self.tab.wordWrap(wrap_state)

    def choose_font(self):
        font_dialog = QFontDialog(self)
        font_dialog.resize(self.width()*.8, self.height()*0.6)
        font_dialog.exec_()
        font = font_dialog.currentFont()
        if font:
            self.tab.set_font(font)
            self.out.setFont(font)

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
        self.saveSession()

    def mse_help(self):
        src = os.path.join(os.path.dirname(__file__), 'helpText.txt')
        if os.path.exists(src):
            txt = open(src).read() % self.ver
        else:
            txt = '<h3>File not found: helpText.txt</h3><br>'
        old = self.out.toPlainText().replace('\n', '<br>')
        self.out.setHtml(old+txt)
        self.out.moveCursor(QTextCursor.End)
        self.out.ensureCursorVisible()

    def closeEvent(self, event):
        self.saveSession()
        self.saveSettings()
        self.close()
        if __name__ == '__main__':
            sys.exit()

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
                        self.out.showMessage( os.path.splitext(f)[-1])
                        self.out.showMessage('Open File: '+f)
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
            #completer
            w.edit.completer.setStyleSheet(qss)
            #editor
            w.edit.setStyleSheet(qss)
            o.setStyleSheet(qss)
        s = self.s.readSettings()
        s['theme'] = name
        self.s.writeSettings(s)

    def setWindowStyle(self):
        if __name__ == '__main__':
            qss = os.path.join(os.path.dirname(__file__),'style', 'style.css')
            if os.path.exists(qss):
                self.setStyleSheet(open(qss).read())
                self.setWindowIcon(QIcon(icons['pw']))

    def loadSession(self):
        sessions = self.session.readSession()
        self.tab.clear()
        active = 0
        if sessions:
            for i, s in enumerate(sessions):
                w= self.tab.addNewTab(s['name'], s['text'])
                if s['active']:
                    active = i
                w.setFontSize(s.get('size', None))
        else:
            self.tab.addNewTab()
        self.tab.setCurrentIndex(active)

    def saveSession(self, verbos=False):
        tabs= []
        index = self.tab.currentIndex()
        for item in range(self.tab.count()):
            name = self.tab.tabText(item)
            text = self.tab.getTabText(item)
            if managers.context == 'hou':
                size = self.tab.widget(item).edit.fs
            else:
                size = self.tab.widget(item).edit.font().pointSize()
            tab = {'name':name,
                   'text':text,
                   'active': item == index,
                   'size': size}
            tabs.append(tab)
        path = self.session.writeSession(tabs)
        if verbos:
            self.out.showMessage('>>> Session saved: %s' % path.replace('\\','/'))

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
            class stdoutProxy():
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
                    if result != None:
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
            sys.stdout = tmp_stdout

    def clearHistory(self):
        self.out.setText('')

    def saveScript(self):
        text = self.tab.getCurrentText()
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getSaveFileName (self, 'Save script', d, "PY Files (*.py)")
        if path[0]:
            try:
                with open(path[0], 'w') as f:
                    f.write(text)
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

    def tabsToSpaces(self):
        text = self.tab.getCurrentText()
        text = text.replace('\t','    ')
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

        if geo:
            self.move(geo[0], geo[1])
            self.resize(geo[2], geo[3])
        if center:
            x, y = center
            geo = self.geometry()
            geo.moveCenter(QPoint(x,y))
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
            wrap_state = self.wordWrap_act.isChecked()
            self.tab.wordWrap(not wrap_state)
            self.tab.render_whitespace(show_whitespace)
            self.out.render_whitespace(show_whitespace)
            self.whitespace_act.setChecked(show_whitespace)
            self.tab.wordWrap(wrap_state)

        f =  self.out.font()
        f.setPointSize(outFontSize)
        self.out.setFont(f)

    def saveSettings(self):
        settings = self.s.readSettings()
        geo = self.geometry()
        sGeo = [geo.x(), geo.y(), geo.width(), geo.height()]
        center = [geo.center().x(),geo.center().y()]
        size = max(8, self.out.font().pointSize())
        split_sizes = self.splitter.sizes()
        out_word_wrap = self.out_wordWrap_act.isChecked()
        clear_execute = self.clear_exec_act.isChecked()
        echo_execute = self.print_command_act.isChecked()
        word_wrap = self.wordWrap_act.isChecked()
        always_ontop = self.always_ontop_act.isChecked()
        show_whitespace = self.whitespace_act.isChecked()

        data = dict(geometry=sGeo,
                    center=center,
                    outFontSize=size,
                    splitter=split_sizes,
                    wrap=word_wrap,
                    out_wrap=out_word_wrap,
                    echo_execute=echo_execute,
                    clear_execute=clear_execute,
                    always_ontop=always_ontop,
                    show_whitespace=show_whitespace)
        settings.update(data)
        self.s.writeSettings(settings)

    def openSettingsFile(self):
        path = settingsManager.userPrefFolder()
        self.out.showMessage('>>> Settings folder: %s' % path.replace('\\','/'))

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
        elif os.name =='os2':
            os.system('open "%s"' % path)


try:
    QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
except:
    pass


if __name__ == '__main__':
    app = QApplication([])
    w = scriptEditorClass()
    w.show()
    app.exec_()
