import os
import getpass
import datetime

from vendor.Qt.QtWidgets import QAction
from vendor.Qt.QtGui import QTextCursor
from plugins.plugin_base import BasePlugin


class ScriptHeaderPlugin(BasePlugin):
    """
    ScriptHeaderPlugin demonstrates how to manipulate the active code editor tab.
    It shows how to access the underlying Qt QTextEdit widget and insert text
    using QTextCursor while respecting the editor's undo/redo stack.
    """
    name = "Script Header Generator"
    description = "Inserts a standard Python script header at the top of the active editor tab."
    version = "1.0.0"

    def register(self):
        """
        Create the UI action for this plugin.
        """
        self.action = QAction("Insert script header", self.editor)
        self.action.triggered.connect(self.insert_header)

        # Add to the Plugins menu via the PluginManager
        if hasattr(self.editor, 'plugin_manager'):
            self.editor.plugin_manager.add_plugin_action(self, self.action)

    def unregister(self):
        """
        Remove the UI action safely when the plugin unloads.
        """
        if hasattr(self, 'action'):
            self.action.deleteLater()
            del self.action

    def insert_header(self):
        """
        Inserts a formatted header block into the currently active script tab.
        """
        # 1. Ensure a tab is actually open
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return

        # 2. Access the custom tab widget
        widget = self.editor.tab.widget(idx)
        if not widget or not hasattr(widget, 'edit'):
            return

        # 3. Gather information for the header
        filename = "untitled.py"
        # Check if the tab represents a saved file
        if hasattr(widget, 'file_path') and widget.file_path:
            filename = os.path.basename(widget.file_path)
        else:
            # Fallback to the tab's display name
            tab_name = self.editor.tab.tabText(idx)
            if tab_name:
                filename = tab_name
                if not filename.endswith(".py"):
                    filename += ".py"

        username = getpass.getuser()
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        # 4. Define the content to insert
        header = (
            f'# -*- coding: utf-8 -*-\n'
            f'"""\n'
            f'Filename: {filename}\n'
            f'Author: {username}\n'
            f'Date: {date_str}\n'
            f'Description:\n'
            f'    <Write a brief description here>\n'
            f'"""\n\n'
        )

        # 5. Manipulate the editor text using Qt's QTextCursor
        edit = widget.edit
        cursor = edit.textCursor()

        # Save original position so we don't annoy the user by jumping their cursor
        original_pos = cursor.position()

        # Wrap changes in an edit block so the user can undo the entire insertion with a single Ctrl+Z
        cursor.beginEditBlock()
        try:
            # Move cursor to the very start of the document
            cursor.movePosition(QTextCursor.Start)
            edit.setTextCursor(cursor)
            # Insert the text
            cursor.insertText(header)

            # Restore the user's cursor position (shifted down by the length of our insertion)
            cursor.setPosition(original_pos + len(header))
            edit.setTextCursor(cursor)
        finally:
            cursor.endEditBlock()
