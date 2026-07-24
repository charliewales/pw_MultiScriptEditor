import os
import sys
import inspect
import importlib
import importlib.util
import traceback

from vendor.Qt.QtWidgets import QMenu, QAction
from .plugin_base import BasePlugin

class PluginManager(object):
    """
    Manages loading, unloading, and reloading of plugins for Multi Script Editor.
    Loads from built-in directory and user's mse_settings/plugins directory.
    """
    def __init__(self, editor):
        self.editor = editor
        self.plugins = {}  # Store active plugin instances
        self.loaded_modules = {}  # Store imported module names
        self.menu = None

        # Expose plugin_base modules under absolute names so user plugins
        # can also import them absolutely (e.g. from plugins.plugin_base import BasePlugin)
        base_module_name = f"{__package__}.plugin_base"
        if base_module_name in sys.modules:
            sys.modules['plugins.plugin_base'] = sys.modules[base_module_name]
            sys.modules['plugin_base'] = sys.modules[base_module_name]

    def load_plugins(self):
        """
        Discover and load all plugins from both built-in and user settings directories.
        """
        self.unload_plugins()

        # Create the Plugins menu first so plugins can append actions to it
        self.create_menu()

        # 1. Load built-in plugins (from the installation folder)
        plugins_dir = os.path.dirname(os.path.abspath(__file__))
        self._load_plugins_from_directory(plugins_dir, is_user=False)

        # 2. Load user plugins (from mse_settings/plugins)
        try:
            from core.settings_model import SettingsModel
            user_pref_dir = SettingsModel()._get_user_pref_folder()
            user_plugins_dir = os.path.join(user_pref_dir, "plugins")
            if os.path.exists(user_plugins_dir):
                self._load_plugins_from_directory(user_plugins_dir, is_user=True)
        except Exception as e:
            self.editor.out.showMessage(
                f"Error loading user plugins from settings: {e}\n"
                f"{traceback.format_exc()}"
            )

        self.finalize_menu()

    def _load_plugins_from_directory(self, directory, is_user=False):
        """
        Scan a directory for plugin files and import/register them.
        """
        if not os.path.exists(directory):
            return

        for item in os.listdir(directory):
            if not item.endswith(".py") or item.startswith("_") or item.startswith("."):
                continue
            
            module_name = item[:-3]
            if not is_user and module_name in ("plugin_base", "plugin_manager"):
                continue

            try:
                # Namespace user plugins uniquely to avoid collisions with built-ins
                full_module_name = f"mse_user_plugin_{module_name}" if is_user else f"{__package__}.{module_name}"
                
                if not is_user:
                    # Built-in plugins loaded relative to current package
                    if full_module_name in sys.modules:
                        module = importlib.reload(sys.modules[full_module_name])
                    else:
                        module = importlib.import_module(f".{module_name}", package=__package__)
                else:
                    # User plugins loaded from an absolute location
                    file_path = os.path.join(directory, item)
                    spec = importlib.util.spec_from_file_location(full_module_name, file_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Could not load spec for {file_path}")
                    module = importlib.util.module_from_spec(spec)
                    module.__package__ = __package__
                    sys.modules[full_module_name] = module
                    spec.loader.exec_module(module)

                self.loaded_modules[module_name] = module

                # Inspect classes in the module
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, BasePlugin) and cls is not BasePlugin:
                        # Instantiate the plugin
                        plugin_inst = cls(self.editor)
                        try:
                            plugin_inst.register()
                            
                            # Use a unique key to prevent clashes
                            key = f"{plugin_inst.name} (User)" if is_user else plugin_inst.name
                            self.plugins[key] = plugin_inst
                            
                            prefix = "[User] " if is_user else ""
                            self.editor.out.showMessage(f"Plugin loaded: {prefix}{plugin_inst.name} (v{plugin_inst.version})")
                        except Exception as register_err:
                            self.editor.out.showMessage(
                                f"Error registering plugin '{name}' from '{module_name}': {register_err}\n"
                                f"{traceback.format_exc()}"
                            )
            except Exception as import_err:
                self.editor.out.showMessage(
                    f"Error importing plugin module '{module_name}': {import_err}\n"
                    f"{traceback.format_exc()}"
                )

    def unload_plugins(self):
        """
        Unload all registered plugins and clean up menus.
        """
        # Unregister each plugin
        for name, plugin_inst in list(self.plugins.items()):
            try:
                plugin_inst.unregister()
                self.editor.out.showMessage(f"Plugin unloaded: {name}")
            except Exception as unregister_err:
                self.editor.out.showMessage(
                    f"Error unregistering plugin '{name}': {unregister_err}\n"
                    f"{traceback.format_exc()}"
                )
        self.plugins.clear()

        # Remove menu if exists
        if self.menu:
            self.editor.menubar.removeAction(self.menu.menuAction())
            self.menu.deleteLater()
            self.menu = None

    def create_menu(self):
        """
        Create the Plugins menu on the menubar.
        """
        self.menu = QMenu("Plugins", self.editor.menubar)
        
        # Try to insert menu after the Options menu (which means before the Run menu)
        menubar_actions = self.editor.menubar.actions()
        insert_before_action = None
        
        # We try to insert before 'run_menu', or 'help_menu' if 'run_menu' isn't available
        if hasattr(self.editor, 'run_menu'):
            insert_before_action = self.editor.run_menu.menuAction()
        elif hasattr(self.editor, 'help_menu'):
            insert_before_action = self.editor.help_menu.menuAction()

        if insert_before_action and insert_before_action in menubar_actions:
            self.editor.menubar.insertMenu(insert_before_action, self.menu)
        else:
            self.editor.menubar.addMenu(self.menu)

    def finalize_menu(self):
        """
        Append plugin metadata and reload actions to the Plugins menu.
        """
        if not self.menu:
            return

        self.menu.addSeparator()
        
        # Add list of active plugins
        if self.plugins:
            self.menu.addAction("Loaded Plugins:").setEnabled(False)
            for name, plugin in self.plugins.items():
                action = self.menu.addAction(f"  • {name} (v{plugin.version})")
                action.setToolTip(plugin.description)
                action.setEnabled(False)
            self.menu.addSeparator()
        else:
            self.menu.addAction("No plugins loaded").setEnabled(False)
            self.menu.addSeparator()

        # Add reload action
        reload_action = QAction("Reload Plugins", self.menu)
        reload_action.triggered.connect(self.load_plugins)
        self.menu.addAction(reload_action)
