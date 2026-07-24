from __future__ import with_statement

import codecs
import json
import os

from core.settings_model import SettingsModel

sessionFilename = 'pw_scriptEditor_session.json'
backupFilename = 'pw_scriptEditor_session_backup.json'


class SessionModel(object):
    def __init__(self):
        self.path = os.path.normpath(os.path.join(SettingsModel()._get_user_pref_folder(), sessionFilename))
        if not os.path.exists(self.path):
            folder = os.path.dirname(self.path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            with codecs.open(self.path, "w", "utf-16") as stream:
                json.dump([], stream, indent=4)

    def readSession(self):
        if os.path.exists(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    return json.load(stream)
                except:
                    return []
        return []

    def writeSession(self, data):
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)
        return self.path

    # BACKUP METHODS (Auto-save)
    def getBackupPath(self):
        return os.path.normpath(os.path.join(SettingsModel()._get_user_pref_folder(), backupFilename))

    def writeBackup(self, data):
        path = self.getBackupPath()
        with codecs.open(path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)
        return path

    def readBackup(self):
        path = self.getBackupPath()
        if os.path.exists(path):
            with codecs.open(path, "r", "utf-16") as stream:
                try:
                    return json.load(stream)
                except:
                    return []
        return []

    def backupExists(self):
        return os.path.exists(self.getBackupPath())

    def removeBackup(self):
        path = self.getBackupPath()
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

    # NAMED SESSIONS METHODS
    def getSessionsFolder(self):
        folder = os.path.join(SettingsModel()._get_user_pref_folder(), 'mse_sessions')
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
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
        with codecs.open(path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)
        return path

    def readNamedSession(self, name):
        folder = self.getSessionsFolder()
        path = os.path.join(folder, "{0}.json".format(name))
        if os.path.exists(path):
            with codecs.open(path, "r", "utf-16") as stream:
                try:
                    return json.load(stream)
                except:
                    return []
        return []

    def deleteNamedSession(self, name):
        folder = self.getSessionsFolder()
        path = os.path.join(folder, "{0}.json".format(name))
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
