from __future__ import with_statement

import codecs
import json
import os

from core.settings_model import SettingsModel

sessionFilename = 'pw_scriptEditor_session.json'
backupFilename = 'pw_scriptEditor_session_backup.json'


def get_restored_modified_state(file_path, modified):
    return bool(file_path and modified)


def prepare_tabs_for_session_save(tabs):
    saved_tabs = []
    for tab in tabs:
        saved_tab = dict(tab)
        if not saved_tab.get('file_path'):
            saved_tab['modified'] = False
        saved_tabs.append(saved_tab)
    return saved_tabs


def get_session_editor_state(edit, loaded_text):
    if edit is None:
        return loaded_text, False
    if hasattr(edit, 'needs_loading_text'):
        return (
            edit.needs_loading_text or "",
            bool(getattr(edit, 'needs_loading_modified', False)),
        )
    return loaded_text, bool(edit.document().isModified())


class SessionModel(object):
    def __init__(self):
        user_pref_folder = SettingsModel()._get_user_pref_folder()
        self.path = os.path.normpath(os.path.join(user_pref_folder, sessionFilename))
        self._backup_path = os.path.normpath(
            os.path.join(user_pref_folder, backupFilename)
        )
        self._sessions_folder = os.path.join(user_pref_folder, 'mse_sessions')
        if not os.path.exists(self.path):
            self._write_json(self.path, [])

    def _read_json(self, path, fallback=None):
        if fallback is None:
            fallback = []
        if os.path.exists(path):
            with codecs.open(path, "r", "utf-16") as stream:
                try:
                    return json.load(stream)
                except Exception:
                    return fallback
        return fallback

    def _write_json(self, path, data):
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with codecs.open(path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)
        return path

    def readSession(self):
        return self._read_json(self.path)

    def writeSession(self, data):
        return self._write_json(self.path, data)

    # BACKUP METHODS (Auto-save)
    def getBackupPath(self):
        return self._backup_path

    def writeBackup(self, data):
        path = self.getBackupPath()
        return self._write_json(path, data)

    def readBackup(self):
        return self._read_json(self.getBackupPath())

    def backupExists(self):
        return os.path.exists(self.getBackupPath())

    def removeBackup(self):
        path = self.getBackupPath()
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    # NAMED SESSIONS METHODS
    def getSessionsFolder(self):
        folder = self._sessions_folder
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except OSError:
                pass
        return folder

    def listNamedSessions(self):
        folder = self.getSessionsFolder()
        sessions = []
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.endswith('.json'):
                    sessions.append(os.path.splitext(f)[0])
        return sorted(sessions)

    def writeNamedSession(self, name, data):
        folder = self.getSessionsFolder()
        path = os.path.join(folder, "{0}.json".format(name))
        return self._write_json(path, data)

    def readNamedSession(self, name):
        folder = self.getSessionsFolder()
        path = os.path.join(folder, "{0}.json".format(name))
        return self._read_json(path)

    def deleteNamedSession(self, name):
        folder = self.getSessionsFolder()
        path = os.path.join(folder, "{0}.json".format(name))
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
