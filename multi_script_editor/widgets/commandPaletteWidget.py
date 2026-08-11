from vendor.Qt.QtCore import Qt
from vendor.Qt.QtWidgets import QAction, QListWidgetItem, QMenu
from widgets.outline_utils import HtmlDelegate, color_to_str
from widgets.searchPopupWidget import (
    SearchPopupWidget,
    resize_popup_for_text,
)


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
        self._items_by_action_id = {}
        self._searchable_by_action_id = {}

        if self.editor:
            self.load_commands()

        resize_popup_for_text(
            self,
            font,
            (
                f"{act.get('category', '')}: "
                f"{act.get('title', '')}    "
                f"{act.get('shortcut', '')}"
                for act in self.actions_data
            ),
            padding=60,
        )
        self.populate_list("")

    def load_commands(self):
        """
        Recursively extracts actions exclusively from allowed menus:
        Bookmarks, Edit, Options, Plugins, Run, Snippets, View.
        """
        self.list_widget.clear()
        self.actions_data = []
        self._items_by_action_id.clear()
        self._searchable_by_action_id.clear()
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

        # Map actions by (category.lower(), title.lower())
        action_map = {}
        for act_item in self.actions_data:
            key = (act_item["category"].lower(), act_item["title"].lower())
            action_map[key] = act_item

        # Prepend recently used commands from settings (up to 5)
        recent_items = []
        if hasattr(self.editor, "_current_settings") and isinstance(self.editor._current_settings, dict):
            raw_recent = self.editor._current_settings.get("recent_commands", [])
            for item in raw_recent[:5]:
                if isinstance(item, str):
                    parts = [p.strip() for p in item.split(",", 2)]
                    cat = parts[0] if len(parts) > 0 else ""
                    title = parts[1] if len(parts) > 1 else ""
                    sc = parts[2] if len(parts) > 2 else ""
                elif isinstance(item, dict):
                    cat = item.get("category", "")
                    title = item.get("title", "")
                    sc = item.get("shortcut", "")
                else:
                    continue

                if not title:
                    continue

                lookup_key = (cat.lower(), title.lower())
                act_obj = action_map[lookup_key]["action"] if lookup_key in action_map else None

                recent_items.append(
                    {
                        "category": "Recent",
                        "orig_category": cat,
                        "title": title,
                        "shortcut": sc,
                        "action": act_obj,
                    }
                )

        if recent_items:
            self.actions_data = recent_items + [{"is_separator": True}] + self.actions_data

    def _create_item(self, act):
        c = self.colors or {}
        text_color = color_to_str(c.get("tab_selected_text", c.get("text")), "#d4d4d4")
        cat_color = color_to_str(c.get("keyword", c.get("blue")), "#569cd6")
        sub_color = color_to_str(c.get("comment"), "#808080")
        sep_color = color_to_str(c.get("comment"), "#555555")

        item = QListWidgetItem()
        if act.get("is_separator"):
            item.setFlags(Qt.NoItemFlags)
            item.setText(
                f'<table width="100%" cellpadding="0" cellspacing="0">'
                f'<tr><td style="border-bottom: 1px solid {sep_color}; height: 1px; '
                f'font-size: 1px; line-height: 1px;">&nbsp;</td></tr>'
                f'</table>'
            )
        else:
            if self._font:
                item.setFont(self._font)

            cat = act.get("category", "")
            orig_cat = act.get("orig_category", "")
            title = act.get("title", "")
            sc = act.get("shortcut", "")
            shortcut_html = (
                f'<span style="color: {sub_color}; white-space: nowrap;">'
                f'&nbsp;&nbsp;&nbsp;&nbsp;{sc}</span>'
                if sc
                else ""
            )
            display_cat = f"{cat} ({orig_cat})" if orig_cat else cat

            item.setText(
                f'<table width="100%" cellpadding="0" cellspacing="0">'
                f'<tr>'
                f'<td><span style="color: {cat_color}; font-weight: bold;">{display_cat}: </span>'
                f'<span style="color: {text_color};">{title}</span></td>'
                f'<td align="right">{shortcut_html}</td>'
                f'</tr>'
                f'</table>'
            )

        item.setData(Qt.UserRole, act)
        return item

    def _item_for_action(self, act):
        action_id = id(act)
        item = self._items_by_action_id.get(action_id)
        if item is None:
            item = self._create_item(act)
            self._items_by_action_id[action_id] = item
        return item

    def _searchable_text(self, act):
        action_id = id(act)
        searchable = self._searchable_by_action_id.get(action_id)
        if searchable is None:
            searchable = "{} {} {}".format(
                act.get("category", ""),
                act.get("orig_category", ""),
                act.get("title", ""),
            ).lower()
            self._searchable_by_action_id[action_id] = searchable
        return searchable

    def populate_list(self, filter_text):
        while self.list_widget.count():
            self.list_widget.takeItem(0)

        filter_text = filter_text.lower().strip()
        first_selectable_row = -1
        has_matching_recent = False

        for act in self.actions_data:
            if act.get("is_separator"):
                # Only add separator if there are matching recent items before it
                if has_matching_recent:
                    self.list_widget.addItem(self._item_for_action(act))
                continue

            cat = act.get("category", "")
            if not filter_text or filter_text in self._searchable_text(act):
                if cat == "Recent":
                    has_matching_recent = True

                self.list_widget.addItem(self._item_for_action(act))

                if first_selectable_row == -1:
                    first_selectable_row = self.list_widget.count() - 1

        if first_selectable_row != -1:
            self.list_widget.setCurrentRow(first_selectable_row)

    def navigate_next(self, wrap=False):
        row = self.list_widget.currentRow()
        count = self.list_widget.count()
        while row < count - 1:
            row += 1
            item = self.list_widget.item(row)
            if item and (item.flags() & Qt.ItemIsSelectable):
                self.list_widget.setCurrentRow(row)
                return
        if wrap and count > 0:
            for r in range(count):
                item = self.list_widget.item(r)
                if item and (item.flags() & Qt.ItemIsSelectable):
                    self.list_widget.setCurrentRow(r)
                    return

    def navigate_prev(self, wrap=False):
        row = self.list_widget.currentRow()
        count = self.list_widget.count()
        while row > 0:
            row -= 1
            item = self.list_widget.item(row)
            if item and (item.flags() & Qt.ItemIsSelectable):
                self.list_widget.setCurrentRow(row)
                return
        if wrap and count > 0:
            for r in range(count - 1, -1, -1):
                item = self.list_widget.item(r)
                if item and (item.flags() & Qt.ItemIsSelectable):
                    self.list_widget.setCurrentRow(r)
                    return

    def record_recent_command(self, act_data):
        if not self.editor or act_data.get("is_separator"):
            return

        title = act_data.get("title", "")
        cat = act_data.get("orig_category") or act_data.get("category", "")
        sc = act_data.get("shortcut", "")

        if not title:
            return

        formatted_entry = f"{cat}, {title}, {sc}" if sc else f"{cat}, {title}"

        if hasattr(self.editor, "_current_settings") and isinstance(self.editor._current_settings, dict):
            raw_list = self.editor._current_settings.get("recent_commands", [])
            sanitized_list = []
            for item in raw_list:
                if isinstance(item, str):
                    parts = [p.strip() for p in item.split(",", 2)]
                    item_cat = parts[0] if len(parts) > 0 else ""
                    item_title = parts[1] if len(parts) > 1 else ""
                    if not (item_title == title and item_cat == cat):
                        sanitized_list.append(item)
                elif isinstance(item, dict):
                    item_cat = item.get("category", "")
                    item_title = item.get("title", "")
                    item_sc = item.get("shortcut", "")
                    if not (item_title == title and item_cat == cat):
                        formatted_prev = f"{item_cat}, {item_title}, {item_sc}" if item_sc else f"{item_cat}, {item_title}"
                        sanitized_list.append(formatted_prev)

            sanitized_list.insert(0, formatted_entry)
            sanitized_list = sanitized_list[:5]
            self.editor._current_settings["recent_commands"] = sanitized_list

            if hasattr(self.editor, "saveSettings"):
                self.editor.saveSettings()

    def on_item_clicked(self, item):
        act_data = item.data(Qt.UserRole)
        if not act_data or act_data.get("is_separator"):
            return

        self.record_recent_command(act_data)

        action_or_cb = act_data.get("action")
        self.accept()

        if isinstance(action_or_cb, QAction):
            action_or_cb.trigger()
        elif callable(action_or_cb):
            action_or_cb()
