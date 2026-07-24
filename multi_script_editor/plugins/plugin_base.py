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
