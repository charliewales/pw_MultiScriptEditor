import platform
import sys, os

main = __import__('__main__')

#######  COMPLETERS  ##############################################

# NUKE
def nukeCompleter(*args):
    from managers import _nuke
    return _nuke.completer(*args)

def getNukeContextMenu(*args):
    from managers import _nuke
    return _nuke.contextMenu(*args)
###################################################################

# HOUDINI
def houdiniCompleter(*args):
    from managers import _houdini
    return _houdini.completer(*args)
def getHoudiniContextMenu(*args):
    from managers import _houdini
    return _houdini.contextMenu(*args)
def houdiniDropEvent(*args):
    from managers import _houdini
    return _houdini.wrapDroppedText(*args)
###################################################################

# MAYA
def mayaCompleter(*args):
    from managers import _maya
    return _maya.completer(*args)

def mayaDropEvent(*args):
    from managers import _maya
    return _maya.wrapDroppedText(*args)
def getMayaContextMenu(*args):
    from managers import _maya
    return _maya.contextMenu(*args)
###################################################################


contextCompleters = dict(
    nuke=nukeCompleter,
    hou=houdiniCompleter,
    maya=mayaCompleter
)

contextMenus = dict(
    hou=getHoudiniContextMenu,
    nuke=getNukeContextMenu,
    maya=getMayaContextMenu
)

dropEvents = dict(
    maya=mayaDropEvent,
    hou=houdiniDropEvent
)

autoImport = dict(
    hou='import hou\n',
    nuke='import nuke\n',
    max='import MaxPlus\n'
)
mayaDragTempData = 'maya_temp_drag_empty_Data'

context = None


exec_name = os.path.basename(sys.executable).lower()

if 'hou' in main.__dict__ or 'houdini' in exec_name or 'hindie' in exec_name or 'hython' in exec_name:
    context = 'hou'
    from managers import _houdini
elif 'cmds' in main.__dict__ or 'maya' in exec_name:
    context = 'maya'
    from managers import _maya
elif 'nuke' in main.__dict__ or 'nuke' in exec_name:
    context = 'nuke'
    from managers import _nuke
elif 'MaxPlus' in main.__dict__ or '3dsmax' in exec_name:
    context = 'max'




if platform.system().lower() == 'windows':
    _s = 'w'
elif platform.system().lower() == 'darwin':
    _s = 'x'
else:
    _s = 'l'