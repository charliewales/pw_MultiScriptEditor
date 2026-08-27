import os
import shutil
import subprocess
from core.settings_model import SettingsModel


class DiffManager(object):
    """
    Manages the detection, configuration, and execution of external Diff tools.
    """

    COMMON_PATHS = [
        # Windows
        r"C:\Program Files\Meld\Meld.exe",
        r"C:\Program Files (x86)\Meld\Meld.exe",
        r"C:\Program Files\WinMerge\WinMergeU.exe",
        r"C:\Program Files (x86)\WinMerge\WinMergeU.exe",
        r"C:\Program Files\KDiff3\kdiff3.exe",
        r"C:\Program Files (x86)\KDiff3\kdiff3.exe",
        r"C:\Program Files\Beyond Compare 4\BCompare.exe",
        r"C:\Program Files\Beyond Compare 5\BCompare.exe",
        # macOS
        "/Applications/Meld.app/Contents/MacOS/Meld",
        "/Applications/KDiff3.app/Contents/MacOS/kdiff3",
        "/Applications/Beyond Compare.app/Contents/MacOS/bcomp",
        "/Applications/Beyond Compare.app/Contents/MacOS/BCompare",
        "/Applications/Kaleidoscope.app/Contents/MacOS/ksdiff",
        "/Applications/DiffMerge.app/Contents/MacOS/DiffMerge",
        "/Applications/Araxis Merge.app/Contents/MacOS/araxisgitmerge",
        "/opt/homebrew/bin/meld",
        "/opt/homebrew/bin/kdiff3",
        "/opt/homebrew/bin/bcompare",
        "/opt/homebrew/bin/ksdiff",
        "/usr/local/bin/meld",
        "/usr/local/bin/kdiff3",
        "/usr/local/bin/bcompare",
        "/usr/local/bin/ksdiff",
        "/usr/bin/opendiff",
        # Linux
        "/usr/bin/meld",
        "/usr/local/bin/meld",
        "/usr/bin/kdiff3",
        "/usr/local/bin/kdiff3",
        "/usr/bin/bcompare",
        "/usr/local/bin/bcompare",
        "/usr/bin/kompare",
        "/usr/bin/diffmerge",
        "/var/lib/flatpak/exports/bin/org.gnome.Meld",
    ]

    @classmethod
    def is_valid_tool(cls, path_or_cmd):
        if not path_or_cmd:
            return False
        if os.path.exists(path_or_cmd):
            return True
        if shutil.which(path_or_cmd):
            return True
        return False

    @classmethod
    def get_diff_tool_path(cls):
        """
        Retrieves the diff tool path from settings, or attempts to auto-detect it.
        """
        settings = SettingsModel().read_settings()
        configured_path = settings.get("diff_tool_path", "").strip()

        if cls.is_valid_tool(configured_path):
            return configured_path

        # Try to auto-detect from common paths
        for path in cls.COMMON_PATHS:
            if cls.is_valid_tool(path):
                return path

        # Try common CLI names in PATH
        for cmd in [
            "meld",
            "WinMergeU",
            "winmerge",
            "kdiff3",
            "bcompare",
            "bcomp",
            "ksdiff",
            "diffmerge",
            "kompare",
            "opendiff",
        ]:
            if cls.is_valid_tool(cmd):
                return cmd

        return ""

    @classmethod
    def save_diff_tool_path(cls, new_path):
        """
        Saves the configured diff tool path into Settings.
        """
        model = SettingsModel()
        settings = model.read_settings()
        settings["diff_tool_path"] = new_path
        model.write_settings(settings)

    @classmethod
    def configure_diff_tool(cls, parent=None):
        """
        Opens a dialog to configure the diff tool executable path or command.
        """
        from widgets.diff_dialog import DiffToolConfigDialog
        dialog = DiffToolConfigDialog(parent=parent, current_path=cls.get_diff_tool_path())
        if dialog.exec_():
            new_path = dialog.get_path()
            if new_path:
                cls.save_diff_tool_path(new_path)
                return new_path
        return ""

    @classmethod
    def run_diff(cls, path1, path2, parent=None):
        """
        Executes the diff tool with the given paths.
        If no tool is found or configured, prompts the user with a configuration dialog.
        """
        from vendor.Qt.QtWidgets import QMessageBox

        if not path1 or not path2:
            if parent:
                QMessageBox.warning(parent, "Diff Error", "Both paths must be provided to run a diff.")
            return False

        if not os.path.exists(path1):
            if parent:
                QMessageBox.warning(parent, "Diff Error", f"Path 1 does not exist:\n{path1}")
            return False

        if not os.path.exists(path2):
            if parent:
                QMessageBox.warning(parent, "Diff Error", f"Path 2 does not exist:\n{path2}")
            return False

        tool_path = cls.get_diff_tool_path()

        if not cls.is_valid_tool(tool_path):
            # Prompt user to select/enter the tool executable
            tool_path = cls.configure_diff_tool(parent)
            if not tool_path or not cls.is_valid_tool(tool_path):
                return False

        try:
            cmd = [tool_path, path1, path2]
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            if parent:
                QMessageBox.warning(parent, "Diff Error", f"Error launching diff tool:\n{e}")
            return False
