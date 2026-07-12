import json
import os
import codecs
from vendor.Qt.QtGui import QFont
class SettingsModel:
    settings_filename = 'pw_scriptEditor_pref.json'
    _cached_settings = None

    def __init__(self):
        self.path = self._get_settings_file_path()

    def _get_user_pref_folder(self):
        appData = None
        import managers
        if managers.context == 'hou':
            try:
                import hou
                appData = hou.homeHoudiniDirectory()
            except Exception:
                appData = os.getenv('HOUDINI_USER_PREF_DIR')
        elif managers.context == 'maya':
            appData = os.getenv('MAYA_APP_DIR')
        elif managers.context == 'nuke':
            home = os.getenv('HOME') or os.path.expanduser('~')
            appData = os.path.join(home, '.nuke')
        elif managers.context == 'max':
            try:
                import MaxPlus
                appData = os.path.dirname(MaxPlus.PathManager.GetTempDir())
            except Exception:
                pass
        else:
            home = os.getenv('HOME') or os.path.expanduser('~')
            appData = home

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

    def _sanitize_font_weights(self, data):
        try:
            normal_weight = int(getattr(QFont, 'Normal', getattr(QFont.Weight, 'Normal', 50)))
        except Exception:
            normal_weight = 50

        def convert_weight(w):
            if w in (-1, 1, 1.0): return w
            if normal_weight == 400:
                if w <= 99:
                    if w <= 25: return 300
                    if w <= 50: return 400
                    if w <= 63: return 600
                    if w <= 75: return 700
                    return 900
            elif normal_weight == 50:
                if w > 99:
                    if w <= 300: return 25
                    if w <= 500: return 50
                    if w <= 600: return 63
                    if w <= 700: return 75
                    return 87
            return w

        def traverse(obj):
            if isinstance(obj, dict):
                if 'weight' in obj and isinstance(obj['weight'], int):
                    obj['weight'] = convert_weight(obj['weight'])
                for v in obj.values():
                    traverse(v)
            elif isinstance(obj, list):
                for v in obj:
                    traverse(v)

        traverse(data)

    def read_settings_from_disk(self):
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    data = json.load(stream)
                    self._sanitize_font_weights(data)
                    return data
                except Exception:
                    pass
        return self.get_defaults()

    def read_settings(self):
        if SettingsModel._cached_settings is not None:
            return SettingsModel._cached_settings
        SettingsModel._cached_settings = self.read_settings_from_disk()
        return SettingsModel._cached_settings

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
                    highlight_all_occurrences=True,
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
                    return {'snippets': {}}
        return {'snippets': {}}

    def write_settings(self, data):
        SnippetsModel._cached_settings = data
        folder = os.path.dirname(self.path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)

    @staticmethod
    def get_defaults():
        return dict(
            snippets={
                # "Python: Main block": 'if __name__ == "__main__":\n    # Main code here\n    pass',
                # "Python: Class Template": "class MyClass(object):\n    def __init__(self):\n        super(MyClass, self).__init__()\n        pass",
                "Qt: Basic Window": 'from vendor.Qt.QtWidgets import QMainWindow\n\n\nclass MyWindow(QMainWindow):\n    def __init__(self, parent=None):\n        super(MyWindow, self).__init__(parent)\n        self.setWindowTitle("My UI")\n        self.resize(400, 300)\n\n\nif __name__ == "__main__":\n    win = MyWindow(self_main)\n    win.show()',
            }
        )
