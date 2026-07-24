from vendor.Qt.QtGui import QTextCursor
from vendor.Qt.QtWidgets import QAction
from plugins.plugin_base import BasePlugin


class ApiDemoPlugin(BasePlugin):
    """
    ApiDemoPlugin demonstrates the basic structure of a custom plugin and how to
    utilize the built-in API methods provided by BasePlugin.

    To create your own plugin:
    1. Inherit from `BasePlugin`.
    2. Define `name`, `description`, and `version` class attributes.
    3. Implement `register(self)` to add your tools to the UI (e.g. actions, shortcuts).
    4. Implement `unregister(self)` to cleanly remove your tools when the plugin reloads.
    """
    # Plugin Metadata - Used by the PluginManager to identify and display the plugin
    name = "API Demo Tool"
    description = "Demonstrates how to use Editor Variables and Tab methods provided by BasePlugin."
    version = "1.0.0"

    def register(self):
        """
        Executed when the plugin is loaded. This is where you create UI elements,
        actions, and connect them to your custom methods.
        """
        # Create a QAction that will appear in the menu
        self.action = QAction("API Demo Tool", self.editor)
        # Connect the action's trigger signal to our custom method
        self.action.triggered.connect(self.run_demo)

        # Add the action to the Plugins menu using the manager's API
        if hasattr(self.editor, 'plugin_manager'):
            # The manager automatically places it in a submenu if this file is inside a folder!
            self.editor.plugin_manager.add_plugin_action(self, self.action)

    def unregister(self):
        """
        Executed when the plugin is unloaded, reloaded, or when the editor closes.
        It's critical to clean up any UI elements (like actions) or event connections here
        so they don't duplicate on reload.
        """
        # Safely delete the action
        if hasattr(self, 'action'):
            self.action.deleteLater()
            del self.action

    def run_demo(self):
        """
        Custom method executed when the user clicks the action.
        Demonstrates accessing the editor's data via BasePlugin's helper properties.
        """
        # 1. Accessing Tab content methods
        # self.get_current_tab_content() returns the raw string from the active tab.
        current_code = self.get_current_tab_content()
        # self.get_tab_count() tells you how many tabs are open in the editor.
        total_tabs = self.get_tab_count()
        lines_count = len(current_code.splitlines()) if current_code else 0

        # 2. Accessing Editor Variables properties
        # self.self_version returns the MSE version string.
        version = self.self_version
        # self.self_context returns the context string (e.g. Maya, Houdini, Nuke, Standalone).
        context = self.self_context or "Standalone (No context)"
        # self.self_help returns the editor's help method, if available.
        has_help = "Yes" if callable(self.self_help) else "No"
        # self.self_main returns the editor's main widget
        mse_window = self.self_main

        # Preparing the text report
        report = (
            f"\n--- API Demo Plugin Report ---\n"
            f"• Editor Version: {version}\n"
            f"• Current Context: {context}\n"
            f"• Help Method Available: {has_help}\n"
            f"• Lines in Current Tab: {lines_count}\n"
            f"• Parent widget: {mse_window}\n"
            f"• Total Open Tabs: {total_tabs}\n"
            f"------------------------------"
        )

        # 3. Accessing the output console
        # self.self_output gives you direct access to the QPlainTextEdit output log.
        if self.self_output:
            self.self_output.appendPlainText(report)

            # Scroll to the bottom of the output
            self.self_output.moveCursor(QTextCursor.End)
            self.self_output.ensureCursorVisible()
