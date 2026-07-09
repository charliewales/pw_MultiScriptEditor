import os
import sys

root = os.path.dirname(__file__)
if not root in sys.path:
    sys.path.append(root)


# HOUDINI
def showHoudini(*args, **kwargs):
    """
    Launch Multi Script Editor in Houdini
    """
    from .managers import _houdini
    return _houdini.show(*args, **kwargs)


# NUKE
def showNuke(panel=False):
    """
    Launch Multi Script Editor in Nuke
    """
    from .managers import _nuke

    _nuke.show(panel)


# MAYA
def showMaya(dock=False):
    """
    Launch Multi Script Editor in Maya
    """
    from .managers import _maya

    _maya.show(dock)


# 3DSMAX PLUS
def show3DSMax():
    """
    Launch Multi Script Editor in 3DSMax
    """
    sys.argv = []
    from .managers import _3dsmax

    _3dsmax.show()


def show():
    import scriptEditor

    scriptEditor.show()
