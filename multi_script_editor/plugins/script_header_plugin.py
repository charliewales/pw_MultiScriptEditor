import os
import getpass
import datetime

from vendor.Qt.QtWidgets import QAction
from vendor.Qt.QtGui import QTextCursor
from .plugin_base import BasePlugin

class ScriptHeaderPlugin(BasePlugin):
    """
    Plugin that inserts a standard Python script header block at the top of the current tab.
    """
    name = "Script Header Generator"
    description = "Inserts a standard Python script header at the top of the active editor tab."
    version = "1.0.0"

    def register(self):
        # Create action
        self.action = QAction("Insert Script Header", self.editor)
        self.action.triggered.connect(self.insert_header)
        
        # Add to the Plugins menu if it exists
        if hasattr(self.editor, 'plugin_manager') and self.editor.plugin_manager.menu:
            self.editor.plugin_manager.menu.addAction(self.action)

    def unregister(self):
        # Remove action from menu and delete it
        if hasattr(self, 'action'):
            if hasattr(self.editor, 'plugin_manager') and self.editor.plugin_manager.menu:
                self.editor.plugin_manager.menu.removeAction(self.action)
            self.action.deleteLater()
            del self.action

    def insert_header(self):
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return
            
        widget = self.editor.tab.widget(idx)
        if not widget or not hasattr(widget, 'edit'):
            return

        # Determine the name of the file
        filename = "untitled.py"
        if hasattr(widget, 'file_path') and widget.file_path:
            filename = os.path.basename(widget.file_path)
        else:
            tab_name = self.editor.tab.tabText(idx)
            if tab_name:
                filename = tab_name
                if not filename.endswith(".py"):
                    filename += ".py"

        username = getpass.getuser()
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        # Define the header content
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

        edit = widget.edit
        cursor = edit.textCursor()
        
        # Save original position, insert at the start, and restore cursor position
        original_pos = cursor.position()
        
        # Begin user action for a single undo step
        cursor.beginEditBlock()
        try:
            cursor.movePosition(QTextCursor.Start)
            edit.setTextCursor(cursor)
            cursor.insertText(header)
            
            # Restore position offset by the length of the header
            cursor.setPosition(original_pos + len(header))
            edit.setTextCursor(cursor)
        finally:
            cursor.endEditBlock()
