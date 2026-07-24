class BasePlugin(object):
    """
    Base class that all MultiScriptEditor plugins must inherit from.
    """
    name = "Base Plugin"
    description = "A basic template for a plugin"
    version = "1.0.0"

    def __init__(self, editor):
        """
        Initialize the plugin.
        
        Args:
            editor (scriptEditorClass): The main script editor window instance.
        """
        self.editor = editor

    def register(self):
        """
        Called when the plugin is loaded. Add UI modifications, actions or callbacks here.
        """
        pass

    def unregister(self):
        """
        Called when the plugin is unloaded or the editor closes. Clean up here.
        """
        pass

    # =========================================================================
    # Editor Variables Access
    # =========================================================================

    @property
    def self_main(self):
        """Returns the main script editor widget."""
        return self.editor

    @property
    def self_output(self):
        """Returns the output widget."""
        return getattr(self.editor, 'out', None)

    @property
    def self_version(self):
        """Returns the current version string of the editor."""
        return getattr(self.editor, 'ver', "Unknown")

    @property
    def self_context(self):
        """Returns the current context (e.g. host application)."""
        if hasattr(self.editor, 'namespace'):
            return self.editor.namespace.get('self_context')
        return None

    @property
    def self_help(self):
        """Returns the editor's help function."""
        return getattr(self.editor, 'mse_help', None)

    # =========================================================================
    # Tab Access Methods
    # =========================================================================

    def get_current_tab_content(self):
        """Returns the text content of the currently active tab."""
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return ""
        widget = self.editor.tab.widget(idx)
        if widget and hasattr(widget, 'edit'):
            return widget.edit.toPlainText()
        return ""

    def get_tab_content(self, index):
        """Returns the text content of the tab at the given index."""
        if index < 0 or index >= self.editor.tab.count():
            return ""
        widget = self.editor.tab.widget(index)
        if widget and hasattr(widget, 'edit'):
            return widget.edit.toPlainText()
        return ""

    def get_all_tabs_content(self):
        """Returns a list of text contents for all open tabs."""
        return [self.get_tab_content(i) for i in range(self.editor.tab.count())]

    def get_tab_count(self):
        """Returns the number of open tabs."""
        return self.editor.tab.count()

    def get_current_tab_selected_text(self):
        """Returns the selected text from the currently active tab."""
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return ""
        widget = self.editor.tab.widget(idx)
        if widget and hasattr(widget, 'edit'):
            cursor = widget.edit.textCursor()
            if cursor.hasSelection():
                return cursor.selectedText()
        return ""

    def get_output_selected_text(self):
        """Returns the selected text from the output widget."""
        out_widget = self.self_output
        if out_widget:
            cursor = out_widget.textCursor()
            if cursor.hasSelection():
                return cursor.selectedText()
        return ""
