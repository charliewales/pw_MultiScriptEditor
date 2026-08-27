import os
import platform
import sys

main = __import__('__main__')

#######  COMPLETERS  ##############################################

# NUKE
def nukeCompleter(*args):
    from . import _nuke
    return _nuke.completer(*args)

def getNukeContextMenu(*args):
    from . import _nuke
    return _nuke.contextMenu(*args)
###################################################################

# HOUDINI
def houdiniCompleter(*args):
    from . import _houdini
    return _houdini.completer(*args)
def getHoudiniContextMenu(*args):
    from . import _houdini
    return _houdini.contextMenu(*args)
def houdiniDropEvent(*args):
    from . import _houdini
    return _houdini.wrapDroppedText(*args)
###################################################################

# MAYA
def mayaCompleter(*args):
    from . import _maya
    return _maya.completer(*args)

def mayaDropEvent(*args):
    from . import _maya
    return _maya.wrapDroppedText(*args)
def getMayaContextMenu(*args):
    from . import _maya
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
    blender='import bpy\n'
)
context = None


exec_name = os.path.basename(sys.executable).lower()

if 'hou' in main.__dict__ or 'houdini' in exec_name or 'hindie' in exec_name or 'hython' in exec_name:
    context = 'hou'
    from . import _houdini
elif 'cmds' in main.__dict__ or 'maya' in exec_name:
    context = 'maya'
    from . import _maya
elif 'nuke' in main.__dict__ or 'nuke' in exec_name:
    context = 'nuke'
    from . import _nuke
elif 'bpy' in sys.modules or 'blender' in exec_name:
    context = 'blender'
    from . import _blender as _blender




_s = {
    'windows': 'w',
    'darwin': 'x',
}.get(platform.system().lower(), 'l')
