import os

from core.outline_parser import OutlineParser
from core.settings_model import SettingsModel
from core.session_model import SessionModel
from core.autocomplete_provider import AutocompleteProvider
from core.linter_provider import LinterProvider

class MainPresenter:
    def __init__(self, view, execution_manager):
        self.view = view
        self.execution_manager = execution_manager
        self.settings_model = SettingsModel()
        self.session_model = SessionModel()
        self.autocomplete_provider = AutocompleteProvider()
        self.linter_provider = LinterProvider()
        
        # Connect view signals to presenter slots
        self.view.execute_command_requested.connect(self.handle_execute_command)
        self.view.update_outline_requested.connect(self.handle_update_outline)
        if hasattr(self.view, 'save_settings_requested'):
            self.view.save_settings_requested.connect(self.handle_save_settings)
        if hasattr(self.view, 'load_settings_requested'):
            self.view.load_settings_requested.connect(self.handle_load_settings)
            
        # Push initial settings to the view
        self.handle_load_settings()

    def handle_load_settings(self):
        settings = self.settings_model.read_settings()
        self.view.apply_settings(settings)

    def handle_save_settings(self, settings_data):
        self.settings_model.write_settings(settings_data)

    # SESSION METHODS
    def get_session_tabs(self):
        return self.session_model.readSession()
        
    def save_session(self, tabs):
        return self.session_model.writeSession(tabs)
        
    def get_backup_tabs(self):
        return self.session_model.readBackup()
        
    def save_backup(self, tabs):
        self.session_model.writeBackup(tabs)
        
    def backup_exists(self):
        return self.session_model.backupExists()
        
    def remove_backup(self):
        self.session_model.removeBackup()
        
    def get_named_sessions(self):
        return self.session_model.listNamedSessions()
        
    def save_named_session(self, name, tabs):
        self.session_model.writeNamedSession(name, tabs)
        
    def get_named_session_tabs(self, name):
        return self.session_model.readNamedSession(name)
        
    def delete_named_session(self, name):
        self.session_model.deleteNamedSession(name)

    def handle_update_outline(self, code, ext):
        """
        Parses the code for the outline view and updates the UI.
        """
        symbols = OutlineParser.parse(code, ext)
        self.view.set_outline_symbols(symbols, ext)

    def handle_execute_command(self, command, echo_command=False, clear_history=False):
        """
        Handles the execution of a command triggered from the View.
        """
        if clear_history:
            self.view.clear_output()
            
        self.view.append_output_message(command)
            
        namespace = self.view.get_namespace()
        
        def output_callback(text):
            self.view.append_output_message(text)
            
        def close_callback():
            self.view.close()
            
        self.execution_manager.run_command(command, namespace, output_callback, close_callback)

    def request_autocomplete(self, text, line, column, namespace, fuzzy, context):
        """
        Delegates the autocomplete request to the model (AutocompleteProvider).
        Returns a list of CompletionItem objects.
        """
        ext = '.py'
        edit = self.view.tab.widget(self.view.tab.currentIndex())
        if edit and hasattr(edit, 'file_path') and edit.file_path:
             ext = os.path.splitext(edit.file_path)[1].lower()
             
        if ext != '.py':
            return []
            
        return self.autocomplete_provider.get_completions(
            text=text,
            line=line,
            column=column,
            namespace=namespace,
            fuzzy=fuzzy,
            context=context
        )

    def request_lint(self, code):
        """
        Delegates the lint request to the model (LinterProvider).
        Updates the view with the syntax errors.
        """
        ext = '.py'
        edit = self.view.tab.widget(self.view.tab.currentIndex())
        if edit and hasattr(edit, 'file_path') and edit.file_path:
             ext = os.path.splitext(edit.file_path)[1].lower()
             
        if ext != '.py':
            self.view.show_syntax_errors({})
            return

        errors = self.linter_provider.check_syntax(code)
        self.view.show_syntax_errors(errors)
