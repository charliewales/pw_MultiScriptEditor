import json
import os
import codecs
from managers import context

class SettingsModel:
    settings_filename = 'pw_scriptEditor_pref.json'
    _cached_settings = None

    def __init__(self):
        self.path = self._get_settings_file_path()

    def _get_user_pref_folder(self):
        appData = None
        if context == 'hou':
            appData = os.getenv('HOUDINI_USER_PREF_DIR')
        elif context == 'maya':
            appData = os.getenv('MAYA_APP_DIR')
        elif context == 'nuke':
            home = os.getenv('HOME') or os.path.expanduser('~')
            appData = os.path.join(home, '.nuke')
        elif context == 'max':
            import MaxPlus
            appData = os.path.dirname(MaxPlus.PathManager.GetTempDir())
        if not appData:
            appData = os.getenv('HOME') or os.path.expanduser('~')
        return appData

    def _get_settings_file_path(self):
        path = os.path.normpath(os.path.join(self._get_user_pref_folder(), self.settings_filename)).replace('\\','/')
        if not os.path.exists(path):
            folder = os.path.dirname(path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            with codecs.open(path, "w", "utf-16") as stream:
                json.dump(self.get_defaults(), stream, indent=4)
        return path

    def read_settings(self):
        if SettingsModel._cached_settings is not None:
            return SettingsModel._cached_settings
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    SettingsModel._cached_settings = json.load(stream)
                    return SettingsModel._cached_settings
                except Exception:
                    return self.get_defaults()
        return self.get_defaults()

    def write_settings(self, data):
        SettingsModel._cached_settings = data
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)

    @staticmethod
    def get_defaults():
        return dict(geometry=None,
                    outFontSize=8,
                    wrap=True,
                    out_wrap=True,
                    echo_execute=True,
                    clear_execute=False,
                    always_ontop=False,
                    show_whitespace=True,
                    font={"family": "monospace", "pointSize": 12, "weight": 1, "italic": False},
                    recent_files=[]
                    )


class SnippetsModel(SettingsModel):
    settings_filename = 'pw_scriptEditor_snippets.json'
    _cached_settings = None

    def _get_settings_file_path(self):
        return os.path.normpath(os.path.join(self._get_user_pref_folder(), self.settings_filename)).replace('\\','/')

    def read_settings(self):
        if SnippetsModel._cached_settings is not None:
            return SnippetsModel._cached_settings
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    SnippetsModel._cached_settings = json.load(stream)
                    return SnippetsModel._cached_settings
                except Exception:
                    return self.get_defaults()
        return self.get_defaults()

    def write_settings(self, data):
        SnippetsModel._cached_settings = data
        folder = os.path.dirname(self.path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)

    @staticmethod
    def get_defaults():
        return dict(snippets={})
