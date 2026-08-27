import bpy

from vendor.Qt.QtWidgets import QApplication

from multi_script_editor import scriptEditor


_blender_app = None
_blender_window = None
_QT_EVENT_INTERVAL = 0.01


def _process_qt_events():
    if _blender_app is None:
        return None

    _blender_app.processEvents()
    if _blender_window is not None and _blender_window.isVisible():
        return _QT_EVENT_INTERVAL
    return None


def show():
    global _blender_app, _blender_window

    _blender_app = QApplication.instance() or QApplication([])
    if _blender_window is None:
        _blender_window = scriptEditor.create_editor_instance()

    _blender_window.show()
    _blender_window.raise_()
    _blender_window.activateWindow()

    if not bpy.app.timers.is_registered(_process_qt_events):
        bpy.app.timers.register(
            _process_qt_events,
            first_interval=0.0,
            persistent=True,
        )

    return _blender_window
