from core.outline_parser import OutlineParser
from core.settings_model import SettingsModel
from core.session_model import SessionModel

class MainPresenter:
    def __init__(self, view, execution_manager):
        self.view = view
        self.execution_manager = execution_manager
        self.settings_model = SettingsModel()
        self.session_model = SessionModel()
        
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

    def handle_update_outline(self, code):
        """
        Parses the code for the outline view and updates the UI.
        """
        symbols = OutlineParser.parse(code)
        self.view.set_outline_symbols(symbols)

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
