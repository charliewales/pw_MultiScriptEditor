import os
import sys
from functools import partial
from vendor.Qt.QtCore import Qt, QSize, QTimer
from vendor.Qt.QtGui import QIcon, QKeySequence
from vendor.Qt.QtWidgets import QShortcut, QMenu, QAction, QStyle
from icons import icons
import managers

class ScriptEditorUIBuilder:
    @staticmethod
    def setup_ui(editor):
        editor.execAll_act.setIcon(QIcon(icons['all']))
        editor.execLine_act.setIcon(QIcon(icons['line']))
        editor.execSel_act.setIcon(QIcon(icons['sel']))
        editor.clearHistory_act.setIcon(QIcon(icons['clear']))
        editor.toolBar.setIconSize(QSize(32, 32))
        editor.menubar.setNativeMenuBar(False)
        editor.menubar.setStyleSheet("QMenu {icon-size: 20px;}")

        # connects
        editor.load_act.triggered.connect(editor.loadScript)
        editor.load_act.setIcon(QIcon(icons['open']))
        editor.load_act.setShortcut("Ctrl+O")
        editor.save_act.triggered.connect(editor.saveScript)
        editor.save_act.setIcon(QIcon(icons['save']))
        editor.save_act.setShortcut("Ctrl+S")

        editor.recent_files_menu = QMenu("Recent Files", editor)
        editor.recent_files_menu.setIcon(QIcon(icons["file_recent"]))
        editor.file_menu.insertMenu(editor.saveSeccion_act, editor.recent_files_menu)
        editor.updateRecentFilesMenu()

        editor.saveSeccion_act.triggered.connect(lambda: editor.saveSession(True))
        editor.saveSeccion_act.setIcon(QIcon(icons['save']))
        editor.saveSeccion_act.setShortcut("Ctrl+Shift+S")
        editor.closeAllTabs_act.triggered.connect(editor.closeAllTabsWithConfirm)
        editor.closeAllTabs_act.setIcon(QIcon(icons['close_all_tabs']))
        editor.exit_act.triggered.connect(editor.close)
        editor.tabToSpaces_act.triggered.connect(editor.tabsToSpaces)
        editor.quit_act.triggered.connect(editor.close)
        editor.quit_act.setShortcut("Ctrl+Q")
        editor.quit_act.setIcon(QIcon(icons['quit']))

        editor.duplicateLine_act.setShortcut('Ctrl+Shift+D')
        editor.duplicateLine_act.setShortcutContext(Qt.WidgetShortcut)
        editor.duplicateLine_act.setIcon(QIcon(icons['duplicate_line']))
        editor.deleteLine_act.setShortcut('Ctrl+D')
        editor.deleteLine_act.setShortcutContext(Qt.WidgetShortcut)
        editor.deleteLine_act.setIcon(QIcon(icons['delete_line']))

        editor.set_font_act.triggered.connect(editor.choose_font)
        editor.set_font_act.setIcon(QIcon(icons['font']))

        editor.settingsFile_act.triggered.connect(editor.openSettingsFile)
        editor.settingsFile_act.setIcon(QIcon(icons['settings']))

        editor.theme_menu.setIcon(QIcon(icons['theme']))

        editor.donate_act.triggered.connect(lambda: editor.openLink('donate'))
        editor.openManual_act.triggered.connect(lambda: editor.openLink('manual'))
        editor.openManual_act.setIcon(QIcon(icons['github']))

        editor.python_act.triggered.connect(
            lambda: editor.openLink(
                "python{0}".format(sys.version_info.major), f".{sys.version_info.minor}")
        )
        editor.python_act.setIcon(QIcon(icons['python']))

        editor.houdini_hou_act.triggered.connect(lambda: editor.openLink('houdini_hou'))
        editor.houdini_hou_act.setIcon(QIcon(icons['houdini']))
        editor.houdini_envs_act.triggered.connect(lambda: editor.openLink('houdini_envs'))
        editor.houdini_envs_act.setIcon(QIcon(icons['houdini']))
        editor.maya_cmds_act.triggered.connect(lambda: editor.openLink('maya_cmds'))
        editor.maya_cmds_act.setIcon(QIcon(icons['maya']))
        editor.nuke_dev_guide_act.triggered.connect(lambda: editor.openLink('nuke_dev_guide'))
        editor.nuke_dev_guide_act.setIcon(QIcon(icons['nuke']))

        import vendor.Qt
        editor.qt_docs_act.triggered.connect(
            lambda: editor.openLink(f"qt{'6' if vendor.Qt.IsPySide6 else '5'}_docs")
        )
        editor.qt_docs_act.setIcon(QIcon(icons['qt']))
        editor.qt_modules_act.triggered.connect(
            lambda: editor.openLink(f"qt{'6' if vendor.Qt.IsPySide6 else '5'}_modules")
        )
        editor.qt_modules_act.setIcon(QIcon(icons['qt']))

        editor.about_act.triggered.connect(editor.about)
        editor.about_act.setIcon(QIcon(icons['about']))
        editor.help_act.setIcon(QIcon(icons['sel']))
        editor.shortcuts_act.triggered.connect(editor.shortcuts)
        editor.shortcuts_act.setIcon(QIcon(icons['shortcut']))

        editor.documentation_act.triggered.connect(editor.openDocumentation)
        editor.documentation_act.setIcon(QIcon(icons['pw']))
        editor.printHelp_act.triggered.connect(editor.mse_help)
        editor.printHelp_act.setIcon(QIcon(icons['print_help']))
        
        # editor
        editor.undo_act.triggered.connect(editor.tab.undo)
        editor.undo_act.setShortcut('Ctrl+Z')
        editor.undo_act.setShortcutContext(Qt.WidgetShortcut)
        editor.undo_act.setIcon(QIcon(icons['undo']))

        editor.redo_act.triggered.connect(editor.tab.redo)
        editor.redo_act.setShortcut('Ctrl+Y')
        editor.redo_act.setShortcutContext(Qt.WidgetShortcut)
        editor.redo_act.setIcon(QIcon(icons['redo']))

        editor.copy_act.triggered.connect(editor.tab.copy)
        editor.copy_act.setShortcut('Ctrl+C')
        editor.copy_act.setShortcutContext(Qt.WidgetShortcut)
        editor.copy_act.setIcon(QIcon(icons['copy']))

        editor.cut_act.triggered.connect(editor.tab.cut)
        editor.cut_act.setShortcut('Ctrl+X')
        editor.cut_act.setShortcutContext(Qt.WidgetShortcut)
        editor.cut_act.setIcon(QIcon(icons['cut']))

        editor.paste_act.triggered.connect(editor.tab.paste)
        editor.paste_act.setShortcut('Ctrl+V')
        editor.paste_act.setShortcutContext(Qt.WidgetShortcut)
        editor.paste_act.setIcon(QIcon(icons['paste']))

        editor.find_act.triggered.connect(editor.findWidget)
        editor.find_act.setShortcut('Ctrl+F')
        editor.find_act.setShortcutContext(Qt.WindowShortcut)
        editor.find_act.setIcon(QIcon(icons['replace']))

        editor.tabToSpaces_act.setIcon(QIcon(icons['tabs_to_spaces']))

        editor.print_command_act.setCheckable(True)

        editor.clear_exec_act.triggered.connect(editor.show_clear_exec)
        editor.clear_exec_act.setShortcut('Ctrl+Alt+C')
        editor.clear_exec_act.setShortcutContext(Qt.WindowShortcut)
        editor.clear_exec_act.setCheckable(True)

        editor.whitespace_act.triggered.connect(editor.render_whitespace)
        editor.whitespace_act.setShortcut('Ctrl+Shift+W')
        editor.whitespace_act.setShortcutContext(Qt.WindowShortcut)
        editor.whitespace_act.setCheckable(True)

        editor.out_wordWrap_act.triggered.connect(editor.out.wordWrap)
        editor.out_wordWrap_act.setShortcut('Ctrl+Alt+W')
        editor.out_wordWrap_act.setShortcutContext(Qt.WindowShortcut)
        editor.out_wordWrap_act.setCheckable(True)

        editor.wordWrap_act.triggered.connect(editor.tab.wordWrap)
        editor.wordWrap_act.setShortcut('Alt+W')
        editor.wordWrap_act.setShortcutContext(Qt.WindowShortcut)
        editor.wordWrap_act.setCheckable(True)

        editor.moveLineUp_act.triggered.connect(editor.tab.move_line_up)
        editor.moveLineUp_act.setShortcut('Alt+Up')
        editor.moveLineUp_act.setShortcutContext(Qt.WidgetShortcut)
        editor.moveLineUp_act.setIcon(QIcon(icons["move_line_up"]))

        editor.moveLineDown_act.triggered.connect(editor.tab.move_line_down)
        editor.moveLineDown_act.setShortcut('Alt+Down')
        editor.moveLineDown_act.setShortcutContext(Qt.WidgetShortcut)
        editor.moveLineDown_act.setIcon(QIcon(icons["move_line_down"]))

        editor.comment_cat.triggered.connect(editor.tab.comment)
        editor.comment_cat.setShortcut('Alt+C')
        editor.comment_cat.setShortcutContext(Qt.WidgetShortcut)
        editor.comment_cat.setIcon(QIcon(icons['comment']))

        editor.add_quotes_act.triggered.connect(editor.tab.addQuotes)
        editor.add_quotes_act.setShortcut('Alt+Q')
        editor.add_quotes_act.setShortcutContext(Qt.WidgetShortcut)
        editor.add_quotes_act.setIcon(QIcon(icons['add_quotes']))

        editor.autocomplete_act.setShortcut('Alt+A')
        editor.autocomplete_act.setShortcutContext(Qt.WindowShortcut)
        QShortcut(QKeySequence("Alt+Q"), editor, editor.tab.addQuotes)

        editor.selectNextOccurrence_act.triggered.connect(editor.tab.selectNextOccurrence)
        editor.selectNextOccurrence_act.setShortcut('Ctrl+Alt+D')
        editor.selectNextOccurrence_act.setShortcutContext(Qt.WindowShortcut)
        editor.selectNextOccurrence_act.setIcon(QIcon(icons["replace"]))

        editor.selectAllOccurrences_act.triggered.connect(editor.tab.selectAllOccurrences)
        editor.selectAllOccurrences_act.setShortcut('Ctrl+Shift+Alt+D')
        editor.selectAllOccurrences_act.setShortcutContext(Qt.WindowShortcut)
        editor.selectAllOccurrences_act.setIcon(QIcon(icons["replace"]))

        editor.always_ontop_act.triggered.connect(editor.always_ontop)
        editor.always_ontop_act.setShortcutContext(Qt.WidgetShortcut)
        editor.always_ontop_act.setCheckable(True)

        dir_f = partial(editor.function_cmd, 'dir')
        editor.dir_act.triggered.connect(dir_f)
        editor.dir_act.setShortcut('Alt+D')
        editor.dir_act.setIcon(QIcon(icons['sel']))
        editor.dir_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+d'), editor, dir_f)

        help_f = partial(editor.function_cmd, 'help')
        editor.help_act.triggered.connect(help_f)
        editor.help_act.setShortcut('Alt+H')
        editor.help_act.setIcon(QIcon(icons['sel']))
        editor.help_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+h'), editor, help_f)

        print_f = partial(editor.function_cmd, "print")
        editor.print_act.triggered.connect(print_f)
        editor.print_act.setShortcut("Alt+e")
        editor.print_act.setIcon(QIcon(icons["sel"]))
        editor.print_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence("Alt+e"), editor, print_f)

        type_f = partial(editor.function_cmd, 'type')
        editor.type_act.triggered.connect(type_f)
        editor.type_act.setShortcut('Alt+T')
        editor.type_act.setIcon(QIcon(icons['sel']))
        editor.type_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('Alt+t'), editor, type_f)

        editor.quick_help_act.triggered.connect(editor.get_word_help)
        editor.quick_help_act.setShortcut('F1')
        editor.quick_help_act.setIcon(QIcon(icons['help']))
        editor.quick_help_act.setShortcutContext(Qt.WidgetShortcut)
        QShortcut(QKeySequence('F1'), editor, editor.get_word_help)

        editor.fillThemeMenu()

        # shortcuts
        if managers.context == 'nuke':
            import nuke
            if nuke.NUKE_VERSION_MAJOR > 8:
                editor.execSel_act.setShortcut('Ctrl+Return')
                editor.execSel_act.setShortcutContext(Qt.ApplicationShortcut)

        editor.execSel_act.triggered.connect(editor.executeSelected)
        editor.execSel_act.setShortcut('Ctrl+Return')
        editor.execSel_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)

        QShortcut(QKeySequence('Ctrl+Enter'), editor, editor.executeSelected)

        editor.execAll_act.triggered.connect(editor.executeAll)
        editor.execAll_act.setShortcut('Alt+Return')
        editor.execAll_act.setShortcutContext(Qt.ApplicationShortcut)

        QShortcut(QKeySequence('Alt+Enter'), editor, editor.executeAll)

        editor.execLine_act.setShortcut('Ctrl+Shift+Return')
        editor.execLine_act.triggered.connect(editor.executeLine)
        editor.execLine_act.setShortcutContext(Qt.ApplicationShortcut)

        QShortcut(QKeySequence('Ctrl+Shift+Enter'), editor, editor.executeLine)

        editor.clearHistory_act.triggered.connect(editor.clearHistory)
        editor.clearHistory_act.setShortcut('Ctrl+Shift+C')

        # hide
        editor.donate_act.setVisible(False)

        # Create status bar
        editor.statusBar()

        # Outline toggle setup
        editor.showOutline_act.setShortcut("Ctrl+Shift+O")
        editor.showOutline_act.triggered.connect(editor.toggleOutline)

        # Syntax Check toggle setup
        editor.syntaxCheck_act.triggered.connect(editor.toggleSyntaxCheck)
        
        # Output Bottom toggle setup
        editor.outputBottom_act.triggered.connect(editor.toggleOutputBottom)

        editor.outline_timer = QTimer(editor)
        editor.outline_timer.setSingleShot(True)
        editor.outline_timer.timeout.connect(editor._updateOutlineNow)

        # Sessions Submenu in File menu
        editor.sessions_menu = QMenu("Sessions", editor)
        editor.sessions_menu.setIcon(QIcon(icons['open']))
        editor.file_menu.insertMenu(editor.saveSeccion_act, editor.sessions_menu)
