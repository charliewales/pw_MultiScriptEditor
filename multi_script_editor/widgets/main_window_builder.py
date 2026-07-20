import sys
from functools import partial
from vendor.Qt.QtCore import Qt, QSize, QTimer
from vendor.Qt.QtGui import QIcon, QKeySequence
from vendor.Qt.QtWidgets import QShortcut, QMenu, QAction
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
        editor.addCursorsToLineEnds_act.setShortcut('Alt+Shift+I')
        editor.addCursorsToLineEnds_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorsToLineEnds_act.setIcon(QIcon(icons['add_cursors_to_line_ends']))

        editor.addCursorAbove_act.triggered.connect(editor.tab.addCursorAbove)
        editor.addCursorAbove_act.setShortcut('Ctrl+Alt+Up')
        editor.addCursorAbove_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorAbove_act.setIcon(QIcon(icons['add_cursor_above']))

        editor.addCursorBelow_act.triggered.connect(editor.tab.addCursorBelow)
        editor.addCursorBelow_act.setShortcut('Ctrl+Alt+Down')
        editor.addCursorBelow_act.setShortcutContext(Qt.WindowShortcut)
        editor.addCursorBelow_act.setIcon(QIcon(icons['add_cursor_below']))

        editor.find_act.triggered.connect(editor.findWidget)
        editor.find_act.setShortcut('Ctrl+F')
        editor.find_act.setShortcutContext(Qt.WindowShortcut)
        editor.find_act.setIcon(QIcon(icons['replace']))

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

        # Outline toggle setup
        editor.showOutline_act.setShortcut("Ctrl+Shift+O")
        editor.showOutline_act.setShortcutContext(Qt.WindowShortcut)
        editor.showOutline_act.triggered.connect(editor.toggleOutline)
        editor.showOutlineButton_act.triggered.connect(editor.toggleOutlineButton)
        # QShortcut(QKeySequence("Ctrl+Shift+O"), editor, editor.showOutline_act.trigger)

        # Syntax Check toggle setup
        editor.syntaxCheck_act.triggered.connect(editor.toggleSyntaxCheck)

        editor.highlightAllOccurrences_act.triggered.connect(editor.toggleHighlightAllOccurrences)
        editor.occurrencesCaseSensitive_act.triggered.connect(editor.toggleOccurrencesCaseSensitive)
        editor.preferSingleQuotes_act.triggered.connect(editor.togglePreferSingleQuotes)

        # Output Bottom toggle setup
        editor.outputBottom_act.setShortcut("Ctrl+U")
        editor.outputBottom_act.setShortcutContext(Qt.WindowShortcut)
        editor.outputBottom_act.triggered.connect(editor.toggleOutputBottom)
        # QShortcut(QKeySequence("Ctrl+U"), editor, editor.outputBottom_act.trigger)

        # Output toggle setup
        editor.showOutput_act.setShortcut("Ctrl+K")
        editor.showOutput_act.setShortcutContext(Qt.WindowShortcut)
        editor.showOutput_act.triggered.connect(editor.toggleOutput)
        # QShortcut(QKeySequence("Ctrl+Alt+J"), editor, editor.showOutput_act.trigger)

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
        editor.sessions_menu.setIcon(QIcon(icons['open']))
        editor.sessions_menu.menuAction().setStatusTip("Manage and load saved sessions")
        editor.file_menu.insertMenu(editor.closeAllTabs_act, editor.sessions_menu)
        editor.file_menu.insertSeparator(editor.closeAllTabs_act)

        # Snippets Submenu
        editor.snippets_menu = QMenu("Snippets", editor)
        editor.snippets_menu.setIcon(QIcon(icons['snippets']))
        editor.snippets_menu.menuAction().setStatusTip("Manage code snippets")
        editor.file_menu.insertMenu(editor.closeAllTabs_act, editor.snippets_menu)
        editor.file_menu.insertSeparator(editor.closeAllTabs_act)

        # Snippets actions shortcuts
        editor.manageSnippet_act = QAction("Insert/save snippet", editor)
        editor.manageSnippet_act.setShortcut('Alt+S')
        editor.manageSnippet_act.setShortcutContext(Qt.WindowShortcut)
        editor.manageSnippet_act.setStatusTip("Insert a snippet, or save selection as a new snippet")
        editor.manageSnippet_act.triggered.connect(editor.handleSnippetShortcut)
        editor.addAction(editor.manageSnippet_act)

        # Create Bookmarks actions
        editor.toggleBookmark_act = QAction("Toggle Bookmark", editor)
        editor.toggleBookmark_act.setShortcut("Ctrl+F2")
        editor.toggleBookmark_act.setIcon(QIcon(icons.get('bookmark_toggle', '')))
        editor.toggleBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.toggle_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)

        editor.nextBookmark_act = QAction("Next Bookmark", editor)
        editor.nextBookmark_act.setShortcut("F2")
        editor.nextBookmark_act.setIcon(QIcon(icons.get('bookmark_next', '')))
        editor.nextBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.next_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)

        editor.prevBookmark_act = QAction("Previous Bookmark", editor)
        editor.prevBookmark_act.setShortcut("Shift+F2")
        editor.prevBookmark_act.setIcon(QIcon(icons.get('bookmark_prev', '')))
        editor.prevBookmark_act.triggered.connect(lambda: editor.tab.currentWidget().edit.prev_bookmark() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)

        editor.clearBookmarks_act = QAction("Clear Bookmarks", editor)
        editor.clearBookmarks_act.setShortcut("Ctrl+Shift+F2")
        editor.clearBookmarks_act.setIcon(QIcon(icons.get('clear', '')))
        editor.clearBookmarks_act.triggered.connect(lambda: editor.tab.currentWidget().edit.clear_bookmarks() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)

        editor.bookmarksFinder_act = QAction("Go to bookmark...", editor)
        editor.bookmarksFinder_act.setShortcut("Ctrl+B")
        editor.bookmarksFinder_act.setIcon(QIcon(icons.get('goto_line', '')))
        editor.bookmarksFinder_act.triggered.connect(lambda: editor.tab.currentWidget().edit.show_bookmarks_popup() if editor.tab.currentWidget() and hasattr(editor.tab.currentWidget(), 'edit') else None)

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
            editor.manageSnippet_act: "Insert a snippet, or save selection as a new snippet",
            editor.load_act: "Open an existing script file",
            editor.save_act: "Save the current script",
            editor.saveSeccion_act: "Save the current session tabs and layout",
            editor.closeAllTabs_act: "Close all open script tabs",
            editor.exit_act: "Close the application",
            editor.quit_act: "Quit the application",
            editor.tabToSpaces_act: "Convert tabs to spaces in the current script",
            editor.spacesToTabs_act: "Convert spaces to tabs in the current script",
            editor.duplicateLine_act: "Duplicate the current line or selection",
            editor.deleteLine_act: "Delete the current line",
            editor.set_font_act: "Choose the font for the editor",
            editor.settingsFile_act: "Open the folder containing the settings file",
            editor.editTheme_act: "Edit the current color theme",
            editor.donate_act: "Support the development of Multi Script Editor",
            editor.openManual_act: "Open the GitHub repository and manual",
            editor.python_act: "Open the official Python documentation",
            editor.houdini_hou_act: "Open Houdini hou package documentation",
            editor.houdini_envs_act: "Open Houdini environment variables documentation",
            editor.maya_cmds_act: "Open Maya commands documentation",
            editor.nuke_dev_guide_act: "Open Nuke Developer Guide",
            editor.qt_docs_act: "Open Qt for Python documentation",
            editor.qt_modules_act: "Open Qt Modules documentation",
            editor.about_act: "Show information about the application",
            editor.help_act: "Execute help() on the selected text",
            editor.shortcuts_act: "Show a list of application shortcuts",
            editor.documentation_act: "Open Multi Script Editor documentation",
            editor.printHelp_act: "Print Multi Script Editor help in the output",
            editor.undo_act: "Undo the last action",
            editor.redo_act: "Redo the last action",
            editor.copy_act: "Copy the selected text to clipboard",
            editor.cut_act: "Cut the selected text to clipboard",
            editor.paste_act: "Paste text from the clipboard",
            editor.addCursorsToLineEnds_act: "Add cursors to the end of each selected line",
            editor.find_act: "Find and replace text in the editor",
            editor.gotoLine_act: "Go to a specific line in the editor",
            editor.goToSymbol_act: "Go to a symbol in the editor",
            editor.print_command_act: "Echo executed commands in the output panel",
            editor.clear_exec_act: "Clear the output panel before executing code",
            editor.whitespace_act: "Show or hide whitespace characters in the editor",
            editor.out_wordWrap_act: "Toggle word wrap in the output panel",
            editor.wordWrap_act: "Toggle word wrap in the editor",
            editor.moveLineUp_act: "Move the current line or selection up",
            editor.moveLineDown_act: "Move the current line or selection down",
            editor.comment_cat: "Toggle comment on the current line or selection",
            editor.add_quotes_act: "Add quotes around selected text or select text inside quotes",
            editor.f_string_act: "Create an f-string from the current selection or clipboard",
            editor.autocomplete_act: "Toggle code autocomplete functionality",
            editor.showAutocomplete_act: "Show code autocompletion",
            editor.fuzzy_autocomplete_act: "Toggle fuzzy code autocomplete functionality",
            editor.show_docstrings_act: "Show docstrings in the autocomplete popup",
            editor.highlightAllOccurrences_act: "Highlight all occurrences of the selected text",
            editor.occurrencesCaseSensitive_act: "If enabled, case sensitive will be used when selecting occurrences",
            editor.preferSingleQuotes_act: "If enabled, single quotes will be used when adding quotes and f-strings",
            editor.selectNextOccurrence_act: "Select the next occurrence of the current word",
            editor.nextSelection_act: "Move to the next selection",
            editor.previousSelection_act: "Move to the previous selection",
            editor.selectAllOccurrences_act: "Select all occurrences of the current word",
            editor.always_ontop_act: "Keep the application window always on top",
            editor.dir_act: "Execute dir() on the selected text",
            editor.print_act: "Execute print() on the selected text",
            editor.type_act: "Execute type() on the selected text",
            editor.quick_help_act: "Show quick help for the current word",
            editor.execSel_act: "Execute the selected code or current line",
            editor.execAll_act: "Execute all code in the current tab",
            editor.execLine_act: "Execute the current line",
            editor.clearHistory_act: "Clear the output panel history",
            editor.showOutline_act: "Show or hide the code outline panel",
            editor.showOutput_act: "Show or hide the output panel",
            editor.syntaxCheck_act: "Toggle live Python syntax checking",
            editor.outputBottom_act: "Move the output panel to the bottom of the window",
            editor.autoCloseDelimiters_act: "Automatically close brackets, braces, and quotes",
            editor.quickTabSwitching_act: "Enable switching tabs using Ctrl+1, Ctrl+2, etc., and display tab numbers when holding Ctrl",
            editor.zoom_in_act: "Zoom in the editor font size",
            editor.zoom_out_act: "Zoom out the editor font size",
            editor.reset_zoom_act: "Reset the editor font size to theme default",
            editor.toggleBookmark_act : "Toggle bookmark on the current line",
            editor.nextBookmark_act : "Navigate to the next bookmark",
            editor.prevBookmark_act : "Navigate to the previous bookmark",
            editor.clearBookmarks_act : "Clear all bookmarks in the current document",
            editor.bookmarksFinder_act : "Search and navigate bookmarked lines",
            editor.showOutlineButton_act: "Show or hide the code outline button in the status bar",
            editor.unfold_all_act: "Unfold all code blocks",
            editor.quickHelp_act: "Show quick help for the current word",
            editor.addCursorAbove_act: "Add a cursor above the current line",
            editor.fold_all_act: "Fold all code blocks",
            editor.unfold_act: "Unfold the current code block",
            editor.saveAs_act: "Save the current script as a new file",
            editor.toggleMenus_act: "Toggle the main menu bar visibility",
            editor.toggleEditorToolbar_act: "Toggle visibility of the editor toolbar",
            editor.fold_act: "Fold the current code block",
            editor.addCursorBelow_act: "Add a cursor below the current line",
            editor.trimAutoWhitespace_act: "Automatically trim trailing whitespace on save",
            editor.trimWhitespace_act: "Trim trailing whitespace in the current script",
            editor.saveOutputAs_act: "Save the output panel text to a file",
            editor.saveOutputToTab_act: "Copy the output panel text to a new tab",
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

        # Populate editor toolbar
        if hasattr(editor, 'editor_toolbar'):
            tb = editor.editor_toolbar
            tb.clear()

            # Align to the right by adding an expanding spacer widget
            from vendor.Qt.QtWidgets import QWidget, QSizePolicy
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            tb.addWidget(spacer)

            # File Actions
            tb.addAction(editor.load_act)
            tb.addAction(editor.saveOutputAs_act)
            tb.addAction(editor.saveOutputToTab_act)
            tb.addAction(editor.closeAllTabs_act)

            tb.addSeparator()

            # Bookmarks Actions
            if hasattr(editor, 'toggleBookmark_act'):
                tb.addAction(editor.toggleBookmark_act)
            if hasattr(editor, 'nextBookmark_act'):
                tb.addAction(editor.nextBookmark_act)
            if hasattr(editor, 'prevBookmark_act'):
                tb.addAction(editor.prevBookmark_act)
            if hasattr(editor, 'clearBookmarks_act'):
                tb.addAction(editor.clearBookmarks_act)
            if hasattr(editor, 'bookmarksFinder_act'):
                tb.addAction(editor.bookmarksFinder_act)

            tb.addSeparator()

            # Edit Actions
            tb.addAction(editor.clipboardManager_act)
            tb.addAction(editor.find_act)
            tb.addAction(editor.gotoLine_act)
            tb.addAction(editor.goToSymbol_act)
            tb.addAction(editor.comment_cat)
            tb.addAction(editor.add_quotes_act)
            tb.addAction(editor.f_string_act)
            tb.addAction(editor.addCursorsToLineEnds_act)
            tb.addAction(editor.addCursorAbove_act)
            tb.addAction(editor.addCursorBelow_act)

            tb.addSeparator()

            # View Actions
            tb.addAction(editor.fold_act)
            tb.addAction(editor.unfold_act)
            tb.addAction(editor.fold_all_act)
            tb.addAction(editor.unfold_all_act)
            tb.addAction(editor.zoom_in_act)
            tb.addAction(editor.zoom_out_act)
            tb.addAction(editor.reset_zoom_act)
