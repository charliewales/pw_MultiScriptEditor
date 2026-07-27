from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QFontMetrics, QIcon
from vendor.Qt.QtWidgets import QAction, QListWidgetItem, QMenu
from widgets.outline_utils import HtmlDelegate
from widgets.searchPopupWidget import SearchPopupWidget


def to_color_str(color_val, default="#d4d4d4"):
    if not color_val:
        return default
    if isinstance(color_val, (list, tuple)) and len(color_val) >= 3:
        return "#{:02x}{:02x}{:02x}".format(color_val[0], color_val[1], color_val[2])
    if hasattr(color_val, "name"):
        return color_val.name()
    return str(color_val)


class CommandPaletteWidget(SearchPopupWidget):
    """
    Floating command palette popup widget for fast command search and execution (Ctrl+Shift+P).
    Subclasses SearchPopupWidget.
    """

    def __init__(
        self,
        parent=None,
        center_widget=None,
        qss=None,
        font=None,
        colors=None,
        editor=None,
    ):
        super(CommandPaletteWidget, self).__init__(
            parent,
            center_widget,
            qss,
            font,
            colors,
            placeholder_text="Type a command to search...",
        )
        self.editor = editor
        self.list_widget.setItemDelegate(HtmlDelegate(self.list_widget))
        self.actions_data = []

        if self.editor:
            self.load_commands()

        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for act in self.actions_data:
            cat = act.get("category", "")
            title = act.get("title", "")
            sc = act.get("shortcut", "")
            full_str = f"{cat}: {title}   {sc}"
            w = fm.horizontalAdvance(full_str) if hasattr(fm, "horizontalAdvance") else fm.width(full_str)
            w += 60
            if w > max_text_width:
                max_text_width = w

        self.resize_and_move(max_text_width)
        self.populate_list("")

    def load_commands(self):
        """
        Recursively extracts actions exclusively from allowed menus:
        Bookmarks, Edit, Options, Plugins, Run, Snippets, View.
        """
        self.actions_data = []
        visited_actions = set()

        ALLOWED_MENUS = {"bookmarks", "edit", "options", "plugins", "run", "snippets", "view"}

        def is_allowed_top_level(title):
            return title.lower().strip() in ALLOWED_MENUS

        def extract_menu_actions(menu, category_path=""):
            for act in menu.actions():
                if not act or act.isSeparator() or not act.isVisible() or act in visited_actions:
                    continue

                sub_menu = act.menu()
                if sub_menu:
                    sub_title = sub_menu.title().replace("&", "").strip()
                    next_cat = f"{category_path} > {sub_title}" if category_path else sub_title
                    extract_menu_actions(sub_menu, next_cat)
                else:
                    text = act.text().replace("&", "").strip()
                    if not text or text == "Command Palette...":
                        continue

                    sc = act.shortcut().toString()
                    cat = category_path if category_path else "General"

                    visited_actions.add(act)
                    self.actions_data.append(
                        {
                            "category": cat,
                            "title": text,
                            "shortcut": sc,
                            "action": act,
                        }
                    )

        if hasattr(self.editor, "menubar") and self.editor.menubar:
            for menu in self.editor.menubar.findChildren(QMenu):
                parent_menu = menu.parent()
                if isinstance(parent_menu, QMenu):
                    continue
                menu_title = menu.title().replace("&", "").strip()
                if is_allowed_top_level(menu_title):
                    extract_menu_actions(menu, menu_title)

        # Check menu attributes directly on editor if they match allowed list
        menu_attrs = [
            "bookmarks_menu",
            "tools_menu",
            "options_menu",
            "plugins_menu",
            "run_menu",
            "snippets_menu",
            "view_menu",
        ]
        for attr in menu_attrs:
            if hasattr(self.editor, attr):
                m = getattr(self.editor, attr)
                if isinstance(m, QMenu):
                    title = m.title().replace("&", "").strip()
                    if is_allowed_top_level(title):
                        extract_menu_actions(m, title)

        # Sort actions alphabetically by Category, then Title
        self.actions_data.sort(key=lambda x: (x["category"].lower(), x["title"].lower()))

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower().strip()

        c = self.colors or {}
        text_color = to_color_str(c.get("tab_selected_text", c.get("text")), "#d4d4d4")
        cat_color = to_color_str(c.get("keyword", c.get("blue")), "#569cd6")
        sub_color = to_color_str(c.get("comment"), "#808080")

        first_selectable_row = -1

        for act in self.actions_data:
            cat = act.get("category", "")
            title = act.get("title", "")
            sc = act.get("shortcut", "")
            full_searchable = f"{cat} {title}".lower()

            if not filter_text or filter_text in full_searchable:
                item = QListWidgetItem()
                if self._font:
                    item.setFont(self._font)

                shortcut_html = f'<span style="color: {sub_color}; float: right;">{sc}</span>' if sc else ''
                html = (
                    f'<table width="100%" cellpadding="0" cellspacing="0">'
                    f'<tr>'
                    f'<td><span style="color: {cat_color}; font-weight: bold;">{cat}: </span>'
                    f'<span style="color: {text_color};">{title}</span></td>'
                    f'<td align="right">{shortcut_html}</td>'
                    f'</tr>'
                    f'</table>'
                )

                item.setText(html)
                item.setData(Qt.UserRole, act)
                self.list_widget.addItem(item)

                if first_selectable_row == -1:
                    first_selectable_row = self.list_widget.count() - 1

        if first_selectable_row != -1:
            self.list_widget.setCurrentRow(first_selectable_row)

    def on_item_clicked(self, item):
        act_data = item.data(Qt.UserRole)
        if not act_data:
            return

        action_or_cb = act_data.get("action")
        self.accept()

        if isinstance(action_or_cb, QAction):
            action_or_cb.trigger()
        elif callable(action_or_cb):
            action_or_cb()
