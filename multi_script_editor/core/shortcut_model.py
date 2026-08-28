import json
import os
import re

from core.settings_model import SettingsModel


class ShortcutProfilesModel:
    DEFAULT_PROFILE = 'Default'
    _INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    _RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5',
        'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }

    def __init__(self, folder=None):
        base_folder = folder or SettingsModel()._get_user_pref_folder()
        self.folder = os.path.join(base_folder, 'shortcut_profiles')

    @classmethod
    def validate_profile_name(cls, name):
        name = (name or '').strip()
        if not name:
            raise ValueError('Enter a profile name.')
        if len(name) > 80:
            raise ValueError('Profile names cannot exceed 80 characters.')
        if name.casefold() == cls.DEFAULT_PROFILE.casefold():
            raise ValueError('The Default profile cannot be overwritten.')
        if name.endswith(('.', ' ')) or cls._INVALID_NAME.search(name):
            raise ValueError('The profile name contains invalid filename characters.')
        if name.upper() in cls._RESERVED_NAMES:
            raise ValueError('That profile name is reserved by Windows.')
        return name

    def _profile_path(self, name):
        name = self.validate_profile_name(name)
        return os.path.join(self.folder, name + '.json')

    def list_profiles(self):
        profiles = [self.DEFAULT_PROFILE]
        if not os.path.isdir(self.folder):
            return profiles

        custom_profiles = []
        for filename in os.listdir(self.folder):
            if not filename.lower().endswith('.json'):
                continue
            path = os.path.join(self.folder, filename)
            try:
                with open(path, 'r', encoding='utf-8') as stream:
                    data = json.load(stream)
                if not isinstance(data, dict):
                    continue
                name = data.get('name', os.path.splitext(filename)[0])
                name = self.validate_profile_name(name)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            if name.casefold() not in {item.casefold() for item in custom_profiles}:
                custom_profiles.append(name)

        return profiles + sorted(custom_profiles, key=str.casefold)

    def read_profile(self, name):
        if (name or '').casefold() == self.DEFAULT_PROFILE.casefold():
            return {}
        try:
            path = self._profile_path(name)
            with open(path, 'r', encoding='utf-8') as stream:
                data = json.load(stream)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

        if not isinstance(data, dict):
            return {}

        shortcuts = data.get('shortcuts', {})
        if not isinstance(shortcuts, dict):
            return {}

        result = {}
        for action_id, sequences in shortcuts.items():
            if not isinstance(action_id, str) or not isinstance(sequences, list):
                continue
            result[action_id] = [
                sequence for sequence in sequences
                if isinstance(sequence, str) and sequence.strip()
            ]
        return result

    def write_profile(self, name, shortcuts):
        name = self.validate_profile_name(name)
        if not isinstance(shortcuts, dict):
            raise ValueError('Shortcut data must be a dictionary.')

        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)
        path = self._profile_path(name)
        temporary_path = path + '.tmp'
        data = {
            'name': name,
            'shortcuts': shortcuts,
        }
        with open(temporary_path, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=4, ensure_ascii=False)
        os.replace(temporary_path, path)

    def delete_profile(self, name):
        path = self._profile_path(name)
        if os.path.isfile(path):
            os.remove(path)
