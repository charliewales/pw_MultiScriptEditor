import json
import os
import codecs
from managers import context

settingsFilename = 'pw_scriptEditor_pref.json'


def userPrefFolder():
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


def settingsFile():
    path = os.path.normpath(os.path.join(userPrefFolder(), settingsFilename)).replace('\\','/')
    if not os.path.exists(path):
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with codecs.open(path, "w", "utf-16") as stream:
            json.dump(scriptEditorClass.defaults(), stream, indent=4)
    return path


class scriptEditorClass(object):
    def __init__(self):
        super(scriptEditorClass, self).__init__()
        self.path = settingsFile()

    def readSettings(self):
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with codecs.open(self.path, "r", "utf-16") as stream:
                try:
                    return json.load(stream)
                except:
                    return self.defaults()
        return self.defaults()

    def writeSettings(self, data):
        with codecs.open(self.path, "w", "utf-16") as stream:
            json.dump(data, stream, indent=4)

    @staticmethod
    def defaults():
        return dict(geometry=None,
                    outFontSize=8,
                    wrap=True,
                    out_wrap=True,
                    echo_execute=True,
                    clear_execute=False,
                    always_ontop=True,
                    show_whitespace=True,
                    font={"family": "Courier", "pointSize": 10, "weight": 1, "italic": False}
                    )
