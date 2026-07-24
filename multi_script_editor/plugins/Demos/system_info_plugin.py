import os
import sys
import platform
import subprocess

from vendor.Qt.QtWidgets import QAction
from plugins.plugin_base import BasePlugin
import vendor.Qt


def get_ram_info():
    """
    Get the total system RAM in GB. Supports Windows, macOS, and Linux.
    """
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return f"{round(stat.ullTotalPhys / (1024**3), 2)} GB"
        elif sys.platform == "darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()
            return f"{round(int(out) / (1024**3), 2)} GB"
        elif sys.platform.startswith("linux"):
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        mem_kb = int(line.split()[1])
                        return f"{round(mem_kb / (1024**2), 2)} GB"
    except Exception:
        pass
    return "Unknown RAM"


def get_gpu_info():
    """
    Get GPU names. Supports Windows, macOS, and Linux.
    """
    try:
        if sys.platform == "win32":
            # Try powershell first
            try:
                out = subprocess.check_output(
                    ["powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000  # CREATE_NO_WINDOW
                )
                gpu_names = [line.strip().decode("utf-8", errors="ignore") for line in out.splitlines() if line.strip()]
                if gpu_names:
                    return ", ".join(gpu_names)
            except Exception:
                pass
            # Fallback to wmic
            out = subprocess.check_output(
                "wmic path win32_VideoController get name",
                shell=True,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000
            )
            lines = [line.strip().decode("utf-8", errors="ignore") for line in out.splitlines() if line.strip()]
            if len(lines) > 1:
                return ", ".join(lines[1:])
        elif sys.platform == "darwin":
            out = subprocess.check_output(
                "system_profiler SPDisplaysDataType | grep 'Chipset Model'",
                shell=True
            )
            parts = [line.split(":")[-1].strip().decode("utf-8") for line in out.splitlines() if line.strip()]
            if parts:
                return ", ".join(parts)
        elif sys.platform.startswith("linux"):
            out = subprocess.check_output(
                "lspci | grep -iE 'vga|3d'",
                shell=True
            )
            parts = [line.split(":")[-1].strip().decode("utf-8") for line in out.splitlines() if line.strip()]
            if parts:
                return ", ".join(parts)
    except Exception:
        pass
    return "Unknown GPU"


class SystemInfoPlugin(BasePlugin):
    """
    SystemInfoPlugin demonstrates:
    1. Gathering external system information using Python's platform module and subprocesses.
    2. Using the status bar to show progress for slow operations.
    3. Inserting text exactly where the user's cursor currently is.
    """
    # Plugin Metadata
    name = "System Info"
    description = "Inserts system specifications (OS, Python, Qt, CPU, GPU, RAM, Home Dir) at the current cursor position."
    version = "1.2.0"

    def register(self):
        """
        Create the UI action for this plugin.
        """
        self.action = QAction("Insert System Info", self.editor)
        self.action.triggered.connect(self.insert_system_info)

        # Add to the Plugins menu via the PluginManager
        if hasattr(self.editor, 'plugin_manager'):
            self.editor.plugin_manager.add_plugin_action(self, self.action)

    def unregister(self):
        """
        Remove the UI action safely when the plugin unloads.
        """
        if hasattr(self, 'action'):
            self.action.deleteLater()
            del self.action

    def insert_system_info(self):
        """
        Gathers system information and inserts it into the active editor tab at the cursor position.
        """
        # 1. Ensure a tab is actually open
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return

        # 2. Access the custom tab widget
        widget = self.editor.tab.widget(idx)
        if not widget or not hasattr(widget, 'edit'):
            return

        # 3. Show a temporary status bar message since GPU/RAM checks can take a moment
        self.editor.statusBar().showMessage("Gathering system information...")

        try:
            # Gather standard system information
            os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
            py_ver = sys.version.replace("\n", " ")
            qt_ver = f"{vendor.Qt.__binding__} {vendor.Qt.__binding_version__}"
            processor = platform.processor() or "Unknown CPU"

            # Execute external commands to get hardware info
            ram = get_ram_info()
            gpu = get_gpu_info()

            home_dir = os.path.expanduser("~")

            # Use BasePlugin API to get the current context
            host_context = self.self_context or "Standalone"

            # 4. Format system info as a python comment block
            info_block = (
                f"# ==========================================\n"
                f"# SYSTEM SPECIFICATIONS\n"
                f"# ==========================================\n"
                f"# Host App:   {host_context}\n"
                f"# OS:         {os_name}\n"
                f"# CPU:        {processor}\n"
                f"# GPU:        {gpu}\n"
                f"# RAM:        {ram}\n"
                f"# Home Dir:   {home_dir}\n"
                f"# Python:     {py_ver}\n"
                f"# Qt Binding: {qt_ver}\n"
                f"# ==========================================\n"
            )

            # 5. Insert the text exactly where the user left their cursor
            edit = widget.edit
            cursor = edit.textCursor()

            # Wrap changes in an edit block so the user can undo the insertion with Ctrl+Z
            cursor.beginEditBlock()
            try:
                # cursor.insertText replaces any selected text, or inserts at the caret position
                cursor.insertText(info_block)
            finally:
                cursor.endEditBlock()
        finally:
            # 6. Always clear the status bar message when done, even if an error occurs
            self.editor.statusBar().clearMessage()
