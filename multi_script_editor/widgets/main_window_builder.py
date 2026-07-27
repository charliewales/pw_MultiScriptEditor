import sys
from functools import partial

import managers
import vendor.Qt
from icons import icons
from vendor.Qt.QtCore import QSize, Qt, QTimer
from vendor.Qt.QtGui import QIcon, QKeySequence
from vendor.Qt.QtWidgets import QAction, QMenu, QShortcut


class ScriptEditorUIBuilder:
    @staticmethod
    def setup_ui(editor):
        editor.execAll_act.setIcon(QIcon(icons['all']))
        editor.execLine_act.setIcon(QIcon(icons['line']))
        editor.execSel_act.setIcon(QIcon(icons['sel']))
        editor.clearHistory_act.setIcon(QIcon(icons['clear']))

        # connects
        editor.load_act.triggered.connect(editor.loadScript)
        editor.load_act.setIcon(QIcon(icons['open']))
        editor.load_act.setShortcut("Ctrl+O")
        editor.diffTool_act.triggered.connect(editor.openDiffDialog)
        editor.diffTool_act.setIcon(QIcon(icons['git_diff']))
        editor.diffTool_act.setShortcut("Ctrl+Alt+Shift+C")
        editor.save_act.triggered.connect(editor.saveScript)
        editor.save_act.setIcon(QIcon(icons['save']))
        editor.save_act.setShortcut("Ctrl+S")
        editor.saveAs_act.triggered.connect(editor.saveScriptAs)
        editor.saveAs_act.setIcon(QIcon(icons['save']))
        editor.saveAs_act.setShortcut("Ctrl+Shift+S")

        editor.saveSeccion_act.triggered.connect(lambda: editor.saveSession(True))
        editor.saveSeccion_act.setIcon(QIcon(icons['save']))
        editor.saveSeccion_act.setShortcut("Ctrl+Alt+S")
        editor.closeAllTabs_act.triggered.connect(editor.closeAllTabsWithConfirm)
        editor.closeAllTabs_act.setIcon(QIcon(icons['close_all_tabs']))
        editor.closeAllTabs_act.setShortcut("Ctrl+Shift+Alt+W")
        editor.exit_act.triggered.connect(editor.close)
        editor.tabToSpaces_act.triggered.connect(editor.tabsToSpaces)
        editor.showAutocomplete_act.triggered.connect(editor.show_autocompletion)
        editor.showAutocomplete_act.setIcon(QIcon(icons['show_autocomplete']))
        editor.trimWhitespace_act.triggered.connect(editor.trimTrailingWhitespace)
        editor.trimWhitespace_act.setIcon(QIcon(icons['trim_whitespace']))
        editor.quit_act.triggered.connect(editor.close)
        editor.quit_act.setShortcut("Ctrl+Q")
        editor.quit_act.setIcon(QIcon(icons['quit']))

        editor.duplicateLine_act.setShortcut('Ctrl+Shift+D')
        editor.duplicateLine_act.setShortcutContext(Qt.WidgetShortcut)
        editor.duplicateLine_act.setIcon(QIcon(icons['duplicate_line']))
        editor.duplicateLine_act.triggered.connect(editor.duplicateLine)

        editor.deleteLine_act.setShortcut('Ctrl+D')
        editor.deleteLine_act.setShortcutContext(Qt.WidgetShortcut)
        editor.deleteLine_act.setIcon(QIcon(icons['delete_line']))
        editor.deleteLine_act.triggered.connect(editor.deleteLine)

        editor.set_font_act.triggered.connect(editor.choose_font)
        editor.set_font_act.setIcon(QIcon(icons['font']))

        editor.settingsFile_act.triggered.connect(editor.openSettingsFile)
        editor.settingsFile_act.setIcon(QIcon(icons['settings']))

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
        editor.documentation_act.setIcon(QIcon(icons['docs']))
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
        editor.clipboardManager_act.triggered.connect(editor.tab.showClipboardManager)
        editor.clipboardManager_act.setShortcut('Ctrl+Shift+V')
        editor.clipboardManager_act.setShortcutContext(Qt.WindowShortcut)
        editor.clipboardManager_act.setIcon(QIcon(icons['paste']))

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

        editor.addCursorsToLineEnds_act.triggered.connect(editor.tab.addCursorsToLineEnds)
        editor.addCursorsToLineEnds_act.setShortcut('Ctrl+Shift+I')
        editor.addCursorsToLineEnds_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorsToLineEnds_act.setIcon(QIcon(icons['add_cursors_to_line_ends']))

        editor.addCursorAbove_act.triggered.connect(editor.tab.addCursorAbove)
        editor.addCursorAbove_act.setShortcut('Ctrl+Shift+Up')
        editor.addCursorAbove_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorAbove_act.setIcon(QIcon(icons['add_cursor_above']))

        editor.addCursorBelow_act.triggered.connect(editor.tab.addCursorBelow)
        editor.addCursorBelow_act.setShortcut('Ctrl+Shift+Down')
        editor.addCursorBelow_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorBelow_act.setIcon(QIcon(icons['add_cursor_below']))

        editor.find_act.triggered.connect(editor.findWidget)
        editor.find_act.setShortcut('Ctrl+F')
        editor.find_act.setShortcutContext(Qt.WindowShortcut)
        editor.find_act.setIcon(QIcon(icons['replace']))

        editor.commandPalette_act.triggered.connect(editor.openCommandPalette)
        editor.commandPalette_act.setShortcut('Ctrl+Shift+P')
        editor.commandPalette_act.setShortcutContext(Qt.WindowShortcut)
        if 'shortcut' in icons:
            editor.commandPalette_act.setIcon(QIcon(icons['shortcut']))

        editor.gitAction_act.triggered.connect(editor.openGitPopup)
        # Ctrl+Shift+G is set in retranslateUi but setting it here for context explicitly
        editor.gitAction_act.setShortcut('Ctrl+Shift+G')
        editor.gitAction_act.setShortcutContext(Qt.WindowShortcut)
        if 'git' in icons:
            editor.gitAction_act.setIcon(QIcon(icons['git']))

        editor.gotoLine_act.triggered.connect(editor.gotoLine)
        editor.gotoLine_act.setShortcut('Ctrl+G')
        editor.gotoLine_act.setShortcutContext(Qt.WindowShortcut)
        editor.gotoLine_act.setIcon(QIcon(icons['goto_line']))

        editor.goToSymbol_act.triggered.connect(editor.goToSymbol)
        editor.goToSymbol_act.setShortcut('Ctrl+R')
        editor.goToSymbol_act.setShortcutContext(Qt.WindowShortcut)
        editor.goToSymbol_act.setIcon(QIcon(icons['goto_symbol']))

        recent_files_sc = QShortcut(QKeySequence('Ctrl+P'), editor)
        recent_files_sc.setContext(Qt.ApplicationShortcut)
        recent_files_sc.activated.connect(editor.showRecentFiles)
        editor._recent_files_sc = recent_files_sc

        open_tabs_sc = QShortcut(QKeySequence('Ctrl+Tab'), editor)
        open_tabs_sc.setContext(Qt.ApplicationShortcut)
        open_tabs_sc.activated.connect(editor.showOpenTabs)
        editor._open_tabs_sc = open_tabs_sc

        editor.tabToSpaces_act.setIcon(QIcon(icons['tabs_to_spaces']))

        editor.spacesToTabs_act.triggered.connect(editor.spacesToTabs)
        editor.spacesToTabs_act.setIcon(QIcon(icons['spaces_to_tabs']))

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

        editor.f_string_act.triggered.connect(editor.tab.fString)
        editor.f_string_act.setShortcut('Alt+F')
        editor.f_string_act.setShortcutContext(Qt.WidgetShortcut)
        editor.f_string_act.setIcon(QIcon(icons['f_string']))

        editor.zoom_in_act.triggered.connect(partial(editor.change_global_font_size, True))
        editor.zoom_in_act.setShortcutContext(Qt.WindowShortcut)
        editor.zoom_in_act.setIcon(QIcon(icons['zoom_in']))

        editor.zoom_out_act.triggered.connect(partial(editor.change_global_font_size, False))
        editor.zoom_out_act.setShortcutContext(Qt.WindowShortcut)
        editor.zoom_out_act.setIcon(QIcon(icons['zoom_out']))

        editor.reset_zoom_act.triggered.connect(editor.restore_global_font_size)
        editor.reset_zoom_act.setShortcut('Ctrl+0')
        editor.reset_zoom_act.setShortcutContext(Qt.WindowShortcut)
        editor.reset_zoom_act.setIcon(QIcon(icons['zoom_reset']))

        editor.fold_act.triggered.connect(editor.fold_current)
        editor.fold_act.setShortcut('Alt+-')
        editor.fold_act.setShortcutContext(Qt.WindowShortcut)
        editor.fold_act.setIcon(QIcon(icons['fold']))

        editor.unfold_act.triggered.connect(editor.unfold_current)
        editor.unfold_act.setShortcut('Alt++')
        editor.unfold_act.setShortcutContext(Qt.WindowShortcut)
        editor.unfold_act.setIcon(QIcon(icons['unfold']))

        editor.fold_all_act.triggered.connect(editor.fold_all)
        editor.fold_all_act.setShortcut('Alt+Shift+-')
        editor.fold_all_act.setShortcutContext(Qt.WindowShortcut)
        editor.fold_all_act.setIcon(QIcon(icons['fold_all']))

        editor.unfold_all_act.triggered.connect(editor.unfold_all)
        editor.unfold_all_act.setShortcut('Alt+Shift++')
        editor.unfold_all_act.setShortcutContext(Qt.WindowShortcut)
        editor.unfold_all_act.setIcon(QIcon(icons['unfold_all']))

        editor.autocomplete_act.setShortcut('Alt+A')
        editor.autocomplete_act.setShortcutContext(Qt.WindowShortcut)
        QShortcut(QKeySequence("Alt+Q"), editor, editor.tab.addQuotes)
        QShortcut(QKeySequence("Alt+f"), editor, editor.tab.fString)

        editor.selectNextOccurrence_act.triggered.connect(editor.tab.selectNextOccurrence)
        editor.selectNextOccurrence_act.setShortcut('Ctrl+Alt+D')
        editor.selectNextOccurrence_act.setShortcutContext(Qt.WindowShortcut)
        editor.selectNextOccurrence_act.setIcon(QIcon(icons["select_next_occurrence"]))

        editor.nextSelection_act.triggered.connect(editor.tab.nextSelection)
        editor.nextSelection_act.setShortcut('Ctrl+J')
        editor.nextSelection_act.setShortcutContext(Qt.WindowShortcut)
        editor.nextSelection_act.setIcon(QIcon(icons["down"]))

        editor.previousSelection_act.triggered.connect(editor.tab.previousSelection)
        editor.previousSelection_act.setShortcut('Ctrl+Shift+J')
        editor.previousSelection_act.setShortcutContext(Qt.WindowShortcut)
        editor.previousSelection_act.setIcon(QIcon(icons["up"]))


        editor.selectAllOccurrences_act.triggered.connect(editor.tab.selectAllOccurrences)
        editor.selectAllOccurrences_act.setShortcut('Ctrl+Shift+Alt+D')
        editor.selectAllOccurrences_act.setShortcutContext(Qt.WindowShortcut)
        editor.selectAllOccurrences_act.setIcon(QIcon(icons["select_all_occurrences"]))

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

        QShortcut(QKeySequence('Ctrl+='), editor, partial(editor.change_global_font_size, True))

        # hide
        editor.donate_act.setIcon(QIcon(icons["donate"]))

        # Create status bar
        editor.statusBar()
        # Explorer toggle setup
        editor.showExplorer_act.setShortcut("Ctrl+E")
        editor.showExplorer_act.setShortcutContext(Qt.WindowShortcut)
        editor.showExplorer_act.triggered.connect(editor.toggleExplorer)

        # Outline toggle setup
        editor.showOutline_act.setShortcut("Ctrl+Shift+O")
        editor.showOutline_act.setShortcutContext(Qt.WindowShortcut)
        editor.showOutline_act.triggered.connect(editor.toggleOutline)

        # Syntax Check toggle setup
        editor.syntaxCheck_act.triggered.connect(editor.toggleSyntaxCheck)

        editor.highlightAllOccurrences_act.triggered.connect(editor.toggleHighlightAllOccurrences)
        editor.occurrencesCaseSensitive_act.triggered.connect(editor.toggleOccurrencesCaseSensitive)
        editor.preferSingleQuotes_act.triggered.connect(editor.togglePreferSingleQuotes)

        # Output Bottom toggle setup
        editor.outputBottom_act.setShortcut("Ctrl+U")
        editor.outputBottom_act.setShortcutContext(Qt.WindowShortcut)
        editor.outputBottom_act.triggered.connect(editor.toggleOutputBottom)
        editor.addAction(editor.outputBottom_act)

        # Output toggle setup
        editor.showOutput_act.setShortcut("Ctrl+K")
        editor.showOutput_act.setShortcutContext(Qt.WindowShortcut)
        editor.showOutput_act.triggered.connect(editor.toggleOutput)
        editor.addAction(editor.showOutput_act)

        # Menus toggle setup
        editor.toggleMenus_act.setShortcutContext(Qt.WindowShortcut)
        editor.toggleMenus_act.triggered.connect(editor.toggleMenuBar)
        editor.addAction(editor.toggleMenus_act)

        # Editor Toolbar toggle setup
        editor.toggleEditorToolbar_act.setShortcut("Ctrl+Alt+T")
        editor.toggleEditorToolbar_act.setShortcutContext(Qt.WindowShortcut)
        editor.toggleEditorToolbar_act.setChecked(True)
        editor.toggleEditorToolbar_act.toggled.connect(editor.editor_toolbar.setVisible)
        editor.toggleEditorToolbar_act.toggled.connect(editor.saveSettings)
        editor.addAction(editor.toggleEditorToolbar_act)

        # Zen mode toggle setup

        # Auto Close Delimiters toggle setup
        editor.autoCloseDelimiters_act.triggered.connect(editor.toggleAutoCloseDelimiters)

        # Quick Tab Switching toggle setup
        editor.quickTabSwitching_act.triggered.connect(editor.toggleQuickTabSwitching)

        # Show Status Tips setup
        editor.showStatusTips_act.setChecked(True)
        editor.showStatusTips_act.triggered.connect(editor.toggleStatusTips)

        # Version Control (Git) setup
        editor.versionControl_act.setChecked(False)
        editor.versionControl_act.setShortcut('Ctrl+Alt+G')
        editor.versionControl_act.setShortcutContext(Qt.WindowShortcut)
        editor.versionControl_act.triggered.connect(editor.toggleVersionControl)

        editor.outline_timer = QTimer(editor)
        editor.outline_timer.setSingleShot(True)
        editor.outline_timer.timeout.connect(editor._updateOutlineNow)

        # Recent files Submenu
        editor.recent_files_menu = QMenu("Recent files    Ctrl+P", editor)
        editor.recent_files_menu.setIcon(QIcon(icons["file_recent"]))
        editor.file_menu.insertMenu(editor.closeAllTabs_act, editor.recent_files_menu)
        editor.file_menu.insertSeparator(editor.closeAllTabs_act)
        editor.updateRecentFilesMenu()

        # Save output Submenu
        editor.saveOutput_menu = QMenu("Save output", editor)
        editor.saveOutput_menu.setIcon(QIcon(icons['save']))
        editor.saveOutputAs_act = QAction("As...", editor)
        editor.saveOutputAs_act.setIcon(QIcon(icons['save_output_as']))
        editor.saveOutputToTab_act = QAction("To tab", editor)
        editor.saveOutputToTab_act.setIcon(QIcon(icons['save_output_to_tab']))
        editor.saveOutput_menu.addAction(editor.saveOutputAs_act)
        editor.saveOutput_menu.addAction(editor.saveOutputToTab_act)

        editor.saveOutputAs_act.triggered.connect(editor.saveOutputAs)
        editor.saveOutputToTab_act.triggered.connect(editor.saveOutputToTab)

        editor.file_menu.insertMenu(editor.closeAllTabs_act, editor.saveOutput_menu)
        editor.file_menu.insertSeparator(editor.closeAllTabs_act)

        # Sessions Submenu in File menu
        editor.sessions_menu = QMenu("Sessions", editor)
        editor.sessions_menu.menuAction().setStatusTip("Manage and load saved sessions")
        target_menu_act = editor.theme_menu.menuAction() if hasattr(editor, 'theme_menu') and hasattr(editor.theme_menu, 'menuAction') else editor.view_menu.menuAction()
        editor.menubar.insertMenu(target_menu_act, editor.sessions_menu)

        # Snippets Submenu
        editor.snippets_menu = QMenu("Snippets", editor)
        editor.snippets_menu.menuAction().setStatusTip("Manage code snippets")
        editor.menubar.insertMenu(target_menu_act, editor.snippets_menu)

        # Snippets actions shortcuts
        editor.manageSnippet_act = QAction("Insert/run/save snippet", editor)
        editor.manageSnippet_act.setShortcut('Alt+S')
        editor.manageSnippet_act.setShortcutContext(Qt.WindowShortcut)
        editor.manageSnippet_act.triggered.connect(editor.handleSnippetShortcut)
        editor.addAction(editor.manageSnippet_act)

        # Plugin search action shortcut
        editor.searchPlugin_act = QAction("Search/Run plugin", editor)
        editor.searchPlugin_act.setShortcut('Alt+P')
        editor.searchPlugin_act.setShortcutContext(Qt.WindowShortcut)
        editor.searchPlugin_act.triggered.connect(editor.handlePluginShortcut)
        editor.addAction(editor.searchPlugin_act)

        # Create Bookmarks actions
        editor.toggleBookmark_act = QAction("Toggle Bookmark", editor)
        editor.toggleBookmark_act.setShortcut("Ctrl+F2")
        editor.toggleBookmark_act.setIcon(QIcon(icons.get('bookmark_toggle', '')))
        editor.toggleBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.toggle_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)
        editor.addAction(editor.toggleBookmark_act)

        editor.nextBookmark_act = QAction("Next Bookmark", editor)
        editor.nextBookmark_act.setShortcut("F2")
        editor.nextBookmark_act.setIcon(QIcon(icons.get('bookmark_next', '')))
        editor.nextBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.next_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)
        editor.addAction(editor.nextBookmark_act)

        editor.prevBookmark_act = QAction("Previous Bookmark", editor)
        editor.prevBookmark_act.setShortcut("Shift+F2")
        editor.prevBookmark_act.setIcon(QIcon(icons.get('bookmark_prev', '')))
        editor.prevBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.prev_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)
        editor.addAction(editor.prevBookmark_act)

        editor.clearBookmarks_act = QAction("Clear Bookmarks", editor)
        editor.clearBookmarks_act.setShortcut("Ctrl+Shift+F2")
        editor.clearBookmarks_act.setIcon(QIcon(icons.get('clear', '')))
        editor.clearBookmarks_act.triggered.connect(lambda: editor.tab.currentWidget().edit.clear_bookmarks() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)
        editor.addAction(editor.clearBookmarks_act)

        editor.bookmarksFinder_act = QAction("Go to bookmark...", editor)
        editor.bookmarksFinder_act.setShortcut("Ctrl+B")
        editor.bookmarksFinder_act.setIcon(QIcon(icons.get('goto_line', '')))
        editor.bookmarksFinder_act.triggered.connect(lambda: editor.tab.currentWidget().edit.show_bookmarks_popup() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)
        editor.addAction(editor.bookmarksFinder_act)

        # Create Bookmarks menu
        editor.bookmarks_menu = QMenu("Bookmarks", editor)
        editor.bookmarks_menu.setTearOffEnabled(True)
        editor.bookmarks_menu.addAction(editor.toggleBookmark_act)
        editor.bookmarks_menu.addAction(editor.nextBookmark_act)
        editor.bookmarks_menu.addAction(editor.prevBookmark_act)
        editor.bookmarks_menu.addAction(editor.clearBookmarks_act)
        editor.bookmarks_menu.addSeparator()
        editor.bookmarks_menu.addAction(editor.bookmarksFinder_act)

        # Status tips for actions
        status_tips = {
            editor.about_act: "Show information about the application",
            editor.add_quotes_act: "Add quotes around selected text or select text inside quotes",
            editor.addCursorAbove_act: "Add a cursor above the current line",
            editor.addCursorBelow_act: "Add a cursor below the current line",
            editor.addCursorsToLineEnds_act: "Add cursors to the end of each selected line",
            editor.always_ontop_act: "Keep the application window always on top",
            editor.autoCloseDelimiters_act: "Automatically close brackets, braces, and quotes",
            editor.autocomplete_act: "Toggle code autocomplete functionality",
            editor.bookmarksFinder_act: "Search and navigate bookmarked lines",
            editor.clear_exec_act: "Clear the output panel before executing code",
            editor.clearBookmarks_act: "Clear all bookmarks in the current document",
            editor.clearHistory_act: "Clear the output panel history",
            editor.clipboardManager_act: "Show the clipboard history manager",
            editor.closeAllTabs_act: "Close all open script tabs",
            editor.commandPalette_act: "Open Command Palette for quick search of editor actions (Ctrl+Shift+P)",
            editor.comment_cat: "Toggle comment on the current line or selection",
            editor.copy_act: "Copy the selected text to clipboard",
            editor.cut_act: "Cut the selected text to clipboard",
            editor.deleteLine_act: "Delete the current line",
            editor.dir_act: "Execute dir() on the selected text",
            editor.documentation_act: "Open Multi Script Editor documentation",
            editor.donate_act: "Support the development of Multi Script Editor",
            editor.duplicateLine_act: "Duplicate the current line or selection",
            editor.editTheme_act: "Edit the current color theme",
            editor.execAll_act: "Execute all code in the current tab",
            editor.execLine_act: "Execute the current line",
            editor.execSel_act: "Execute the selected code or current line",
            editor.exit_act: "Close the application",
            editor.f_string_act: "Create an f-string from the current selection or clipboard",
            editor.find_act: "Find and replace text in the editor",
            editor.fold_act: "Fold the current code block",
            editor.fold_all_act: "Fold all code blocks",
            editor.fuzzy_autocomplete_act: "Toggle fuzzy code autocomplete functionality",
            editor.gitAction_act: "Perform Git actions or show Git context menu",
            editor.gotoLine_act: "Go to a specific line in the editor",
            editor.goToSymbol_act: "Go to a symbol in the editor",
            editor.help_act: "Execute help() on the selected text",
            editor.highlightAllOccurrences_act: "Highlight all occurrences of the selected text",
            editor.houdini_envs_act: "Open Houdini environment variables documentation",
            editor.houdini_hou_act: "Open Houdini hou package documentation",
            editor.load_act: "Open an existing script file",
            editor.manageSnippet_act: "Insert(Return)/Run(Enter) a snippet, or save selection as a new snippet",
            editor.maya_cmds_act: "Open Maya commands documentation",
            editor.moveLineDown_act: "Move the current line or selection down",
            editor.moveLineUp_act: "Move the current line or selection up",
            editor.nextBookmark_act: "Navigate to the next bookmark",
            editor.nextSelection_act: "Move to the next selection",
            editor.nuke_dev_guide_act: "Open Nuke Developer Guide",
            editor.occurrencesCaseSensitive_act: "If enabled, case sensitive will be used when selecting occurrences",
            editor.openManual_act: "Open the GitHub repository and manual",
            editor.out_wordWrap_act: "Toggle word wrap in the output panel",
            editor.outputBottom_act: "Move the output panel to the bottom of the window",
            editor.paste_act: "Paste text from the clipboard",
            editor.preferSingleQuotes_act: "If enabled, single quotes will be used when adding quotes and f-strings",
            editor.prevBookmark_act: "Navigate to the previous bookmark",
            editor.previousSelection_act: "Move to the previous selection",
            editor.print_act: "Execute print() on the selected text",
            editor.print_command_act: "Echo executed commands in the output panel",
            editor.printHelp_act: "Print Multi Script Editor help in the output",
            editor.python_act: "Open the official Python documentation",
            editor.qt_docs_act: "Open Qt for Python documentation",
            editor.qt_modules_act: "Open Qt Modules documentation",
            editor.quick_help_act: "Show quick help for the current word",
            editor.quickHelp_act: "Show quick help for the current word",
            editor.quickTabSwitching_act: "Enable switching tabs using Ctrl+1, Ctrl+2, etc., and display tab numbers when holding Ctrl",
            editor.quit_act: "Quit the application",
            editor.redo_act: "Redo the last action",
            editor.reset_zoom_act: "Reset the editor font size to theme default",
            editor.save_act: "Save the current script",
            editor.saveAs_act: "Save the current script as a new file",
            editor.saveOutputAs_act: "Save the output panel text to a file",
            editor.saveOutputToTab_act: "Copy the output panel text to a new tab",
            editor.saveSeccion_act: "Save the current session tabs and layout",
            editor.searchPlugin_act: "Search and execute a plugin",
            editor.selectAllOccurrences_act: "Select all occurrences of the current word",
            editor.selectNextOccurrence_act: "Select the next occurrence of the current word",
            editor.set_font_act: "Choose the font for the editor",
            editor.settingsFile_act: "Open the folder containing the settings file",
            editor.shortcuts_act: "Show a list of application shortcuts",
            editor.show_docstrings_act: "Show docstrings in the autocomplete popup",
            editor.showAutocomplete_act: "Show code autocompletion",
            editor.showExplorer_act: "Show or hide the file explorer panel",
            editor.showOutline_act: "Show or hide the code outline panel",
            editor.showOutput_act: "Show or hide the output panel",
            editor.showStatusTips_act: "Toggle visibility of status bar tips",
            editor.spacesToTabs_act: "Convert spaces to tabs in the current script",
            editor.syntaxCheck_act: "Toggle live Python syntax checking",
            editor.tabToSpaces_act: "Convert tabs to spaces in the current script",
            editor.toggleBookmark_act: "Toggle bookmark on the current line",
            editor.toggleEditorToolbar_act: "Toggle visibility of the editor toolbar",
            editor.toggleMenus_act: "Toggle the main menu bar visibility",
            editor.trimAutoWhitespace_act: "Automatically trim trailing whitespace on save",
            editor.trimWhitespace_act: "Trim trailing whitespace in the current script",
            editor.type_act: "Execute type() on the selected text",
            editor.undo_act: "Undo the last action",
            editor.unfold_act: "Unfold the current code block",
            editor.unfold_all_act: "Unfold all code blocks",
            editor.versionControl_act: "Toggle Git version control features",
            editor.whitespace_act: "Show or hide whitespace characters in the editor",
            editor.wordWrap_act: "Toggle word wrap in the editor",
            editor.zoom_in_act: "Zoom in the editor font size",
            editor.zoom_out_act: "Zoom out the editor font size",
            editor.diffTool_act: "Compare with...",
        }

        # Insert Bookmarks menu after File menu
        actions = editor.menubar.actions()
        if len(actions) > 1:
            editor.menubar.insertMenu(actions[1], editor.bookmarks_menu)
        else:
            editor.menubar.addMenu(editor.bookmarks_menu)

        for act, tip in status_tips.items():
            if hasattr(act, 'setStatusTip'):
                act.setStatusTip(tip)
            if hasattr(act, 'setToolTip'):
                try:
                    shortcut = act.shortcut()
                    if shortcut and not shortcut.isEmpty():
                        act.setToolTip(f"{tip} ({shortcut.toString()})")
                    else:
                        act.setToolTip(tip)
                except Exception:
                    act.setToolTip(tip)

        # Add status tips for top-level menus
        if hasattr(editor, 'file_menu') and hasattr(editor.file_menu, 'menuAction'):
            editor.file_menu.menuAction().setStatusTip("File operations")
        if hasattr(editor, 'bookmarks_menu') and hasattr(editor.bookmarks_menu, 'menuAction'):
            editor.bookmarks_menu.menuAction().setStatusTip("Manage line bookmarks")
        if hasattr(editor, 'tools_menu') and hasattr(editor.tools_menu, 'menuAction'):
            editor.tools_menu.menuAction().setStatusTip("Edit text and code")
        if hasattr(editor, 'options_menu') and hasattr(editor.options_menu, 'menuAction'):
            editor.options_menu.menuAction().setStatusTip("Editor options and preferences")
        if hasattr(editor, 'run_menu') and hasattr(editor.run_menu, 'menuAction'):
            editor.run_menu.menuAction().setStatusTip("Execute script and code selections")
        if hasattr(editor, 'theme_menu') and hasattr(editor.theme_menu, 'menuAction'):
            editor.theme_menu.menuAction().setStatusTip("Change color themes and syntax highlighting")
        if hasattr(editor, 'view_menu') and hasattr(editor.view_menu, 'menuAction'):
            editor.view_menu.menuAction().setStatusTip("Change appearance and layout")
        if hasattr(editor, 'help_menu') and hasattr(editor.help_menu, 'menuAction'):
            editor.help_menu.menuAction().setStatusTip("Help, shortcuts and documentation")

        # Populate editor toolbar
        if hasattr(editor, 'editor_toolbar'):
            tb = editor.editor_toolbar
            tb.clear()



            # File Actions
            tb.addAction(editor.load_act)
            tb.addAction(editor.diffTool_act)
            tb.addAction(editor.saveOutputAs_act)
            tb.addAction(editor.saveOutputToTab_act)
            tb.addAction(editor.closeAllTabs_act)

            tb.addSeparator()

            # Bookmarks Actions
            if hasattr(editor, 'toggleBookmark_act'):
                tb.addAction(editor.toggleBookmark_act)
            if hasattr(editor, 'prevBookmark_act'):
                tb.addAction(editor.prevBookmark_act)
            if hasattr(editor, 'nextBookmark_act'):
                tb.addAction(editor.nextBookmark_act)
            if hasattr(editor, 'bookmarksFinder_act'):
                tb.addAction(editor.bookmarksFinder_act)
            if hasattr(editor, 'clearBookmarks_act'):
                tb.addAction(editor.clearBookmarks_act)

            tb.addSeparator()

            # Edit Actions
            tb.addAction(editor.clipboardManager_act)
            tb.addAction(editor.find_act)
            tb.addAction(editor.gotoLine_act)
            tb.addAction(editor.goToSymbol_act)
            tb.addAction(editor.comment_cat)
            tb.addAction(editor.add_quotes_act)
            tb.addAction(editor.f_string_act)
            tb.addSeparator()

            tb.addAction(editor.deleteLine_act)
            tb.addAction(editor.duplicateLine_act)
            tb.addAction(editor.moveLineUp_act)
            tb.addAction(editor.moveLineDown_act)

            tb.addSeparator()

            tb.addAction(editor.addCursorsToLineEnds_act)
            tb.addAction(editor.addCursorAbove_act)
            tb.addAction(editor.addCursorBelow_act)

            tb.addSeparator()

            tb.addAction(editor.showAutocomplete_act)

            tb.addSeparator()

            # View Actions
            tb.addAction(editor.fold_act)
            tb.addAction(editor.unfold_act)
            tb.addAction(editor.fold_all_act)
            tb.addAction(editor.unfold_all_act)
            tb.addAction(editor.zoom_in_act)
            tb.addAction(editor.zoom_out_act)
            tb.addAction(editor.reset_zoom_act)

        # Ensure all actions with window-level shortcuts are added to the main window
        # so they remain active even if both the menus and toolbar are hidden.
        for action in editor.findChildren(QAction):
            if action.shortcut() and not action.shortcut().isEmpty():
                if action.shortcutContext() != Qt.WidgetShortcut:
                    if action not in editor.actions():
                        editor.addAction(action)
