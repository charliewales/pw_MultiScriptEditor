import sys
from functools import partial

import vendor.Qt
from icons import icons
from vendor.Qt.QtCore import Qt, QTimer
from vendor.Qt.QtGui import QIcon, QKeySequence
from vendor.Qt.QtWidgets import QAction, QMenu, QShortcut


class ScriptEditorUIBuilder:
    @staticmethod
    def _configure_action(action, callback=None, icon=None, shortcut=None, context=None, checkable=None):
        if callback is not None:
            action.triggered.connect(callback)
        if icon is not None:
            action.setIcon(QIcon(icons[icon]))
        if shortcut is not None:
            if isinstance(shortcut, (list, tuple)):
                action.setShortcuts(
                    [QKeySequence(value) for value in shortcut]
                )
            else:
                action.setShortcut(shortcut)
        if context is not None:
            action.setShortcutContext(context)
        if checkable is not None:
            action.setCheckable(checkable)

    @staticmethod
    def _configure_optional_icon_action(action, callback=None, icon=None, shortcut=None, context=None):
        if callback is not None:
            action.triggered.connect(callback)
        if icon is not None and icon in icons:
            action.setIcon(QIcon(icons[icon]))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if context is not None:
            action.setShortcutContext(context)

    @staticmethod
    def _call_current_edit(editor, method_name, *args):
        current_widget = editor.tab.currentWidget()
        if current_widget and hasattr(current_widget, 'edit'):
            getattr(current_widget.edit, method_name)()

    @staticmethod
    def setup_ui(editor):
        configure = ScriptEditorUIBuilder._configure_action
        configure_optional = ScriptEditorUIBuilder._configure_optional_icon_action

        configure(editor.execAll_act, icon='all')
        configure(editor.execLine_act, icon='line')
        configure(editor.execSel_act, icon='sel')
        configure(editor.clearHistory_act, icon='clear')

        # connects
        configure(editor.load_act, editor.loadScript, 'open', "Ctrl+O")
        configure(editor.diffTool_act, editor.openDiffDialog, 'git_diff', "Ctrl+Alt+Shift+C")
        configure(editor.save_act, editor.saveScript, 'save', "Ctrl+S")
        configure(editor.saveAs_act, editor.saveScriptAs, 'save', "Ctrl+Shift+S")

        configure(editor.saveSeccion_act, lambda: editor.saveSession(True), 'save', "Ctrl+Alt+S")
        configure(editor.closeAllTabs_act, editor.closeAllTabsWithConfirm, 'close_all_tabs', "Ctrl+Shift+Alt+W")
        configure(editor.exit_act, editor.close)
        configure(editor.tabToSpaces_act, editor.tabsToSpaces)
        configure(editor.showAutocomplete_act, editor.show_autocompletion, 'show_autocomplete')
        configure(editor.trimWhitespace_act, editor.trimTrailingWhitespace, 'trim_whitespace')
        configure(editor.quit_act, editor.close, 'quit', "Ctrl+Q")

        configure(editor.duplicateLine_act, editor.duplicateLine, 'duplicate_line', 'Ctrl+Shift+D', Qt.WindowShortcut)
        configure(editor.deleteLine_act, editor.deleteLine, 'delete_line', 'Ctrl+D', Qt.WindowShortcut)
        configure(editor.set_font_act, editor.choose_font, 'font')
        configure(editor.settingsFile_act, editor.openSettingsFile, 'settings')
        configure(editor.editTheme_act, editor.openThemeEditor, 'theme', 'Ctrl+Shift+T')

        configure(editor.donate_act, lambda: editor.openLink('donate'))
        configure(editor.blenderManual_act, lambda: editor.openLink('blender_manual'), 'blender')
        configure(editor.openManual_act, lambda: editor.openLink('manual'), 'github')
        configure(
            editor.python_act,
            lambda: editor.openLink("python{0}".format(sys.version_info.major), f".{sys.version_info.minor}"),
            'python',
        )
        configure(editor.houdini_hou_act, lambda: editor.openLink('houdini_hou'), 'houdini')
        configure(editor.houdini_envs_act, lambda: editor.openLink('houdini_envs'), 'houdini')
        configure(editor.maya_cmds_act, lambda: editor.openLink('maya_cmds'), 'maya')
        configure(editor.nuke_dev_guide_act, lambda: editor.openLink('nuke_dev_guide'), 'nuke')
        configure(editor.qt_docs_act, lambda: editor.openLink(f"qt{'6' if vendor.Qt.IsPySide6 else '5'}_docs"), 'qt')
        configure(editor.qt_modules_act, lambda: editor.openLink(f"qt{'6' if vendor.Qt.IsPySide6 else '5'}_modules"), 'qt')
        configure(editor.about_act, editor.about, 'about')
        configure(editor.help_act, icon='sel')
        editor.shortcuts_act.setText('Shortcut manager')
        configure(editor.shortcuts_act, editor.shortcuts, 'shortcut')
        configure(editor.documentation_act, editor.openDocumentation, 'docs')
        configure(editor.printHelp_act, editor.mse_help, 'print_help')

        # editor
        configure(editor.undo_act, editor.tab.undo, 'undo', 'Ctrl+Z', Qt.WidgetShortcut)
        configure(editor.redo_act, editor.tab.redo, 'redo', 'Ctrl+Y', Qt.WidgetShortcut)
        configure(editor.clipboardManager_act, editor.tab.showClipboardManager, 'paste', 'Ctrl+Shift+V', Qt.WindowShortcut)
        configure(editor.copy_act, editor.tab.copy, 'copy', 'Ctrl+C', Qt.WidgetShortcut)
        configure(editor.cut_act, editor.tab.cut, 'cut', 'Ctrl+X', Qt.WidgetShortcut)
        configure(editor.paste_act, editor.tab.paste, 'paste', 'Ctrl+V', Qt.WidgetShortcut)
        configure(editor.addCursorsToLineEnds_act, editor.tab.addCursorsToLineEnds, 'add_cursors_to_line_ends', 'Ctrl+Shift+I', Qt.WindowShortcut)
        configure(editor.addCursorAbove_act, editor.tab.addCursorAbove, 'add_cursor_above', 'Ctrl+Shift+Up', Qt.WindowShortcut)
        configure(editor.addCursorBelow_act, editor.tab.addCursorBelow, 'add_cursor_below', 'Ctrl+Shift+Down', Qt.WindowShortcut)
        configure(editor.find_act, editor.findWidget, 'replace', 'Ctrl+F', Qt.WindowShortcut)
        configure(editor.replace_act, lambda: editor.findWidget(True), 'replace', 'Ctrl+H', Qt.WindowShortcut)
        configure_optional(editor.commandPalette_act, editor.openCommandPalette, 'shortcut', 'Ctrl+Shift+P', Qt.WindowShortcut)
        # Ctrl+Shift+G is set in retranslateUi but setting it here for context explicitly
        configure_optional(editor.gitAction_act, editor.openGitPopup, 'git', 'Ctrl+Shift+G', Qt.WindowShortcut)
        configure(editor.gotoLine_act, editor.gotoLine, 'goto_line', 'Ctrl+G', Qt.WindowShortcut)
        configure(editor.goToSymbol_act, editor.goToSymbol, 'goto_symbol', 'Ctrl+R', Qt.WindowShortcut)

        recent_files_sc = QShortcut(QKeySequence('Ctrl+P'), editor)
        recent_files_sc.setContext(Qt.ApplicationShortcut)
        recent_files_sc.activated.connect(editor.showRecentFiles)
        editor._recent_files_sc = recent_files_sc

        open_tabs_sc = QShortcut(QKeySequence('Ctrl+Tab'), editor)
        open_tabs_sc.setContext(Qt.ApplicationShortcut)
        open_tabs_sc.activated.connect(editor.showOpenTabs)
        editor._open_tabs_sc = open_tabs_sc

        configure(editor.tabToSpaces_act, icon='tabs_to_spaces')
        configure(editor.spacesToTabs_act, editor.spacesToTabs, 'spaces_to_tabs')
        configure(editor.print_command_act, checkable=True)
        configure(editor.clear_exec_act, editor.show_clear_exec, shortcut='Ctrl+Alt+C', context=Qt.WindowShortcut, checkable=True)
        configure(editor.whitespace_act, editor.render_whitespace, shortcut='Ctrl+Shift+W', context=Qt.WindowShortcut, checkable=True)
        configure(editor.out_wordWrap_act, editor.out.wordWrap, shortcut='Ctrl+Alt+W', context=Qt.WindowShortcut, checkable=True)
        configure(editor.wordWrap_act, editor.tab.wordWrap, shortcut='Alt+W', context=Qt.WindowShortcut, checkable=True)
        configure(editor.moveLineUp_act, editor.tab.move_line_up, 'move_line_up', 'Alt+Up', Qt.WindowShortcut)
        configure(editor.moveLineDown_act, editor.tab.move_line_down, 'move_line_down', 'Alt+Down', Qt.WindowShortcut)
        configure(editor.selectLine_act, editor.tab.selectLine, 'select_line', 'Ctrl+L', Qt.WindowShortcut)
        configure(editor.comment_cat, editor.tab.comment, 'comment', 'Alt+C', Qt.WindowShortcut)
        configure(editor.add_quotes_act, editor.tab.addQuotes, 'add_quotes', 'Alt+Q', Qt.WindowShortcut)
        configure(editor.f_string_act, editor.tab.fString, 'f_string', 'Alt+F', Qt.WindowShortcut)
        configure(editor.zoom_in_act, partial(editor.change_global_font_size, True), 'zoom_in', ('Ctrl++', 'Ctrl+='), Qt.WindowShortcut)
        configure(editor.zoom_out_act, partial(editor.change_global_font_size, False), 'zoom_out', context=Qt.WindowShortcut)
        configure(editor.reset_zoom_act, editor.restore_global_font_size, 'zoom_reset', 'Ctrl+0', Qt.WindowShortcut)
        configure(editor.fold_act, editor.fold_current, 'fold', 'Alt+-', Qt.WindowShortcut)
        configure(editor.unfold_act, editor.unfold_current, 'unfold', 'Alt++', Qt.WindowShortcut)
        configure(editor.fold_all_act, editor.fold_all, 'fold_all', 'Ctrl+Alt+-', Qt.WindowShortcut)
        configure(editor.unfold_all_act, editor.unfold_all, 'unfold_all', 'Ctrl+Alt++', Qt.WindowShortcut)
        configure(editor.autocomplete_act, shortcut='Alt+A', context=Qt.WindowShortcut)
        configure(editor.selectNextOccurrence_act, editor.tab.selectNextOccurrence, 'select_next_occurrence', 'Ctrl+Alt+D', Qt.WindowShortcut)
        configure(editor.nextSelection_act, editor.tab.nextSelection, 'down', 'Ctrl+J', Qt.WindowShortcut)
        configure(editor.previousSelection_act, editor.tab.previousSelection, 'up', 'Ctrl+Shift+J', Qt.WindowShortcut)
        configure(editor.selectAllOccurrences_act, editor.tab.selectAllOccurrences, 'select_all_occurrences', 'Ctrl+Shift+Alt+D', Qt.WindowShortcut)
        configure(editor.always_ontop_act, editor.always_ontop, context=Qt.WidgetShortcut, checkable=True)

        dir_f = partial(editor.function_cmd, 'dir')
        configure(editor.dir_act, dir_f, 'sel', 'Alt+D', Qt.WindowShortcut)

        help_f = partial(editor.function_cmd, 'help')
        configure(editor.help_act, help_f, 'sel', 'Alt+H', Qt.WindowShortcut)

        print_f = partial(editor.function_cmd, "print")
        configure(editor.print_act, print_f, 'sel', "Alt+e", Qt.WindowShortcut)

        type_f = partial(editor.function_cmd, 'type')
        configure(editor.type_act, type_f, 'sel', 'Alt+T', Qt.WindowShortcut)

        configure(editor.quick_help_act, editor.get_word_help, 'help', 'F1', Qt.WindowShortcut)

        editor.fillThemeMenu()

        # shortcuts
        configure(
            editor.execSel_act,
            editor.executeSelected,
            shortcut=('Ctrl+Return', 'Ctrl+Enter'),
            context=Qt.WidgetWithChildrenShortcut,
        )
        configure(
            editor.execAll_act,
            editor.executeAll,
            shortcut=('Alt+Return', 'Alt+Enter'),
            context=Qt.ApplicationShortcut,
        )
        configure(
            editor.execLine_act,
            editor.executeLine,
            shortcut=('Ctrl+Shift+Return', 'Ctrl+Shift+Enter'),
            context=Qt.ApplicationShortcut,
        )

        configure(editor.clearHistory_act, editor.clearHistory, shortcut='Ctrl+Shift+C')

        # hide
        editor.donate_act.setIcon(QIcon(icons["donate"]))

        # Create status bar
        editor.statusBar()
        # Explorer toggle setup
        configure(editor.showExplorer_act, editor.toggleExplorer, shortcut="Ctrl+Alt+E", context=Qt.WindowShortcut)

        # Outline toggle setup
        configure(editor.showOutline_act, editor.toggleOutline, shortcut="Ctrl+Alt+O", context=Qt.WindowShortcut)

        # Breadcrumbs toggle setup
        configure(editor.showBreadcrumbs_act, editor.toggleBreadcrumbs, shortcut="Ctrl+Alt+B", context=Qt.WindowShortcut)

        # Syntax Check toggle setup
        configure(editor.syntaxCheck_act, editor.toggleSyntaxCheck)

        configure(editor.highlightAllOccurrences_act, editor.toggleHighlightAllOccurrences)
        configure(editor.occurrencesCaseSensitive_act, editor.toggleOccurrencesCaseSensitive)
        configure(editor.preferSingleQuotes_act, editor.togglePreferSingleQuotes)

        # Output Bottom toggle setup
        configure(editor.outputBottom_act, editor.toggleOutputBottom, shortcut="Ctrl+Alt+U", context=Qt.WindowShortcut)
        editor.addAction(editor.outputBottom_act)

        # Output toggle setup
        configure(editor.showOutput_act, editor.toggleOutput, shortcut="Ctrl+Alt+K", context=Qt.WindowShortcut)
        editor.addAction(editor.showOutput_act)

        # Menus toggle setup
        configure(editor.toggleMenus_act, editor.toggleMenuBar, context=Qt.WindowShortcut)
        editor.addAction(editor.toggleMenus_act)

        # Editor Toolbar toggle setup
        configure(editor.toggleEditorToolbar_act, shortcut="Ctrl+Alt+T", context=Qt.WindowShortcut)
        editor.toggleEditorToolbar_act.setChecked(True)
        editor.toggleEditorToolbar_act.toggled.connect(editor.editor_toolbar.setVisible)
        editor.toggleEditorToolbar_act.toggled.connect(editor.saveSettings)
        editor.addAction(editor.toggleEditorToolbar_act)

        # Zen mode toggle setup

        # Auto Close Delimiters toggle setup
        configure(editor.autoCloseDelimiters_act, editor.toggleAutoCloseDelimiters)

        # Quick Tab Switching toggle setup
        configure(editor.quickTabSwitching_act, editor.toggleQuickTabSwitching)

        # Show Status Tips setup
        editor.showStatusTips_act.setChecked(True)
        configure(editor.showStatusTips_act, editor.toggleStatusTips)

        # Version Control (Git) setup
        editor.versionControl_act.setChecked(False)
        configure(editor.versionControl_act, editor.toggleVersionControl, shortcut='Ctrl+Alt+G', context=Qt.WindowShortcut)

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
        editor.saveOutputAs_act.setObjectName('saveOutputAs_act')
        editor.saveOutputToTab_act = QAction("To tab", editor)
        editor.saveOutputToTab_act.setObjectName('saveOutputToTab_act')
        configure(editor.saveOutputAs_act, editor.saveOutputAs, 'save_output_as')
        configure(editor.saveOutputToTab_act, editor.saveOutputToTab, 'save_output_to_tab')
        editor.saveOutput_menu.addAction(editor.saveOutputAs_act)
        editor.saveOutput_menu.addAction(editor.saveOutputToTab_act)

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
        configure(editor.manageSnippet_act, editor.handleSnippetShortcut, shortcut='Alt+S', context=Qt.WindowShortcut)
        editor.addAction(editor.manageSnippet_act)

        # Create Bookmarks actions
        editor.toggleBookmark_act = QAction("Toggle Bookmark", editor)
        editor.toggleBookmark_act.setObjectName('toggleBookmark_act')
        configure_optional(editor.toggleBookmark_act, partial(ScriptEditorUIBuilder._call_current_edit, editor, 'toggle_bookmark'), 'bookmark_toggle', "Ctrl+F2")
        editor.addAction(editor.toggleBookmark_act)

        editor.nextBookmark_act = QAction("Next Bookmark", editor)
        editor.nextBookmark_act.setObjectName('nextBookmark_act')
        configure_optional(editor.nextBookmark_act, partial(ScriptEditorUIBuilder._call_current_edit, editor, 'next_bookmark'), 'bookmark_next', "F2")
        editor.addAction(editor.nextBookmark_act)

        editor.prevBookmark_act = QAction("Previous Bookmark", editor)
        editor.prevBookmark_act.setObjectName('prevBookmark_act')
        configure_optional(editor.prevBookmark_act, partial(ScriptEditorUIBuilder._call_current_edit, editor, 'prev_bookmark'), 'bookmark_prev', "Shift+F2")
        editor.addAction(editor.prevBookmark_act)

        editor.clearBookmarks_act = QAction("Clear Bookmarks", editor)
        editor.clearBookmarks_act.setObjectName('clearBookmarks_act')
        configure_optional(editor.clearBookmarks_act, partial(ScriptEditorUIBuilder._call_current_edit, editor, 'clear_bookmarks'), 'clear', "Ctrl+Shift+F2")
        editor.addAction(editor.clearBookmarks_act)

        editor.bookmarksFinder_act = QAction("Go to bookmark...", editor)
        editor.bookmarksFinder_act.setObjectName('bookmarksFinder_act')
        configure_optional(editor.bookmarksFinder_act, partial(ScriptEditorUIBuilder._call_current_edit, editor, 'show_bookmarks_popup'), 'goto_line', "Ctrl+B")
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
            editor.blenderManual_act: "Open the Blender manual",
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
            editor.find_act: "Find text in the editor or output",
            editor.replace_act: "Find and replace text in the editor",
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
            editor.selectLine_act: "Select the current line or every line containing a cursor",
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
            editor.selectAllOccurrences_act: "Select all occurrences of the current word",
            editor.selectNextOccurrence_act: "Select the next occurrence of the current word",
            editor.set_font_act: "Choose the font for the editor",
            editor.settingsFile_act: "Open the folder containing the settings file",
            editor.shortcuts_act: "Open the Shortcut Manager to configure keyboard shortcuts",
            editor.show_docstrings_act: "Show docstrings in the autocomplete popup",
            editor.showAutocomplete_act: "Show code autocompletion",
            editor.showExplorer_act: "Show or hide the file explorer panel",
            editor.showOutline_act: "Show or hide the code outline panel",
            editor.showBreadcrumbs_act: "Show or hide the breadcrumbs bar at the top of the editor",
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

        # Keep the manager at the bottom of Options, as the final preference action.
        editor.help_menu.removeAction(editor.shortcuts_act)
        editor.options_menu.addSeparator()
        editor.options_menu.addAction(editor.shortcuts_act)

        editor.captureDefaultShortcuts()

        # Ensure all actions with window-level shortcuts are added to the main window
        # so they remain active even if both the menus and toolbar are hidden.
        for action in editor.findChildren(QAction):
            if action.shortcut() and not action.shortcut().isEmpty():
                if action.shortcutContext() != Qt.WidgetShortcut:
                    if action not in editor.actions():
                        editor.addAction(action)
