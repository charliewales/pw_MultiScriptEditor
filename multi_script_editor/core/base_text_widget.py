import os
import webbrowser

from icons import icons
from vendor.Qt.QtGui import QFont, QFontDatabase, QIcon, QTextOption
from vendor.Qt.QtWidgets import QAction, QPlainTextEdit, QTextEdit


class BaseTextWidgetMixin:
    """
    Mixin class that provides common text editing functionalities
    such as font size manipulation, word wrap, and whitespace rendering.
    Expects to be mixed into a QTextEdit or QTextBrowser.
    """
    def getFontSize(self):
        if hasattr(self, 'fs') and self.fs > 0:
            return self.fs

        size = self.font().pointSize()
        if size > 0:
            return size

        return 10 # Safe fallback

    def setFontSize(self, size):
        if size >= 8: # Assuming minimumFontSize is around 8-10.
            self.fs = size
            self.setTextEditFontSize(self.fs)

    def changeFontSize(self, up):
        size = self.getFontSize()

        if up:
            size = min(30, size + 1)
        else:
            size = max(8, size - 1)

        self.setFontSize(size)

    def setTextEditFontSize(self, size):
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)

    def wordWrap(self, state):
        if isinstance(self, QPlainTextEdit):
            if state:
                self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            else:
                self.setLineWrapMode(QPlainTextEdit.NoWrap)
        else:
            if state:
                self.setLineWrapMode(QTextEdit.WidgetWidth)
            else:
                self.setLineWrapMode(QTextEdit.NoWrap)

    def set_font(self, font):
        self.setFont(font)

    def render_whitespace(self, state):
        text_option = self.document().defaultTextOption()
        if state:
            text_option.setFlags(text_option.flags() | QTextOption.ShowTabsAndSpaces)
        else:
            text_option.setFlags(text_option.flags() & ~QTextOption.ShowTabsAndSpaces)
        self.document().setDefaultTextOption(text_option)

    def set_start_font(self, font_d=None):
        if not font_d:
            return
        family = font_d.get('family', 'monospace')
        pointSize = font_d.get('pointSize', 14)
        italic = font_d.get('italic', False)
        weight = font_d.get('weight', 1)

        # Cross-compatibility patch for PySide2 (NF) vs PySide6 (Nerd Font)
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
        self.setFont(editor_font)
        if hasattr(self, 'fs'):
            self.fs = pointSize

        if hasattr(self, 'completer') and self.completer:
            self.completer.setFont(editor_font)
            if hasattr(self.completer, 'doc_tooltip') and self.completer.doc_tooltip:
                self.completer.doc_tooltip.setFont(editor_font)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        main_win = self.window()
        if hasattr(main_win, 'menubar'):
            menu.setFont(main_win.menubar.font())
            menu.setStyleSheet(main_win.menubar.styleSheet())

        # Selection to tab action
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText().replace('\u2029', '\n')
            sel_to_tab_action = QAction('Selection to tab', self)
            
            def create_selection_tab():
                import datetime
                time_str = datetime.datetime.now().strftime("%H:%M:%S")
                tab_name = f"selection {time_str}"
                if hasattr(main_win, 'tab') and hasattr(main_win.tab, 'addNewTab'):
                    main_win.tab.addNewTab(name=tab_name, text=selected_text)
            
            sel_to_tab_action.triggered.connect(create_selection_tab)
            if menu.actions():
                first_action = menu.actions()[0]
                menu.insertAction(first_action, sel_to_tab_action)
                menu.insertSeparator(first_action)
            else:
                menu.addAction(sel_to_tab_action)

        # Check if we are editing an HTML file to add "Open in browser"
        file_path = None
        curr = self
        while curr:
            file_path = getattr(curr, 'file_path', None)
            if file_path:
                break
            if hasattr(curr, 'parent') and callable(curr.parent):
                curr = curr.parent()
            elif hasattr(curr, 'parentWidget') and callable(curr.parentWidget):
                curr = curr.parentWidget()
            else:
                break

        if file_path and os.path.exists(file_path):
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.html', '.htm']:
                open_action = QAction('Open in browser    \tCtrl+Alt+B', self)
                open_action.setIcon(QIcon(icons['open_in_browser']))
                open_action.triggered.connect(lambda checked=False, path=file_path: webbrowser.open(path))
                if menu.actions():
                    first_action = menu.actions()[0]
                    menu.insertAction(first_action, open_action)
                    menu.insertSeparator(first_action)
                else:
                    menu.addAction(open_action)
            elif ext.lower() == '.md':
                preview_action = QAction('Markdown Preview    \tCtrl+Alt+B', self)
                if 'docs' in icons:
                    preview_action.setIcon(QIcon(icons['docs']))
                preview_action.triggered.connect(lambda checked=False: self.show_markdown_preview())
                if menu.actions():
                    first_action = menu.actions()[0]
                    menu.insertAction(first_action, preview_action)
                    menu.insertSeparator(first_action)
                else:
                    menu.addAction(preview_action)
        if hasattr(main_win, 'menubar') and not main_win.menubar.isVisible():
            menu.addSeparator()
            show_menus_action = QAction('Show menus\tCtrl+M', self)
            if 'menu' in icons:
                show_menus_action.setIcon(QIcon(icons['menu']))
            if hasattr(main_win, 'toggleMenus_act'):
                show_menus_action.triggered.connect(main_win.toggleMenus_act.trigger)
            menu.addAction(show_menus_action)

        menu.exec_(event.globalPos())
        del menu
