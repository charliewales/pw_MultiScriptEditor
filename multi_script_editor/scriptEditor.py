import os
import sys
import webbrowser
from functools import partial
import json
import codecs

# Set preferred binding
if not os.environ.get("QT_PREFERRED_BINDING"):
    os.environ["QT_PREFERRED_BINDING"] = os.pathsep.join(["PySide2", "PySide6", "PyQt5", "PySide", "PyQt4"])
# Disable High Dpi Scaling in PySide6
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

mse_version = "6.4.0"

root_path = os.path.dirname(__file__)
vendor_path = os.path.join(root_path, 'vendor')
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

import managers
from core.execution_manager import ExecutionManager
from core.file_utils import read_file_text
from presenters.main_presenter import MainPresenter
import vendor.Qt
from icons import *
from vendor.help import get_help

from vendor.Qt.QtCore import QPoint, Qt, QTimer, Signal
from vendor.Qt.QtGui import QFont, QIcon, QKeySequence, QTextCursor, QColor, QPalette
from vendor.Qt.QtWidgets import QAction, QApplication, QFileDialog, QFontDialog, QMainWindow, QShortcut, QStyle, QSplitter, QListWidget, QLabel, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QMenu, QLineEdit, QAbstractItemView, QToolTip
from widgets import about, findWidget, outputWidget, shortcuts, tabWidget, themeEditor, symbolWidget, snippetWidget
from widgets import scriptEditor_UIs as ui
from core.outline_parser import OutlineParser
from widgets.pythonSyntax import design
from widgets.outline_utils import HtmlDelegate, create_symbol_item

from widgets.main_window_builder import ScriptEditorUIBuilder
from core.settings_model import SettingsModel, SnippetsModel, ThemesModel
from style.links import links


class scriptEditorClass(QMainWindow, ui.Ui_scriptEditor):
    execute_command_requested = Signal(str, bool, bool)
    update_outline_requested = Signal(str, str)
    save_settings_requested = Signal(dict)
    load_settings_requested = Signal()

    def __init__(self, parent=None):
        super(scriptEditorClass, self).__init__(parent)
        # ui
        py_ver = sys.version.split(' ')[0]
        self.ver = f"{mse_version} · Python-{py_ver} · {vendor.Qt.__binding__}-{vendor.Qt.__binding_version__}"
        self.setupUi(self)
        self.icon_path = os.path.dirname(__file__)

        self.setWindowTitle('Multi Script Editor v%s' % self.ver)
        self.setObjectName('pw_scriptEditor')
        # widgets
        self.out = outputWidget.outputClass()
        self.out_ly.addWidget(self.out)
        self.tab = tabWidget.tabWidgetClass(self)
        self.tab.execute_selected_requested.connect(self.executeSelected)

        # Horizontal QSplitter for outline sidebar and editor tabs
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.outline_panel = QWidget()
        self.outline_panel.setObjectName("outlinePanel")
        self.outline_ly = QVBoxLayout(self.outline_panel)
        self.outline_ly.setContentsMargins(0, 0, 0, 0)
        self.outline_ly.setSpacing(4)
        self.outline_list = QListWidget()
        self.outline_list.setObjectName("outlineList")
        self.outline_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.outline_list.setFocusPolicy(Qt.NoFocus)
        self.outline_list.setItemDelegate(HtmlDelegate(self.outline_list))
        self.outline_list.itemClicked.connect(self.outlineItemClicked)

        self.outline_filter = QLineEdit()
        self.outline_filter.setObjectName("outlineFilter")
        self.outline_filter.setPlaceholderText("Filter outline...")
        self.outline_filter.setClearButtonEnabled(True)
        self.outline_filter.textChanged.connect(self.filterOutline)

        esc_shortcut = QShortcut(QKeySequence("Esc"), self.outline_filter)
        esc_shortcut.setContext(Qt.WidgetShortcut)
        esc_shortcut.activated.connect(self.outline_filter.clear)

        self.outline_ly.addWidget(self.outline_filter)
        self.outline_ly.addWidget(self.outline_list)

        self.horizontal_splitter.addWidget(self.outline_panel)
        self.horizontal_splitter.addWidget(self.tab)
        self.in_ly.addWidget(self.horizontal_splitter)
        self.horizontal_splitter.setStretchFactor(0, 0)
        self.horizontal_splitter.setStretchFactor(1, 1)
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
        ScriptEditorUIBuilder.setup_ui(self)

        # Auto-Save timer (every 60 seconds)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autoSave)
        self.autosave_timer.start(60000)

        # Tab current change triggers outline refresh
        self.tab.currentChanged.connect(self.updateOutline)

        self.setupStatusBarWidgets()

        self.tab.currentChanged.connect(self.statusBar().clearMessage)
        self.tab.currentChanged.connect(self.updateStatusBarInfo)
        self.wordWrap_act.toggled.connect(self.updateStatusBarInfo)

        # start
        self._exec_manager = ExecutionManager()
        self._presenter = MainPresenter(self, self._exec_manager)
        self.fillSessionsMenu()
        self.fillSnippetsMenu()
        self.loadSession()
        if self.tab.count() > 0:
            QTimer.singleShot(100, lambda: self.tab.widget(self.tab.currentIndex()).edit.setFocus() if self.tab.widget(self.tab.currentIndex()) else None)
        self.fillThemeMenu()
        self.setWindowStyle()
        self.appContextMenu()
        self.addArgs()
        self.updateStatusBarInfo()

    def setupStatusBarWidgets(self):
        self.lbl_msg = QLabel("")
        self.lbl_lang = QLabel("Language")
        self.lbl_wrap = QLabel("Wrap: OFF")
        self.lbl_lines = QLabel("0 lines")
        self.lbl_cursor = QLabel("Ln 1, Col 1")

        for lbl in (self.lbl_msg, self.lbl_cursor, self.lbl_lines, self.lbl_lang, self.lbl_wrap):
            lbl.setStyleSheet("padding: 0 5px;")
            self.statusBar().addPermanentWidget(lbl)

        self.status_bar_timer = QTimer(self)
        self.status_bar_timer.setSingleShot(True)
        self.status_bar_timer.timeout.connect(self._updateStatusBarInfo)

    def showStatusMessage(self, msg):
        self.lbl_msg.setText(msg)

    def updateStatusBarInfo(self, *args):
        self.status_bar_timer.start(50)

    def _updateStatusBarInfo(self):
        # Word Wrap
        wrap_state = "ON" if self.wordWrap_act.isChecked() else "OFF"
        self.lbl_wrap.setText(f"Wrap: {wrap_state}")

        idx = self.tab.currentIndex()
        if idx < 0:
            self.lbl_lang.setText("")
            self.lbl_lines.setText("0 lines")
            self.lbl_cursor.setText("Ln 1, Col 1")
            return

        w = self.tab.widget(idx)
        if not w or not hasattr(w, 'edit'):
            return

        # Cursor and Lines
        cursor = w.edit.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")

        if hasattr(w.edit, 'multi_cursor_manager') and w.edit.multi_cursor_manager.has_cursors():
            count = len(w.edit.multi_cursor_manager.multi_cursors)
            if getattr(w.edit.multi_cursor_manager, 'is_auto_populated', False):
                self.lbl_msg.setText(f"{count} occurrences")
            else:
                self.lbl_msg.setText(f"{count} occurrences selected")
        else:
            self.lbl_msg.setText("")

        total_lines = w.edit.document().blockCount()
        self.lbl_lines.setText(f"{total_lines} lines")

        # Language
        file_path = getattr(w, 'file_path', None)
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            lang_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.html': 'HTML',
                '.htm': 'HTML',
                '.yaml': 'YAML',
                '.yml': 'YAML',
                '.md': 'Markdown',
                '.css': 'CSS',
                '.txt': 'Plain Text',
                '.json': 'JSON'
            }
            lang = lang_map.get(ext, 'Python')
        else:
            lang = 'Python'
        self.lbl_lang.setText(lang)
        if lang == 'Python' and hasattr(w.edit, 'runLinter'):
            w.edit.runLinter()

        # Toggle execution UI based on language
        is_python = (lang == 'Python')
        for act in (self.execAll_act, self.execLine_act, self.execSel_act, self.clearHistory_act, self.clear_exec_act):
            if hasattr(self, act.objectName()):
                act.setEnabled(is_python)

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
        self.updateStatusBarInfo()

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

            font_data = {
                "family": font.family(),
                "pointSize": font.pointSize(),
                "weight": font.weight(),
                "italic": font.italic()
            }
            self._temporary_zoom_delta = 0
            self._current_settings['font'] = font_data
            current_theme = self._current_settings.get('theme', 'Multi Script Editor')
            self.applyTheme(current_theme)
            self.saveSettings()

    def clear_exec(self, exec_func):
        self.clearHistory()
        exec_func()

    def show_clear_exec(self):
        if self.clear_exec_act.isChecked():
            self.toolBar.setStyleSheet("""
                QToolBar {
                        border: 1px solid rgba(255, 255, 255, 64);
                        border-radius: 4px;
                        margin: 1px;
                    }
                """)
        else:
            self.toolBar.setStyleSheet("""
                QToolBar {
                        border: 1px solid rgba(255, 255, 255, 0);
                        margin: 1px;
                    }
                """)

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
        self.out.appendHtml(txt)
        self.out.moveCursor(QTextCursor.End)
        self.out.ensureCursorVisible()

    def showEvent(self, event):
        super(scriptEditorClass, self).showEvent(event)
        data = self._current_settings
        if not data:
            self.saveSettings()
        # Restore scroll positions of active tab once the window is shown
        current_widget = self.tab.currentWidget()
        if current_widget and hasattr(current_widget, 'edit'):
            edit = current_widget.edit
            if hasattr(edit, 'needs_loading_scroll_v'):
                scroll_v = edit.needs_loading_scroll_v
                if hasattr(edit, 'needs_loading_scroll_v'):
                    delattr(edit, 'needs_loading_scroll_v')
                if scroll_v > 0:
                    edit.verticalScrollBar().setValue(scroll_v)
                    QTimer.singleShot(50, lambda e=edit, val=scroll_v: e.verticalScrollBar().setValue(val))
                    QTimer.singleShot(150, lambda e=edit, val=scroll_v: e.verticalScrollBar().setValue(val))

    def checkUnsavedChanges(self):
        unsaved_tabs = []
        for i in range(self.tab.count()):
            widget = self.tab.widget(i)
            file_path = getattr(widget, 'file_path', None)

            edit = getattr(widget, 'edit', None)
            if edit and hasattr(edit, 'needs_loading_file'):
                continue

            if file_path and os.path.exists(file_path):
                text = self.tab.getTabText(i)
                file_text = read_file_text(file_path)

                if file_text is not None:
                    if text.replace('\r\n', '\n') != file_text.replace('\r\n', '\n'):
                        unsaved_tabs.append((i, file_path))

        if unsaved_tabs:
            msg = "The following files have unsaved changes:\n\n"
            for _, fp in unsaved_tabs:
                msg += "- %s\n" % os.path.basename(fp)
            msg += "\nDo you want to save them before exiting?"

            res = self.show_question_msg(
                "Unsaved Changes",
                msg,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if res == QMessageBox.Save:
                for i, file_path in unsaved_tabs:
                    text = self.tab.getTabText(i)
                    try:
                        with open(file_path, 'w') as f:
                            f.write(text)
                    except Exception as e:
                        self.out.showMessage('Error saving file: %s (%s)' % (file_path, str(e)))
                return True
            elif res == QMessageBox.Discard:
                return True
            else:
                return False
        return True

    def closeEvent(self, event):
        if not self.checkUnsavedChanges():
            event.ignore()
            return

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
                        text = read_file_text(f)
                        self.tab.addNewTab(os.path.basename(f), text, file_path=f)

    def fillThemeMenu(self):
        self.theme_menu.clear()
        edit_action = QAction('Edit...', self, triggered=self.openThemeEditor)
        edit_action.setShortcut('Ctrl+Shift+T')
        edit_action.setStatusTip("Edit the current color theme")
        self.theme_menu.addAction(edit_action)

        # Randomize custom theme at startup action
        randomize_act = QAction('Randomize custom at startup', self, triggered=self.toggleRandomizeCustomAtStartup)
        randomize_act.setCheckable(True)
        randomize_act.setChecked(self._current_settings.get('randomize_custom_at_startup', False))
        randomize_act.setStatusTip("If active, a random theme is chosen from the custom themes at startup")
        self.theme_menu.addAction(randomize_act)
        self.randomize_custom_act = randomize_act

        self.theme_menu.addSeparator()
        current_theme = self._current_settings.get('theme', 'Multi Script Editor')
        for t in sorted(design.predefinedThemes.keys()):
            act = QAction(t, self, triggered=lambda checked=False, x=t: self.applyTheme(x))
            act.setCheckable(True)
            act.setChecked(t == current_theme)
            act.setStatusTip(f"Apply theme: {t}")
            self.theme_menu.addAction(act)

        theme_settings = ThemesModel().read_settings()
        if theme_settings.get('colors'):
            added_separator = False
            for t in sorted(theme_settings.get('colors').keys()):
                if t not in design.predefinedThemes:
                    if not added_separator:
                        self.theme_menu.addSeparator()
                        added_separator = True
                    act = QAction(t, self, triggered=lambda checked=False, x=t: self.applyTheme(x))
                    act.setCheckable(True)
                    act.setChecked(t == current_theme)
                    act.setStatusTip(f"Apply theme: {t}")
                    self.theme_menu.addAction(act)

    def getCustomThemes(self):
        # Retrieve all custom themes created by the user
        theme_settings = ThemesModel().read_settings()
        custom_themes = []
        if theme_settings.get('colors'):
            for t in theme_settings.get('colors').keys():
                if t not in design.predefinedThemes:
                    custom_themes.append(t)
        return sorted(custom_themes)

    def toggleRandomizeCustomAtStartup(self, checked):
        # Update settings and save when the randomize custom option is toggled
        self._current_settings['randomize_custom_at_startup'] = checked
        self.saveSettings()

    def change_global_font_size(self, increase):
        theme_name = self._current_settings.get('theme', 'Multi Script Editor')
        delta = 1 if increase else -1

        self._temporary_zoom_delta = getattr(self, '_temporary_zoom_delta', 0) + delta
        self.applyTheme(theme_name)

    def restore_global_font_size(self):
        theme_name = self._current_settings.get('theme', 'Multi Script Editor')

        # Load from disk
        disk_settings = self._presenter.settings_model.read_settings_from_disk()

        self._temporary_zoom_delta = 0
        disk_font = disk_settings.get('font', {})
        self._current_settings['font'] = disk_font.copy()

        self.applyTheme(theme_name)

    def fold_all(self):
        editor = self.tab.current()
        if editor:
            editor.fold_all()

    def unfold_all(self):
        editor = self.tab.current()
        if editor:
            editor.unfold_all()

    def fold_current(self):
        editor = self.tab.current()
        if editor:
            editor.fold_current()

    def unfold_current(self):
        editor = self.tab.current()
        if editor:
            editor.unfold_current()

    def applyTheme(self, name):
        qss = design.editorStyle(name)
        colors = design.getColors(name).copy()

        zoom_delta = getattr(self, '_temporary_zoom_delta', 0)
        if zoom_delta:
            size_keys = [
                'textsize', 'output_text_size', 'outline_text_size',
                'menu_text_size', 'status_bar_text_size', 'tab_text_size',
                'symbols_text_size', 'line_numbers_text_size', 'completer_text_size'
            ]
            for k in size_keys:
                if k in colors:
                    colors[k] = max(1, int(colors[k]) + zoom_delta)

        self._current_colors_cache = colors

        main_css = design.applyColorToMainStyle(colors)
        if main_css:
            self.menubar.setStyleSheet(main_css)
            for menu in self.findChildren(QMenu):
                menu.setStyleSheet(main_css)

        o = self.out
        o.applyHightLighter(name)
        o.setStyleSheet(qss)
        self.outline_panel.setStyleSheet(qss)

        for act in self.theme_menu.actions():
            if act.isCheckable():
                if hasattr(self, 'randomize_custom_act') and act == self.randomize_custom_act:
                    continue
                act.setChecked(act.text() == name)

        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            w.edit.applyHightLighter(name)
            w.edit.completer.setStyleSheet(qss)
            w.edit.setStyleSheet(qss)

        font_data = colors.get('font')
        if not font_data:
            font_data = self._current_settings.get('font', {}).copy()
        else:
            font_data = font_data.copy()

        if not font_data:
            font_data = {'pointSize': 10}

        zoom_delta = getattr(self, '_temporary_zoom_delta', 0)
        if zoom_delta:
            font_data['pointSize'] = max(1, font_data.get('pointSize', 10) + zoom_delta)

        secondary_default = max(1, int(font_data.get('pointSize', 10) * 0.9))

        if 'tab_text_size' not in colors and 'textsize' not in colors:
            colors_for_tab = colors.copy()
            colors_for_tab['tab_text_size'] = secondary_default
            self.tab._tab_text_size = secondary_default
            self.tab.apply_tab_style(colors_for_tab)
        else:
            self.tab._tab_text_size = colors.get('tab_text_size', None)
            self.tab.apply_tab_style(colors)

        if name not in design.predefinedThemes:
            self.set_font_act.setEnabled(False)
            self.set_font_act.setText("Choose Font (from theme)")
        else:
            self.set_font_act.setEnabled(True)
            self.set_font_act.setText("Choose Font...")

        font_data = colors.get('font')
        if not font_data:
            font_data = self._current_settings.get('font', {}).copy()
        else:
            font_data = font_data.copy()

        if not font_data:
            font_data = {'pointSize': 10}

        zoom_delta = getattr(self, '_temporary_zoom_delta', 0)
        if zoom_delta:
            font_data['pointSize'] = max(1, font_data.get('pointSize', 10) + zoom_delta)

        if font_data:
            self.tab.set_start_font(font_data)

            out_font_data = font_data.copy()
            secondary_default = max(1, int(font_data.get('pointSize', 10) * 0.9))

            if 'output_text_size' in colors:
                out_font_data['pointSize'] = max(1, int(colors['output_text_size']))
            elif 'textsize' in colors:
                out_font_data['pointSize'] = max(1, int(colors['textsize']))
            else:
                out_font_data['pointSize'] = secondary_default
            self.out.set_start_font(out_font_data)

            base_font = QFont(font_data.get('family', ''))
            base_font.setStyleHint(QFont.Monospace)
            base_font.setPointSize(font_data.get('pointSize', 10))
            self.theme_font = QFont(base_font)

            tooltip_font = QFont(base_font)
            tab_text_size = colors.get('tab_text_size', None)
            if tab_text_size is not None:
                tooltip_font.setPointSize(max(1, int(tab_text_size)))
            elif 'textsize' in colors:
                tooltip_font.setPointSize(max(1, int(colors['textsize'])))
            else:
                tooltip_font.setPointSize(secondary_default)
            QToolTip.setFont(tooltip_font)

            if colors.get('use_theme_font_on_outline', True):
                outline_font = QFont(base_font)
            else:
                outline_font = QApplication.font("QListWidget")
            if 'outline_text_size' in colors:
                outline_font.setPointSize(max(1, int(colors['outline_text_size'])))
            elif 'textsize' in colors:
                outline_font.setPointSize(max(1, int(colors['textsize'])))
            else:
                outline_font.setPointSize(secondary_default)

            self.outline_list.setFont(outline_font)
            self.current_outline_font = outline_font
            self.outline_filter.setFont(outline_font)
            for i in range(self.outline_list.count()):
                self.outline_list.item(i).setFont(outline_font)

            if colors.get('use_theme_font_on_menus', False):
                menu_font = QFont(base_font)
            else:
                menu_font = QApplication.font("QMenu")

            if colors.get('use_theme_font_on_status_bar', False):
                status_bar_font = QFont(base_font)
            else:
                status_bar_font = QApplication.font("QStatusBar")

            if 'menu_text_size' in colors:
                menu_font.setPointSize(max(1, int(colors['menu_text_size'])))
            else:
                if 'textsize' in colors and colors.get('use_theme_font_on_menus', False):
                    menu_font.setPointSize(max(1, int(colors['textsize'])))
                else:
                    menu_font.setPointSize(secondary_default)

            self.menubar.setFont(menu_font)
            for menu in self.findChildren(QMenu):
                menu.setFont(menu_font)

            if 'status_bar_text_size' in colors:
                status_bar_font.setPointSize(max(1, int(colors['status_bar_text_size'])))
            else:
                if 'textsize' in colors and colors.get('use_theme_font_on_status_bar', False):
                    status_bar_font.setPointSize(max(1, int(colors['textsize'])))
                else:
                    status_bar_font.setPointSize(secondary_default)

            if self.statusBar():
                self.statusBar().setFont(status_bar_font)
                for lbl in (self.lbl_msg, self.lbl_lang, self.lbl_wrap, self.lbl_lines, self.lbl_cursor):
                    lbl.setFont(status_bar_font)

        s = self._current_settings
        s['theme'] = name
        self.save_settings_requested.emit(s)

        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            w.edit.autocomplete_timer.stop()
            w.edit.completer.hideMe()
            w.edit._skip_autocomplete_once = True

        self.setWindowStyle()

    def setWindowStyle(self):
        theme = self._current_settings.get('theme', 'Multi Script Editor')
        colors = design.getColors(theme)
        css = design.applyColorToMainStyle(colors)
        if css:
            self.setStyleSheet(css)

            # Sync workaround for PySide2: set palette explicitly so it doesn't default to black
            fg = colors.get('tab_text')
            if fg:
                color = QColor(*fg) if isinstance(fg, (list, tuple)) else QColor(fg)
                pal = self.outline_filter.palette()
                pal.setColor(QPalette.Text, color)
                if hasattr(QPalette, 'PlaceholderText'):
                    pal.setColor(QPalette.PlaceholderText, color)
                self.outline_filter.setPalette(pal)

            if __name__ == '__main__':
                self.setWindowIcon(QIcon(icons['pw']))

    def show_question_msg(self, title, text, buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.No):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(buttons)
        msg_box.setDefaultButton(defaultButton)

        if hasattr(self, 'theme_font'):
            msg_box.setFont(self.theme_font)

        if hasattr(msg_box, "exec"):
            return msg_box.exec()
        else:
            return msg_box.exec_()

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
                current_msg = self.statusBar().currentMessage()
                if current_msg.startswith("Syntax Error"):
                    self.statusBar().clearMessage()

    def getShortcut(self, action):
        settings = self._presenter.settings_model.load_settings()
        return settings.get('shortcuts', {}).get(action, None)

    def loadSession(self, sessions=None):
        if sessions is None:
            sessions = self._presenter.get_session_tabs()
        self.tab.clear()
        active_index = -1
        if sessions:
            self.tab.blockSignals(True)
            for i, s in enumerate(sessions):
                text = s.get('text')
                file_path = s.get('file_path')
                is_active = s.get('active', False)
                w = self.tab.addNewTab(s.get('name', 'tab'), None, file_path=file_path, make_current=False)

                # Store bookmarks, line, column, and scroll positions to be loaded when text is populated
                w.needs_loading_bookmarks = s.get('bookmarks', "")
                w.needs_loading_line = s.get('line', 1)
                w.needs_loading_column = s.get('column', 0)
                w.needs_loading_scroll_v = s.get('scroll_v', 0)
                w.needs_loading_folds = s.get('folds', [])

                if is_active:
                    active_index = i
                    if file_path and os.path.exists(file_path):
                        text = read_file_text(file_path)
                    if text:
                        w.addText(text)
                        w.document().clearUndoRedoStacks()
                        w.document().setModified(False)
                        if hasattr(w, 'needs_loading_folds') and w.needs_loading_folds:
                            if hasattr(w, 'set_folded_blocks'):
                                w.set_folded_blocks(w.needs_loading_folds)
                            delattr(w, 'needs_loading_folds')
                        if hasattr(w, 'set_bookmarks') and w.needs_loading_bookmarks:
                            w.set_bookmarks(w.needs_loading_bookmarks)
                            delattr(w, 'needs_loading_bookmarks')
                        # Jump to the saved line and column!
                        if hasattr(w, 'needs_loading_line'):
                            line_num = w.needs_loading_line
                            column_num = getattr(w, 'needs_loading_column', 0)
                            if line_num > 1 or column_num > 0:
                                block = w.document().findBlockByNumber(line_num - 1)
                                if block.isValid():
                                    cursor = w.textCursor()
                                    col = min(column_num, max(0, block.length() - 1))
                                    cursor.setPosition(block.position() + col)
                                    w.setTextCursor(cursor)
                                    if hasattr(w, 'highlight_current_line'):
                                        w.highlight_current_line()
                    if hasattr(w, 'needs_loading_line'):
                        delattr(w, 'needs_loading_line')
                    if hasattr(w, 'needs_loading_column'):
                        delattr(w, 'needs_loading_column')
                    if hasattr(w, 'needs_loading_folds'):
                        delattr(w, 'needs_loading_folds')
                else:
                    w.needs_loading_file = file_path
                    w.needs_loading_text = text

                if s.get('size'):
                    # w is the edit widget from addNewTab
                    if hasattr(w, 'setFontSize'):
                        w.setFontSize(s.get('size'))

            self.tab.blockSignals(False)
            if active_index != -1:
                self.tab.setCurrentIndex(active_index)
                if hasattr(self.tab, 'onTabChanged'):
                    self.tab.onTabChanged(active_index)
        if self.tab.count() == 0:
            self.tab.addNewTab()

    def _get_tabs_data(self, save_full_text=False):
        tabs = []
        index = self.tab.currentIndex()
        zoom_delta = getattr(self, '_temporary_zoom_delta', 0)
        for item in range(self.tab.count()):
            widget = self.tab.widget(item)
            if not widget:
                continue
            name = self.tab.tabText(item)
            text = self.tab.getTabText(item)
            size = 12
            if hasattr(widget, 'edit') and hasattr(widget.edit, 'getFontSize'):
                size = widget.edit.getFontSize()
            size = max(1, size - zoom_delta)

            file_path = getattr(widget, 'file_path', None)
            bookmarks = []
            if hasattr(widget, 'edit') and hasattr(widget.edit, 'get_bookmarks'):
                bookmarks = widget.edit.get_bookmarks()

            line = 1
            column = 0
            scroll_v = 0
            if hasattr(widget, 'edit'):
                if hasattr(widget.edit, 'needs_loading_line'):
                    line = widget.edit.needs_loading_line
                    column = getattr(widget.edit, 'needs_loading_column', 0)
                elif hasattr(widget.edit, 'textCursor'):
                    line = widget.edit.textCursor().blockNumber() + 1
                    column = widget.edit.textCursor().columnNumber()

                if hasattr(widget.edit, 'needs_loading_scroll_v'):
                    scroll_v = widget.edit.needs_loading_scroll_v
                else:
                    scroll_v = widget.edit.verticalScrollBar().value()

            folds = []
            if hasattr(widget, 'edit') and hasattr(widget.edit, 'get_folded_blocks'):
                folds = widget.edit.get_folded_blocks()

            tab = {
                'name': name,
                'text': text if (save_full_text or not file_path) else "",
                'active': item == index,
                'size': size,
                'file_path': file_path,
                'bookmarks': bookmarks,
                'line': line,
                'column': column,
                'scroll_v': scroll_v,
                'folds': folds
            }
            tabs.append(tab)
        return tabs

    def saveSession(self, verbos=False):
        if not hasattr(self, '_presenter'):
            return
        tabs = self._get_tabs_data(save_full_text=False)
        path = self._presenter.save_session(tabs)
        if verbos:
            self.out.showMessage('>>> Session saved: %s' % path.replace('\\', '/'))

    def closeAllTabsWithConfirm(self):
        res = self.show_question_msg(
            "Close All Tabs",
            "Are you sure you want to close all tabs?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self.tab.clear()
            self.tab.addNewTab()

    def executeAll(self):
        if hasattr(self, 'execAll_act') and not self.execAll_act.isEnabled():
            return
        allText = self.tab.getCurrentText()
        if self.print_command_act.isChecked():
            allText += '\n# Execute All'
        if allText:
            self.execute_command_requested.emit(allText.strip(), self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def executeLine(self):
        if hasattr(self, 'execLine_act') and not self.execLine_act.isEnabled():
            return
        text = self.tab.getCurrentLine()
        if self.print_command_act.isChecked():
            text += '\n# Execute Line'
        if text:
            self.execute_command_requested.emit(text, self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def executeSelected(self):
        if hasattr(self, 'execSel_act') and not self.execSel_act.isEnabled():
            return
        text = self.tab.getCurrentSelectedText()
        if self.print_command_act.isChecked():
            text += '\n# Execute Selected'
        if text:
            self.execute_command_requested.emit(text, self.print_command_act.isChecked(), self.clear_exec_act.isChecked())

    def deleteLine(self):
        i = self.tab.currentIndex()
        if i >= 0:
            self.tab.widget(i).edit.deleteLine()

    def duplicateLine(self):
        i = self.tab.currentIndex()
        if i >= 0:
            self.tab.widget(i).edit.duplicate()

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
        self.out.clear()

    def show_autocompletion(self):
        idx = self.tab.currentIndex()
        if idx >= 0:
            w = self.tab.widget(idx)
            if hasattr(w, 'edit'):
                w.edit.parseText(force=True)

    def gotoLine(self):
        index = self.tab.currentIndex()
        if index < 0:
            return

        # Get maximum line count
        edit_widget = self.tab.widget(index).edit
        max_lines = edit_widget.document().blockCount()

        line_num, ok = QInputDialog.getInt(self, "Go to line", "Enter line number:", 1, 1, max_lines)
        if ok:
            block = edit_widget.document().findBlockByNumber(line_num - 1)
            if block.isValid():
                cursor = edit_widget.textCursor()
                cursor.setPosition(block.position())
                edit_widget.setTextCursor(cursor)
                edit_widget.centerCursor()
                edit_widget.setFocus()

    def goToSymbol(self):
        index = self.tab.currentIndex()
        if index < 0:
            return

        edit_widget = self.tab.widget(index).edit
        code = edit_widget.toPlainText()

        # Determine extension based on file_path or fallback to .py
        ext = '.py'
        if hasattr(self.tab.widget(index), 'file_path') and self.tab.widget(index).file_path:
            _, ext = os.path.splitext(self.tab.widget(index).file_path)

        symbols = OutlineParser.parse(code, ext)
        if not symbols:
            return

        theme_name = self._current_settings.get('theme', 'Dark')
        qss = design.editorStyle(theme_name)
        colors = design.getColors(theme_name)

        if colors.get('use_theme_font_on_symbols', True):
            font_data = colors.get('font')
            if font_data:
                font = QFont(font_data.get('family', ''), font_data.get('pointSize', 10), font_data.get('weight', -1), font_data.get('italic', False))
            else:
                font = QFont(edit_widget.font())
        else:
            font = QApplication.font("QListWidget")

        if 'symbols_text_size' in colors:
            font.setPointSize(max(1, int(colors['symbols_text_size'])))
        else:
            font.setPointSize(max(1, int(font.pointSize() * 0.9)))

        self.symbol_widget = symbolWidget.SymbolWidget(symbols, self, edit_widget, qss=qss, font=font, colors=colors, ext=ext)

        def _jump_to_line(line_num):
            block = edit_widget.document().findBlockByNumber(line_num - 1)
            if block.isValid():
                cursor = edit_widget.textCursor()
                cursor.setPosition(block.position())
                edit_widget.setTextCursor(cursor)
                edit_widget.centerCursor()
                edit_widget.setFocus()

        self.symbol_widget.symbolSelected.connect(_jump_to_line)
        self.symbol_widget.show()
        self.symbol_widget.search_le.setFocus()

    def _show_generic_symbol_widget(self, symbols, callback, hide_search=False, placeholder_text="Search symbol...", auto_accept_on_ctrl_release=False, allow_delete=False, delete_callback=None):
        theme_name = self._current_settings.get('theme', 'Dark')
        qss = design.editorStyle(theme_name)
        colors = design.getColors(theme_name)

        if colors.get('use_theme_font_on_symbols', True):
            font_data = colors.get('font')
            if font_data:
                font = QFont(font_data.get('family', ''), font_data.get('pointSize', 10), font_data.get('weight', -1), font_data.get('italic', False))
            else:
                current_edit = self.tab.current()
                if current_edit:
                    font = QFont(current_edit.font())
                else:
                    font = QApplication.font("QListWidget")
        else:
            font = QApplication.font("QListWidget")

        if 'symbols_text_size' in colors:
            font.setPointSize(max(1, int(colors['symbols_text_size'])))
        else:
            font.setPointSize(max(1, int(font.pointSize() * 0.9)))

        center_widget = self.tab.current() or self.out
        self.generic_symbol_widget = symbolWidget.SymbolWidget(
            symbols, self, center_widget, qss=qss, font=font, colors=colors, ext='.generic',
            placeholder_text=placeholder_text, auto_accept_on_ctrl_release=auto_accept_on_ctrl_release,
            allow_delete=allow_delete
        )

        if hide_search:
            self.generic_symbol_widget.search_le.hide()

        self.generic_symbol_widget.symbolSelected.connect(callback)
        if delete_callback:
            self.generic_symbol_widget.symbolDeleted.connect(delete_callback)
        self.generic_symbol_widget.show()
        if not hide_search:
            self.generic_symbol_widget.search_le.setFocus()
        else:
            self.generic_symbol_widget.list_widget.setFocus()

    def showRecentFiles(self):
        if hasattr(self, 'generic_symbol_widget') and self.generic_symbol_widget.isVisible():
            self.generic_symbol_widget.navigate_next(wrap=True)
            return

        recent = self._current_settings.get('recent_files', [])
        if not recent:
            return

        symbols = []
        open_icon = QIcon(icons['open'])
        missing_icon = QIcon(icons['missing'])

        for path in recent:
            name = os.path.basename(path) + ' - ' + os.path.dirname(path)
            if not os.path.exists(path):
                icon = missing_icon
            else:
                icon = open_icon
            symbols.append({'name': name, 'line': path, 'indent': 0, 'icon': icon})

        self._show_generic_symbol_widget(
            symbols, self.openRecentFile,
            placeholder_text="Search files by name...",
            auto_accept_on_ctrl_release=False,
            allow_delete=True,
            delete_callback=self.removeRecentFile
        )

    def removeRecentFile(self, path, prompt=True):
        if prompt:
            reply = self.show_question_msg(
                'Remove Recent File',
                f'Are you sure you want to remove this file from the recent list?\n{path}',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return

        recent = self._current_settings.get('recent_files', [])
        if path in recent:
            recent.remove(path)
            self._current_settings['recent_files'] = recent
            self.saveSettings()
            self.updateRecentFilesMenu()

        if hasattr(self, 'generic_symbol_widget') and self.generic_symbol_widget.isVisible():
            self.generic_symbol_widget.remove_item_by_data(path)

    def showOpenTabs(self):
        if hasattr(self, 'generic_symbol_widget') and self.generic_symbol_widget.isVisible():
            self.generic_symbol_widget.navigate_next(wrap=True)
            return

        symbols = []
        mru_widgets = getattr(self.tab, '_mru_tabs', [])
        ordered_indices = []

        for w in mru_widgets:
            idx = self.tab.indexOf(w)
            if idx >= 0 and idx not in ordered_indices:
                ordered_indices.append(idx)

        for i in range(self.tab.count()):
            if i not in ordered_indices:
                ordered_indices.append(i)

        for i in ordered_indices:
            text = self.tab.tabText(i)
            widget = self.tab.widget(i)
            path = widget.file_path if hasattr(widget, 'file_path') else ''
            name = text
            if path:
                name += ' - ' + os.path.dirname(path)
            symbols.append({'name': name, 'line': i, 'indent': 0})

        self._show_generic_symbol_widget(
            symbols, self.tab.switch_to_tab_index,
            hide_search=True,
            auto_accept_on_ctrl_release=True
        )

        if self.tab.count() > 1:
            self.generic_symbol_widget.navigate_next()

    def saveScriptAs(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        cont = self.tab.widget(index)
        if self.trimAutoWhitespace_act.isChecked():
            self.trimTrailingWhitespace()

        text = self.tab.getCurrentText()

        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        if hasattr(cont, 'file_path') and cont.file_path:
            d = os.path.dirname(cont.file_path)

        path = QFileDialog.getSaveFileName(self, 'Save script as', d, "All Supported Files (*.css *.html *.htm *.js *.json *.log *.md *.py *.txt *.usd *.usda *.yaml *.yml);;CSS Files (*.css);;HTML Files (*.html *.htm);;JavaScript Files (*.js);;JSON Files (*.json);;Log Files (*.log);;Markdown Files (*.md);;Python Files (*.py);;Text Files (*.txt);;USD Files (*.usd *.usda);;YAML Files (*.yaml *.yml);;All Files (*.*)")
        if path[0]:
            try:
                with open(path[0], 'w') as f:
                    f.write(text)
                self.addRecentFile(path[0])
                self.tab.addNewTab(os.path.basename(path[0]), text, file_path=path[0])
                self.out.showMessage('Saved to: %s' % path[0])
            except Exception as e:
                self.out.showMessage('Error saving file: %s (%s)' % (path[0], str(e)))


    def saveScript(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        cont = self.tab.widget(index)
        if self.trimAutoWhitespace_act.isChecked():
            self.trimTrailingWhitespace()

        text = self.tab.getCurrentText()

        # Check if the tab already has an associated file path
        if hasattr(cont, 'file_path') and cont.file_path and os.path.exists(os.path.dirname(cont.file_path)):
            try:
                with open(cont.file_path, 'w') as f:
                    f.write(text)
                self.out.showMessage('Saved to: %s' % cont.file_path)
                cont.edit.document().setModified(False)
            except Exception as e:
                self.out.showMessage('Error saving file: %s (%s)' % (cont.file_path, str(e)))
            return

        # Otherwise do Save As
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getSaveFileName(self, 'Save script', d, "All Supported Files (*.css *.html *.htm *.js *.json *.log *.md *.py *.txt *.usd *.usda *.yaml *.yml);;CSS Files (*.css);;HTML Files (*.html *.htm);;JavaScript Files (*.js);;JSON Files (*.json);;Log Files (*.log);;Markdown Files (*.md);;Python Files (*.py);;Text Files (*.txt);;USD Files (*.usd *.usda);;YAML Files (*.yaml *.yml);;All Files (*.*)")
        if path[0]:
            try:
                with open(path[0], 'w') as f:
                    f.write(text)
                self.addRecentFile(path[0])
                if hasattr(cont, 'file_path'):
                    cont.file_path = path[0]
                self.tab.setTabText(index, os.path.basename(path[0]))
                self.tab.setTabToolTip(index, os.path.normpath(path[0]))
                self.out.showMessage('Saved to: %s' % path[0])
                cont.edit.document().setModified(False)
                if hasattr(cont, 'edit') and hasattr(cont.edit, 'applyHightLighter'):
                    cont.edit.applyHightLighter(self._current_settings.get('theme', 'Multi Script Editor'))
            except:
                self.out.showMessage('Error save file; %s' % path[0])

    def loadScript(self):
        d = os.getenv('HOME')
        if not d:
            d = os.path.expanduser('~')
        path = QFileDialog.getOpenFileName(self, 'Open script', d, "All Supported Files (*.css *.html *.htm *.js *.json *.log *.md *.py *.txt *.usd *.usda *.yaml *.yml);;CSS Files (*.css);;HTML Files (*.html *.htm);;JavaScript Files (*.js);;JSON Files (*.json);;Log Files (*.log);;Markdown Files (*.md);;Python Files (*.py);;Text Files (*.txt);;USD Files (*.usd *.usda);;YAML Files (*.yaml *.yml);;All Files (*.*)")
        if path[0]:
            if os.path.exists(path[0]):
                text = read_file_text(path[0])
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
        open_icon = QIcon(icons['open'])
        missing_icon = QIcon(icons['missing'])

        for path in recent:
            act = QAction(os.path.basename(path), self)
            act.setToolTip(path)
            if os.path.exists(path):
                act.setIcon(open_icon)
                act.setStatusTip(f"Open recent file: {path}")
            else:
                act.setIcon(missing_icon)
                act.setStatusTip(f"Missing recent file: {path}")
            act.triggered.connect(partial(self.openRecentFile, path))
            self.recent_files_menu.addAction(act)

        self.recent_files_menu.addSeparator()
        clear_act = QAction("Clear recent", self)
        clear_act.setStatusTip("Clear the list of recent files")
        clear_act.triggered.connect(self.clearRecentFiles)
        self.recent_files_menu.addAction(clear_act)

    def clearRecentFiles(self):
        reply = self.show_question_msg('Clear Recent Files', 'Are you sure you want to clear the recent files list?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            data = self._current_settings
            data['recent_files'] = []
            self.save_settings_requested.emit(data)
            self.updateRecentFilesMenu()

    def openRecentFile(self, path):
        if os.path.exists(path):
            text = read_file_text(path)
            self.tab.addNewTab(os.path.basename(path), text, file_path=path)
            self.addRecentFile(path)
        else:
            reply = self.show_question_msg(
                'File not found',
                f'The file {path} does not exist.\nDo you want to remove it from the recent list?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.removeRecentFile(path, prompt=False)

    def tabsToSpaces(self):
        text = self.tab.getCurrentText()
        text = text.replace('\t', '    ')
        self.tab.setCurrentText(text)

    def spacesToTabs(self):
        text = self.tab.getCurrentText()
        text = text.replace('    ', '\t')
        self.tab.setCurrentText(text)

    def trimTrailingWhitespace(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        cont = self.tab.widget(index)
        if not hasattr(cont, 'edit'):
            return

        edit = cont.edit
        cursor = edit.textCursor()
        cursor.beginEditBlock()

        document = edit.document()
        for i in range(document.blockCount()):
            block = document.findBlockByNumber(i)
            text = block.text()
            if text.endswith(' ') or text.endswith('\t'):
                stripped = text.rstrip(' \t')
                diff = len(text) - len(stripped)
                if diff > 0:
                    c = QTextCursor(block)
                    c.movePosition(QTextCursor.EndOfBlock)
                    c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, diff)
                    c.removeSelectedText()

        cursor.endEditBlock()

    def insertText(self, text):
        self.tab.addToCurrent(text)

    def always_ontop(self):
        """Set the window to always be on top or turn off the feature."""
        state = self.always_ontop_act.isChecked()
        flags = self.windowFlags()
        if state:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint

        # Workaround for PySide6: ensure window buttons remain enabled
        flags |= Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

        self.setWindowFlags(flags)
        self.show()

    def apply_settings(self, settings):
        self._current_settings = settings
        if hasattr(self, 's') and hasattr(self.s, 'write_settings'):
            self.s.write_settings(settings)
        self.loadSettings()

    def loadSettings(self):
        data = self._current_settings

        always_ontop = data.get('always_ontop', False)
        center = data.get('center', None)
        clear_exec = data.get('clear_execute', None)
        echo_exec = data.get('echo_execute', None)
        geo = data.get('geometry', None)
        is_max = data.get('maximized', False)
        out_wrap = data.get('out_wrap', None)
        outFontSize = data.get('outFontSize', 10)
        splitter = data.get('splitter', [600, 400])
        horizontal_splitter_sizes = data.get('horizontal_splitter', [200, 600])
        wrap = data.get('wrap', None)
        show_whitespace = data.get('show_whitespace', False)
        font = data.get('font', False)
        autocomplete = data.get('autocomplete', True)
        fuzzy_autocomplete = data.get('fuzzy_autocomplete', True)
        show_docstrings = data.get('show_docstrings', True)
        trim_auto_whitespace = data.get('trim_auto_whitespace', False)

        if geo:
            self.move(geo[0], geo[1])
            self.resize(geo[2], geo[3])
        else:
            self.resize(1080, 1080)

        if is_max:
            self.showMaximized()

        if center:
            x, y = center
            geo = self.geometry()
            geo.moveCenter(QPoint(x, y))
            self.setGeometry(geo)

        output_bottom = data.get('output_bottom', False)
        self.outputBottom_act.setChecked(output_bottom)
        self.toggleOutputBottom(output_bottom)

        if splitter:
            if all(s > 0 for s in splitter):
                self._last_splitter_sizes = splitter
                self.splitter.setSizes(splitter)
            else:
                default_sizes = self.getDefaultSplitterSizes()
                self._last_splitter_sizes = default_sizes
                self.splitter.setSizes(default_sizes)
        else:
            default_sizes = self.getDefaultSplitterSizes()
            self._last_splitter_sizes = default_sizes
            self.splitter.setSizes(default_sizes)

        if horizontal_splitter_sizes:
            self._last_horizontal_splitter_sizes = horizontal_splitter_sizes
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
        current_flags = self.windowFlags()
        new_flags = current_flags

        if always_ontop:
            new_flags |= Qt.WindowStaysOnTopHint
        else:
            new_flags &= ~Qt.WindowStaysOnTopHint

        # PySide6 workaround to keep window controls enabled
        new_flags |= Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

        if current_flags != new_flags:
            self.setWindowFlags(new_flags)
            if self.isVisible():
                self.show()
        if show_whitespace is not None:
            self.tab.render_whitespace(show_whitespace)
            self.out.render_whitespace(show_whitespace)
            self.whitespace_act.setChecked(show_whitespace)
        if font:
            self.tab.set_start_font(font)
            self.out.set_start_font(font)

            outline_font = QFont(self.out.font())
            if outline_font.pointSize() > 0:
                outline_font.setPointSize(max(1, int(outline_font.pointSize() * 0.8)))
            elif outline_font.pixelSize() > 0:
                outline_font.setPixelSize(max(1, int(outline_font.pixelSize() * 0.8)))
            self.outline_list.setFont(outline_font)
            self.current_outline_font = outline_font
            self.outline_filter.setFont(outline_font)
            for i in range(self.outline_list.count()):
                self.outline_list.item(i).setFont(outline_font)
        self.autocomplete_act.setChecked(autocomplete)
        self.fuzzy_autocomplete_act.setChecked(fuzzy_autocomplete)
        self.show_docstrings_act.setChecked(show_docstrings)
        self.trimAutoWhitespace_act.setChecked(trim_auto_whitespace)

        f = self.out.font()
        f.setPointSize(outFontSize)
        self.out.setFont(f)

        show_outline = data.get('show_outline', False)
        self.showOutline_act.setChecked(show_outline)
        self.toggleOutline(show_outline)

        show_outline_button = data.get('show_outline_button', True)
        self.showOutlineButton_act.setChecked(show_outline_button)
        self.toggleOutlineButton(show_outline_button)

        show_output = data.get('show_output', True)
        self.showOutput_act.setChecked(show_output)
        self.toggleOutput(show_output)

        show_menus = data.get('show_menus', True)
        self.toggleMenus_act.setChecked(show_menus)
        self.toggleMenuBar(show_menus)

        syntax_check = data.get('syntax_check', True)
        self.syntaxCheck_act.setChecked(syntax_check)
        self.toggleSyntaxCheck(syntax_check)

        highlight_all = data.get('highlight_all_occurrences', True)
        self.highlightAllOccurrences_act.setChecked(highlight_all)

        occurrences_case_sensitive = data.get('occurrences_case_sensitive', False)
        self.occurrencesCaseSensitive_act.setChecked(occurrences_case_sensitive)

        prefer_single_quotes = data.get('prefer_single_quotes', False)
        self.preferSingleQuotes_act.setChecked(prefer_single_quotes)

        quick_tab_switching = data.get('quick_tab_switching', True)
        self.quickTabSwitching_act.setChecked(quick_tab_switching)

        auto_close_delimiters = data.get('auto_close_delimiters', True)
        self.autoCloseDelimiters_act.setChecked(auto_close_delimiters)

        if hasattr(self, 'randomize_custom_act'):
            self.randomize_custom_act.setChecked(data.get('randomize_custom_at_startup', False))

        self.updateRecentFilesMenu()

        theme = data.get('theme', 'Multi Script Editor')
        if data.get('randomize_custom_at_startup', False) and not getattr(self, '_theme_randomized', False):
            self._theme_randomized = True
            custom_themes = self.getCustomThemes()
            if custom_themes:
                import random
                theme = random.choice(custom_themes)
                data['theme'] = theme
        if theme == 'default':
            theme = 'Multi Script Editor'
        self._current_settings['theme'] = theme
        self.applyTheme(theme)

    def saveSettings(self):
        settings = self._current_settings
        in_zen_mode = getattr(self, 'zen_mode_act', None) and self.zen_mode_act.isChecked()
        zen_state = getattr(self, '_zen_mode_state', {})

        if in_zen_mode and 'rect' in zen_state:
            rect = zen_state['rect']
            sGeo = [rect[0], rect[1], rect[2], rect[3]]
            center = [rect[0] + rect[2] / 2, rect[1] + rect[3] / 2]
            is_max = zen_state.get('maximized', False)
        else:
            geo = self.normalGeometry() if hasattr(self, 'normalGeometry') else self.geometry()
            frame_offset_x = self.geometry().x() - self.x()
            frame_offset_y = self.geometry().y() - self.y()
            sGeo = [geo.x() - frame_offset_x, geo.y() - frame_offset_y, geo.width(), geo.height()]
            center = [geo.center().x(), geo.center().y()]
            is_max = self.isMaximized()
        out_pt = self.out.getFontSize()
        size = max(8, out_pt)
        split_sizes = self.splitter.sizes()
        if not self.showOutput_act.isChecked() or any(s == 0 for s in split_sizes):
            split_sizes = getattr(self, '_last_splitter_sizes', self.getDefaultSplitterSizes())
        horizontal_split_sizes = self.horizontal_splitter.sizes()
        if horizontal_split_sizes[0] == 0:
            horizontal_split_sizes = getattr(self, '_last_horizontal_splitter_sizes', [200, 600])
        out_word_wrap = self.out_wordWrap_act.isChecked()
        clear_execute = self.clear_exec_act.isChecked()
        echo_execute = self.print_command_act.isChecked()
        word_wrap = self.wordWrap_act.isChecked()
        always_ontop = self.always_ontop_act.isChecked()
        show_whitespace = self.whitespace_act.isChecked()

        in_zen_mode = getattr(self, 'zen_mode_act', None) and self.zen_mode_act.isChecked()
        zen_state = getattr(self, '_zen_mode_state', {})

        show_outline = zen_state.get('outline', self.showOutline_act.isChecked()) if in_zen_mode else self.showOutline_act.isChecked()
        show_outline_button = self.showOutlineButton_act.isChecked()
        show_output = zen_state.get('output', self.showOutput_act.isChecked()) if in_zen_mode else self.showOutput_act.isChecked()
        show_menus = zen_state.get('menubar', self.toggleMenus_act.isChecked()) if in_zen_mode else self.toggleMenus_act.isChecked()
        syntax_check = self.syntaxCheck_act.isChecked()
        highlight_all = self.highlightAllOccurrences_act.isChecked()
        occurrences_case_sensitive = self.occurrencesCaseSensitive_act.isChecked()
        prefer_single_quotes = self.preferSingleQuotes_act.isChecked()
        output_bottom = self.outputBottom_act.isChecked()
        quick_tab_switching = self.quickTabSwitching_act.isChecked()
        auto_close_delimiters = self.autoCloseDelimiters_act.isChecked()
        autocomplete = self.autocomplete_act.isChecked()
        fuzzy_autocomplete = self.fuzzy_autocomplete_act.isChecked()
        show_docstrings = self.show_docstrings_act.isChecked()
        trim_auto_whitespace = self.trimAutoWhitespace_act.isChecked()
        randomize_custom = self.randomize_custom_act.isChecked() if hasattr(self, 'randomize_custom_act') else False

        current_theme_name = settings.get('theme', 'Multi Script Editor')
        theme_colors = design.getColors(current_theme_name)
        theme_has_custom_font = 'font' in theme_colors and theme_colors['font']

        font_data = dict()
        if not theme_has_custom_font and self.tab.count() > 0 and self.tab.widget(0) and hasattr(self.tab.widget(0), 'edit'):
            editor_font = self.tab.widget(0).edit.font()
            pt_size = self.tab.widget(0).edit.getFontSize()

            zoom_delta = getattr(self, '_temporary_zoom_delta', 0)
            if zoom_delta:
                pt_size = max(1, pt_size - zoom_delta)

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
            maximized=is_max,
            center=center,
            outFontSize=size,
            splitter=split_sizes,
            horizontal_splitter=horizontal_split_sizes,
            wrap=word_wrap,
            out_wrap=out_word_wrap,
            echo_execute=echo_execute,
            clear_execute=clear_execute,
            always_ontop=always_ontop,
            show_whitespace=show_whitespace,
            font=font_data,
            show_outline=show_outline,
            show_outline_button=show_outline_button,
            show_output=show_output,
            show_menus=show_menus,
            syntax_check=syntax_check,
            highlight_all_occurrences=highlight_all,
            occurrences_case_sensitive=occurrences_case_sensitive,
            prefer_single_quotes=prefer_single_quotes,
            output_bottom=output_bottom,
            quick_tab_switching=quick_tab_switching,
            auto_close_delimiters=auto_close_delimiters,
            autocomplete=autocomplete,
            fuzzy_autocomplete=fuzzy_autocomplete,
            show_docstrings=show_docstrings,
            trim_auto_whitespace=trim_auto_whitespace,
            randomize_custom_at_startup=randomize_custom,
        )
        settings.update(data)
        if 'colors' in settings:
            del settings['colors']
        self.save_settings_requested.emit(settings)

    def openSettingsFile(self):
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
        if getattr(self, 'zen_mode_act', None) and self.zen_mode_act.isChecked():
            self._updateZenModeMargins()
        super(scriptEditorClass, self).resizeEvent(event)

    def openLink(self, name, extra=""):
        webbrowser.open(f"{links[name]}{extra}")

    def openDocumentation(self):
        doc_path = os.path.join(os.path.dirname(__file__), 'docs', 'mse.html')
        webbrowser.open('file://' + doc_path.replace('\\', '/'))

    def about(self):
        dial = about.aboutClass(self)
        if hasattr(dial, 'exec'):
            dial.exec()
        else:
            dial.exec_()

    def shortcuts(self):
        dial = shortcuts.shortcutsClass(self)
        if hasattr(dial, 'exec'):
            dial.exec()
        else:
            dial.exec_()

    def findWidget(self):
        focus_widget = QApplication.focusWidget()
        target = 'input'

        if focus_widget == self.out or self.out.isAncestorOf(focus_widget):
            target = 'output'

        selected_text = ""
        if target == 'output':
            # Searching in log, center on editor (self.tab)
            center_widget = self.tab
            cursor = self.out.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
        else:
            # Searching in editor, center on log (self.out)
            center_widget = self.out
            current_widget = self.tab.currentWidget()
            if current_widget and hasattr(current_widget, 'edit'):
                cursor = current_widget.edit.textCursor()
                if cursor.hasSelection():
                    selected_text = cursor.selectedText()

        w = findWidget.findWidgetClass(self.out, center_widget)
        if selected_text:
            # Replace paragraph separators with spaces or newlines (Qt quirk)
            selected_text = selected_text.replace('\u2029', '\n')
            # Only use first line if multiline
            if '\n' in selected_text:
                selected_text = selected_text.split('\n')[0]
            if '\r' in selected_text:
                selected_text = selected_text.split('\r')[0]
            w.find_le.setText(selected_text)
            w.find_le.selectAll()

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
        self.showOutline_act.setChecked(state)
        if state:
            sizes = getattr(self, '_last_horizontal_splitter_sizes', [200, 600])
            if sizes[0] == 0:
                sizes = [200, 600]
            self.horizontal_splitter.setSizes(sizes)
            self._updateOutlineNow()
        else:
            if self.horizontal_splitter.sizes()[0] != 0:
                self._last_horizontal_splitter_sizes = self.horizontal_splitter.sizes()
            self.horizontal_splitter.setSizes([0, 800])

        if hasattr(self, 'tab') and hasattr(self.tab, 'toggleOutline_btn'):
            self.tab.toggleOutline_btn.blockSignals(True)
            self.tab.toggleOutline_btn.setChecked(state)
            self.tab.toggleOutline_btn.blockSignals(False)

    def toggleOutlineButton(self, state):
        self.showOutlineButton_act.setChecked(state)
        if hasattr(self, 'tab') and hasattr(self.tab, 'toggleOutline_btn'):
            self.tab.toggleOutline_btn.setVisible(state)

    def getDefaultSplitterSizes(self):
        bottom = self.outputBottom_act.isChecked()
        return [400, 600] if bottom else [600, 400]

    def toggleOutput(self, state=None):
        if state is None:
            state = self.showOutput_act.isChecked()
        self.showOutput_act.setChecked(state)
        if not state:
            sizes = self.splitter.sizes()
            if all(s > 0 for s in sizes):
                self._last_splitter_sizes = sizes
        self.verticalLayoutWidget.setVisible(state)
        if state:
            sizes = getattr(self, '_last_splitter_sizes', self.getDefaultSplitterSizes())
            if any(s == 0 for s in sizes):
                sizes = self.getDefaultSplitterSizes()
            self.splitter.setSizes(sizes)

    def toggleMenuBar(self, state=None):
        if state is None:
            state = self.toggleMenus_act.isChecked()
        self.menubar.setVisible(state)
        self.toggleMenus_act.setChecked(state)

    def toggleZenMode(self, state=None):
        if state is None:
            state = self.zen_mode_act.isChecked()
        self.zen_mode_act.setChecked(state)

        if state:
            geo = self.normalGeometry() if hasattr(self, 'normalGeometry') else self.geometry()
            frame_offset_x = self.geometry().x() - self.x()
            frame_offset_y = self.geometry().y() - self.y()
            
            self._zen_mode_state = {
                'fullscreen': self.isFullScreen(),
                'maximized': self.isMaximized(),
                'rect': [geo.x() - frame_offset_x, geo.y() - frame_offset_y, geo.width(), geo.height()],
                'menubar': self.toggleMenus_act.isChecked(),
                'output': self.showOutput_act.isChecked(),
                'outline': self.showOutline_act.isChecked()
            }
            if not self.isFullScreen():
                self.showFullScreen()
            if self.menubar.isVisible():
                self.toggleMenuBar(False)
            if self.verticalLayoutWidget.isVisible():
                self.toggleOutput(False)
            if self.showOutline_act.isChecked():
                self.toggleOutline(False)
            self._updateZenModeMargins()
        else:
            self.in_ly.setContentsMargins(0, 0, 0, 0)
            if hasattr(self, '_zen_mode_state'):
                if not self._zen_mode_state.get('fullscreen', False):
                    self.showNormal()
                    if self._zen_mode_state.get('maximized', False):
                        QTimer.singleShot(50, self.showMaximized)
                    elif 'rect' in self._zen_mode_state:
                        rect = self._zen_mode_state['rect']
                        def _restore_rect():
                            self.move(rect[0], rect[1])
                            self.resize(rect[2], rect[3])
                        QTimer.singleShot(50, _restore_rect)

                self.toggleMenuBar(self._zen_mode_state.get('menubar', True))
                self.toggleOutput(self._zen_mode_state.get('output', True))
                self.toggleOutline(self._zen_mode_state.get('outline', False))

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
        if hasattr(self, '_last_splitter_sizes') and self._last_splitter_sizes:
            self._last_splitter_sizes = self._last_splitter_sizes[::-1]

    def _updateZenModeMargins(self):
        from vendor.Qt.QtGui import QFontMetrics
        max_width = 1200
        if self.tab.count() > 0 and self.tab.widget(0) and hasattr(self.tab.widget(0), 'edit'):
            fm = QFontMetrics(self.tab.widget(0).edit.font())
            if hasattr(fm, 'horizontalAdvance'):
                char_width = fm.horizontalAdvance('W')
            else:
                char_width = fm.width('W')
            # 120 columns + 100 padding for line numbers and scrollbar
            max_width = (char_width * 120) + 100

        current_width = self.width()
        if current_width > max_width:
            margin = (current_width - max_width) // 2
        else:
            margin = 0
        self.in_ly.setContentsMargins(margin, 0, margin, 0)

    def saveOutputAs(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save output as", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            text = self.out.toPlainText()
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                self.messageSignal.emit(f"Failed to save output: {str(e)}")
            else:
                self.messageSignal.emit(f"Output saved to {file_path}")

    def saveOutputToTab(self):
        import time
        current_time = time.strftime("%H:%M:%S")
        tab_name = f"output {current_time}"
        text = self.out.toPlainText()
        self.tab.addNewTab(tab_name, text)

    def toggleQuickTabSwitching(self, state=None):
        if state is None:
            state = self.quickTabSwitching_act.isChecked()
        self._current_settings['quick_tab_switching'] = state
        self.saveSettings()
        if not state:
            self.tab._ctrl_pressed = False
            self.tab.show_tab_numbers(False)

    def toggleAutoCloseDelimiters(self, state=None):
        if state is None:
            state = self.autoCloseDelimiters_act.isChecked()
        self._current_settings['auto_close_delimiters'] = state
        self.saveSettings()

    def toggleSyntaxCheck(self, state=None):
        if state is None:
            state = self.syntaxCheck_act.isChecked()

        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            if hasattr(w, 'edit'):
                w.edit.runLinter()

        if not state:
            self.statusBar().clearMessage()

    def toggleHighlightAllOccurrences(self, state=None):
        if state is None:
            state = self.highlightAllOccurrences_act.isChecked()
        self._current_settings['highlight_all_occurrences'] = state
        self.saveSettings()
        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            if hasattr(w, 'edit'):
                if state:
                    w.edit.auto_select_all_occurrences()
                else:
                    if w.edit.multi_cursor_manager.has_cursors():
                        w.edit.multi_cursor_manager.clear()
                        w.edit.highlight_current_line()

    def toggleOccurrencesCaseSensitive(self, state=None):
        if state is None:
            state = self.occurrencesCaseSensitive_act.isChecked()
        self._current_settings['occurrences_case_sensitive'] = state
        self.saveSettings()
        for i in range(self.tab.count()):
            w = self.tab.widget(i)
            if hasattr(w, 'edit'):
                if self.highlightAllOccurrences_act.isChecked():
                    w.edit.auto_select_all_occurrences()

    def togglePreferSingleQuotes(self, state=None):
        if state is None:
            state = self.preferSingleQuotes_act.isChecked()
        self._current_settings['prefer_single_quotes'] = state
        self.saveSettings()

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

        ext = '.py'
        w = self.tab.widget(self.tab.currentIndex())
        if w and hasattr(w, 'file_path') and w.file_path:
             ext = os.path.splitext(w.file_path)[1].lower()

        if hasattr(edit, 'syntax_errors') and edit.syntax_errors:
            self.outline_list.clear()
            return

        self.update_outline_requested.emit(code, ext)

    def set_outline_symbols(self, symbols, ext='.py'):
        self.outline_list.clear()
        if not symbols:
            return

        self.outline_list.clear()

        theme_colors = None
        if hasattr(self, '_current_settings'):
            theme_name = self._current_settings.get('theme', 'Dark')
            theme_colors = design.getColors(theme_name)

        font = getattr(self, 'current_outline_font', self.outline_list.font())

        for sym in symbols:
            item = create_symbol_item(sym, theme_colors, font, ext=ext)
            self.outline_list.addItem(item)

    def outlineItemClicked(self, item):
        line = item.data(Qt.UserRole)
        if line:
            edit = self.tab.current()
            cursor = edit.textCursor()
            block = edit.document().findBlockByNumber(line - 1)
            cursor.setPosition(block.position())
            edit.setTextCursor(cursor)
            edit.centerCursor()
            edit.highlight_current_line()
            edit.setFocus()

    def filterOutline(self, text):
        text = text.lower()
        for i in range(self.outline_list.count()):
            item = self.outline_list.item(i)
            item.setHidden(text not in item.text().lower())

    def autoSave(self):
        if not hasattr(self, '_presenter'):
            return
        tabs = self._get_tabs_data(save_full_text=True)
        self._presenter.save_backup(tabs)

    def fillSessionsMenu(self):
        self.sessions_menu.clear()

        save_act = QAction("Save current session as...", self)
        save_act.setIcon(QIcon(icons['save']))
        save_act.setStatusTip("Save the current state as a named session")
        save_act.triggered.connect(self.saveNamedSession)
        self.sessions_menu.addAction(save_act)

        restore_backup_act = QAction("Restore crash backup", self)
        restore_backup_act.setIcon(QIcon(icons['restore_backup']))
        restore_backup_act.setStatusTip("Restore the last auto-saved backup session")
        restore_backup_act.triggered.connect(self.restoreBackupSession)
        if not self._presenter.backup_exists():
            restore_backup_act.setEnabled(False)
        self.sessions_menu.addAction(restore_backup_act)

        self.delete_session_menu = QMenu("Delete session", self)
        self.delete_session_menu.setIcon(QIcon(icons["clear"]))
        self.delete_session_menu.menuAction().setStatusTip("Delete a saved session")
        self.sessions_menu.addMenu(self.delete_session_menu)

        self.sessions_menu.addSeparator()

        names = self._presenter.get_named_sessions()
        if names:
            for name in names:
                act = QAction(name, self)
                act.setStatusTip(f"Load session: {name}")
                act.triggered.connect(lambda checked=False, n=name: self.loadNamedSession(n))
                self.sessions_menu.addAction(act)

                del_act = QAction(name, self)
                del_act.setStatusTip(f"Delete session: {name}")
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
            tabs = self._get_tabs_data(save_full_text=True)
            self._presenter.save_named_session(name, tabs)
            self.out.showMessage(">>> Named session '{0}' saved successfully.".format(name))
            self.fillSessionsMenu()

    def loadNamedSession(self, name):
        res = self.show_question_msg(
            "Load Session",
            "Loading session '{0}' will replace all current tabs. Do you want to proceed?".format(name),
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            sessions = self._presenter.get_named_session_tabs(name)
            self.loadSession(sessions)
            self.out.showMessage(">>> Loaded named session '{0}'.".format(name))

    def deleteNamedSession(self, name):
        res = self.show_question_msg(
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
                self.loadSession(sessions)
                self.out.showMessage("Crash backup restored successfully.")
            else:
                self.out.showMessage("Crash backup is empty or invalid.")
        else:
            self.out.showMessage("No crash backup found.")


    def handleSnippetShortcut(self):
        index = self.tab.currentIndex()
        if index < 0:
            return
        edit_widget = self.tab.widget(index).edit
        if edit_widget.textCursor().hasSelection():
            self.saveSnippet()
        else:
            self.insertSnippet()

    def _get_snippets(self):
        snippets_model = SnippetsModel()
        snippets_data = snippets_model.read_settings()
        user_snippets = snippets_data.get('snippets', {})
        defaults = snippets_model.get_defaults().get('snippets', {})

        if not user_snippets:
            # Fallback for migration
            settings = SettingsModel()
            old_data = settings.read_settings()
            if 'snippets' in old_data and old_data['snippets']:
                old_snippets = old_data['snippets']
                filtered_old = {k: v for k, v in old_snippets.items() if k not in defaults or defaults[k] != v}
                if filtered_old:
                    user_snippets = filtered_old
                    snippets_data['snippets'] = filtered_old
                    snippets_model.write_settings(snippets_data)

        # Build final dict with user snippets first, then defaults
        all_snippets = {}
        for k in sorted(user_snippets.keys()):
            all_snippets[k] = user_snippets[k]

        for k in sorted(defaults.keys()):
            if k not in all_snippets:
                all_snippets[k] = defaults[k]

        return all_snippets

    def _save_snippets(self, snippets_dict):
        snippets_model = SnippetsModel()
        defaults = snippets_model.get_defaults().get('snippets', {})
        user_snippets = {}
        for k, v in snippets_dict.items():
            if k not in defaults or defaults[k] != v:
                user_snippets[k] = v
        snippets_model.write_settings({'snippets': user_snippets})

    def importSnippets(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import Snippets', '', "JSON Files (*.json);;All Files (*.*)")
        if not path:
            return

        try:
            with codecs.open(path, "r", "utf-16") as stream:
                data = json.load(stream)
            imported_snippets = data.get("snippets", {})
            if not imported_snippets:
                raise ValueError("Empty or invalid format")
        except Exception:
            try:
                with codecs.open(path, "r", "utf-8") as stream:
                    data = json.load(stream)
                imported_snippets = data.get("snippets", {})
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read the file:\n{e}")
                return

        if not imported_snippets:
            QMessageBox.information(self, "Import Snippets", "No snippets found in the selected file.")
            return

        current_snippets = self._get_snippets()
        conflicts = [name for name in imported_snippets if name in current_snippets]

        overwrite = False
        if conflicts:
            reply = self.show_question_msg(
                "Import Snippets",
                f"{len(conflicts)} snippets already exist. Do you want to overwrite them?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )
            if reply == QMessageBox.Cancel:
                return
            overwrite = (reply == QMessageBox.Yes)

        added = 0
        for name, code in imported_snippets.items():
            if name in conflicts and not overwrite:
                continue
            current_snippets[name] = code
            added += 1

        if added > 0:
            self._save_snippets(current_snippets)
            self.fillSnippetsMenu()
            self.out.showMessage(f">>> Successfully imported {added} snippet(s).")
        else:
            self.out.showMessage(">>> No new snippets were imported.")

    def fillSnippetsMenu(self):
        self.snippets_menu.clear()

        self.manageSnippet_act.setIcon(QIcon(icons['snippets']))
        self.snippets_menu.addAction(self.manageSnippet_act)

        import_act = QAction("Import snippets...", self)
        import_act.setStatusTip("Import snippets from another file")
        import_act.setIcon(QIcon(icons["open"]))
        import_act.triggered.connect(self.importSnippets)
        self.snippets_menu.addAction(import_act)

        self.delete_snippet_menu = QMenu("Delete snippet", self)
        self.delete_snippet_menu.setIcon(QIcon(icons["clear"]))
        self.delete_snippet_menu.menuAction().setStatusTip("Delete a saved snippet")
        self.snippets_menu.addMenu(self.delete_snippet_menu)

        self.snippets_menu.addSeparator()

        snippets = self._get_snippets()

        if snippets:
            snippets_model = SnippetsModel()
            defaults = snippets_model.get_defaults().get('snippets', {})
            added_defaults_separator = False
            has_user_snippets = any(name not in defaults for name in snippets)

            for name in snippets.keys():
                if name in defaults and not added_defaults_separator:
                    if has_user_snippets:
                        self.snippets_menu.addSeparator()
                    added_defaults_separator = True

                act = QAction(name, self)
                act.setStatusTip(f"Insert snippet: {name}")
                act.triggered.connect(lambda checked=False, n=name: self._insert_snippet_text(snippets[n]))
                self.snippets_menu.addAction(act)

                if name not in defaults:
                    del_act = QAction(name, self)
                    del_act.setStatusTip(f"Delete snippet: {name}")
                    del_act.triggered.connect(lambda checked=False, n=name: self.deleteSnippet(n))
                    self.delete_snippet_menu.addAction(del_act)

            if not has_user_snippets:
                no_del_act = QAction("No saved snippets", self)
                no_del_act.setEnabled(False)
                self.delete_snippet_menu.addAction(no_del_act)
        else:
            no_snippets_act = QAction("No saved snippets", self)
            no_snippets_act.setEnabled(False)
            self.snippets_menu.addAction(no_snippets_act)

            no_del_act = QAction("No saved snippets", self)
            no_del_act.setEnabled(False)
            self.delete_snippet_menu.addAction(no_del_act)

    def saveSnippet(self):
        index = self.tab.currentIndex()
        if index < 0:
            return

        edit_widget = self.tab.widget(index).edit
        cursor = edit_widget.textCursor()
        selected_text = cursor.selectedText()
        # Replace the special paragraph separator used by Qt with newlines
        selected_text = selected_text.replace('\u2029', '\n')

        if not selected_text:
            self.out.showMessage(">>> No text selected to save as snippet.")
            return

        snippets = self._get_snippets()

        theme_name = self._current_settings.get('theme', 'Dark')
        qss = design.editorStyle(theme_name)
        colors = design.getColors(theme_name)

        if colors.get('use_theme_font_on_symbols', True):
            font_data = colors.get('font')
            if font_data:
                font = QFont(font_data.get('family', ''), font_data.get('pointSize', 10), font_data.get('weight', -1), font_data.get('italic', False))
            else:
                font = QFont(edit_widget.font())
        else:
            font = QApplication.font("QListWidget")

        if 'symbols_text_size' in colors:
            font.setPointSize(max(1, int(colors['symbols_text_size'])))
        else:
            font.setPointSize(max(1, int(font.pointSize() * 0.9)))

        self.snippet_widget = snippetWidget.SnippetWidget(snippets, self, edit_widget, qss=qss, font=font, colors=colors, mode="save")

        def do_save(name):
            snippets[name] = selected_text
            self._save_snippets(snippets)
            self.out.showMessage(">>> Snippet '{0}' saved successfully.".format(name))
            self.fillSnippetsMenu()

        def do_delete(name):
            if hasattr(self, 'snippet_widget') and self.snippet_widget:
                self.snippet_widget.reject()
            self.deleteSnippet(name)

        self.snippet_widget.snippetNameSelected.connect(do_save)
        self.snippet_widget.snippetDeleted.connect(do_delete)
        if hasattr(self.snippet_widget, 'exec'):
            self.snippet_widget.exec()
        else:
            self.snippet_widget.exec_()

    def insertSnippet(self):
        snippets = self._get_snippets()

        if not snippets:
            self.out.showMessage(">>> No snippets saved yet.")
            return

        theme_name = self._current_settings.get('theme', 'Dark')
        qss = design.editorStyle(theme_name)
        colors = design.getColors(theme_name)

        index = self.tab.currentIndex()
        if index < 0:
            return

        edit_widget = self.tab.widget(index).edit

        if colors.get('use_theme_font_on_symbols', True):
            font_data = colors.get('font')
            if font_data:
                font = QFont(font_data.get('family', ''), font_data.get('pointSize', 10), font_data.get('weight', -1), font_data.get('italic', False))
            else:
                font = QFont(edit_widget.font())
        else:
            font = QApplication.font("QListWidget")

        if 'symbols_text_size' in colors:
            font.setPointSize(max(1, int(colors['symbols_text_size'])))
        else:
            font.setPointSize(max(1, int(font.pointSize() * 0.9)))


        self.snippet_widget = snippetWidget.SnippetWidget(snippets, self, edit_widget, qss=qss, font=font, colors=colors)

        def do_delete(name):
            if hasattr(self, 'snippet_widget') and self.snippet_widget:
                self.snippet_widget.reject()
            self.deleteSnippet(name)

        self.snippet_widget.snippetSelected.connect(self._insert_snippet_text)
        self.snippet_widget.snippetDeleted.connect(do_delete)
        if hasattr(self.snippet_widget, 'exec'):
            self.snippet_widget.exec()
        else:
            self.snippet_widget.exec_()

    def _insert_snippet_text(self, text):
        index = self.tab.currentIndex()
        if index < 0:
            return
        edit_widget = self.tab.widget(index).edit
        cursor = edit_widget.textCursor()
        cursor.insertText(text + "\n")
        edit_widget.setFocus()

    def deleteSnippet(self, name):
        res = self.show_question_msg(
            "Delete Snippet",
            "Are you sure you want to delete snippet '{0}'?".format(name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if res == QMessageBox.Yes:
            snippets = self._get_snippets()
            if name in snippets:
                del snippets[name]
                self._save_snippets(snippets)

                snippets_model = SnippetsModel()
                defaults = snippets_model.get_defaults().get('snippets', {})
                if name in defaults:
                    self.out.showMessage(">>> Reverted snippet '{0}' to default.".format(name))
                else:
                    self.out.showMessage(">>> Deleted snippet '{0}'.".format(name))
                self.fillSnippetsMenu()

try:
    from PySide2.QtCore import QTextCodec
    QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
except:
    try:
        from PySide.QtCore import QTextCodec
        QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
    except:
        pass


def create_editor_instance(parent=None):
    w = scriptEditorClass(parent)
    return w


def show():
    app = QApplication.instance()
    if not app:
        app = QApplication()

    w = create_editor_instance()
    w.show()

    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()


if __name__ == '__main__':
    show()
