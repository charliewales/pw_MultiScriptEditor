import codecs
import json
import os
import shutil

from vendor.Qt.QtGui import QFont


_USE_DEFAULT_FALLBACK = object()
_READ_FAILED = object()


class SettingsModel:
    settings_filename = 'pw_scriptEditor_pref.json'
    _cached_settings = None
    fallback_settings = None
    sanitize_font_weights = True
    create_if_missing = True

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
        else:
            home = os.getenv('HOME') or os.path.expanduser('~')
            appData = home

        if not appData:
            appData = os.path.expanduser('~')

        mse_settings_dir = os.path.join(appData, 'mse_settings')

        if not getattr(SettingsModel, '_migrated', False):
            SettingsModel._migrated = True
            
            if not os.path.exists(mse_settings_dir):
                try:
                    os.makedirs(mse_settings_dir)
                except Exception:
                    pass
            
            files_to_move = [
                'pw_scriptEditor_pref.json',
                'pw_scriptEditor_snippets.json',
                'pw_scriptEditor_themes.json',
                'pw_scriptEditor_session.json',
                'pw_scriptEditor_session_backup.json'
            ]
            folders_to_move = [
                'mse_sessions'
            ]
            
            for f in files_to_move:
                old_path = os.path.join(appData, f)
                new_path = os.path.join(mse_settings_dir, f)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    try:
                        shutil.move(old_path, new_path)
                    except Exception:
                        pass
            
            for folder in folders_to_move:
                old_path = os.path.join(appData, folder)
                new_path = os.path.join(mse_settings_dir, folder)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    try:
                        shutil.move(old_path, new_path)
                    except Exception:
                        pass

        return mse_settings_dir

    def _get_settings_file_path(self):
        path = os.path.normpath(os.path.join(self._get_user_pref_folder(), self.settings_filename)).replace('\\','/')
        if self.create_if_missing and not os.path.exists(path):
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
            if w in (-1, 1, 1.0):
                return w
            if normal_weight == 400:
                if w <= 99:
                    if w <= 25:
                        return 300
                    if w <= 50:
                        return 400
                    if w <= 63:
                        return 600
                    if w <= 75:
                        return 700
                    return 900
            elif normal_weight == 50:
                if w > 99:
                    if w <= 300:
                        return 25
                    if w <= 500:
                        return 50
                    if w <= 600:
                        return 63
                    if w <= 700:
                        return 75
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

    @classmethod
    def _get_cache(cls):
        return cls._cached_settings

    @classmethod
    def _set_cache(cls, data):
        cls._cached_settings = data

    def _fallback_data(self):
        if self.fallback_settings is not None:
            return self.fallback_settings.copy()
        return self.get_defaults()

    def _read_json_file(self, fallback=_USE_DEFAULT_FALLBACK):
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    data = json.load(stream)
                    if self.sanitize_font_weights:
                        self._sanitize_font_weights(data)
                    return data
                except Exception:
                    pass
        return self._fallback_data() if fallback is _USE_DEFAULT_FALLBACK else fallback

    def _write_json_file(self, data):
        folder = os.path.dirname(self.path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)

    def read_settings_from_disk(self):
        return self._read_json_file()

    def read_settings(self):
        cached = self.__class__._get_cache()
        if cached is not None:
            return cached
        data = self.read_settings_from_disk()
        self.__class__._set_cache(data)
        return data

    def write_settings(self, data):
        self.__class__._set_cache(data)
        self._write_json_file(data)

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
                    recent_files=[],
                    recent_commands=[],
                    randomize_custom_at_startup=False,
                    quick_tab_switching=True,
                    auto_close_delimiters=True,
                    diff_tool_path=""
                    )


class SnippetsModel(SettingsModel):
    settings_filename = 'pw_scriptEditor_snippets.json'
    _cached_settings = None
    fallback_settings = {'snippets': {}}
    sanitize_font_weights = False
    create_if_missing = False

    @staticmethod
    def get_defaults():
        return dict(
            snippets={
                # "Python: Main block": 'if __name__ == "__main__":\n    # Main code here\n    pass',
                # "Python: Class Template": "class MyClass(object):\n    def __init__(self):\n        super(MyClass, self).__init__()\n        pass",
                "Qt: Basic Window": 'from vendor.Qt.QtWidgets import QMainWindow\n\n\nclass MyWindow(QMainWindow):\n    def __init__(self, parent=None):\n        super(MyWindow, self).__init__(parent)\n        self.setWindowTitle("My UI")\n        self.resize(400, 300)\n\n\nif __name__ == "__main__":\n    win = MyWindow(self_main)\n    win.show()',
            }
        )

class ThemesModel(SettingsModel):
    settings_filename = 'pw_scriptEditor_themes.json'
    _cached_settings = None

    def read_settings(self):
        if ThemesModel._cached_settings is not None:
            return ThemesModel._cached_settings
        data = self._read_json_file(fallback=_READ_FAILED)
        if data is not _READ_FAILED:
            ThemesModel._cached_settings = data
            return ThemesModel._cached_settings

        # Migration from pw_scriptEditor_pref.json
        pref_model = SettingsModel()
        pref_settings = pref_model.read_settings()
        if 'colors' in pref_settings:
            data = {'colors': pref_settings['colors']}
            self.write_settings(data)
            ThemesModel._cached_settings = data
            return data
            
        return self.get_defaults()

    @staticmethod
    def get_defaults():
        return dict(colors={})


class ClipboardModel(SettingsModel):
    settings_filename = 'pw_scriptEditor_clipboard.json'
    _cached_settings = None
    fallback_settings = {'history': []}
    sanitize_font_weights = False
    create_if_missing = False

    @staticmethod
    def get_defaults():
        return dict(history=[])

