import os
import sys

# Set preferred binding
if not os.environ.get("QT_PREFERRED_BINDING"):
    os.environ["QT_PREFERRED_BINDING"] = os.pathsep.join(
        ["PySide2", "PySide6", "PyQt5", "PySide", "PyQt4"]
    )

# Disable High Dpi Scaling in PySide6
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

root = os.path.dirname(__file__)
if root not in sys.path:
    sys.path.append(root)

vendor_path = os.path.join(root, 'vendor')
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)


# BLENDER
def showBlender():
    """
    Launch Multi Script Editor in Blender.
    """
    from .managers import _blender

    return _blender.show()


# HOUDINI
def showHoudini(*args, **kwargs):
    """
    Launch Multi Script Editor in Houdini
    """
    from .managers import _houdini
    return _houdini.show(*args, **kwargs)


# MAYA
def showMaya(dock=False):
    """
    Launch Multi Script Editor in Maya
    """
    from .managers import _maya

    return _maya.show(dock)


# NUKE
def showNuke(panel=False):
    """
    Launch Multi Script Editor in Nuke
    """
    from .managers import _nuke

    return _nuke.show(panel)


def show(*args, **kwargs):
    from . import managers
    if managers.context == 'hou':
        return showHoudini(*args, **kwargs)
    elif managers.context == 'maya':
        # Maya's show takes 'dock' kwarg
        return showMaya(kwargs.get('dock', False))
    elif managers.context == 'nuke':
        # Nuke's show takes 'panel' kwarg
        return showNuke(kwargs.get('panel', False))
    elif managers.context == 'blender':
        return showBlender()

    from . import scriptEditor
    return scriptEditor.show()
