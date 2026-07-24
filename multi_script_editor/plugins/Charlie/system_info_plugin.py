import os
import sys
import platform
import subprocess
import socket

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
    3. Printing dynamically formatted text to the output console.
    """
    # Plugin Metadata
    name = "System Info"
    description = "Prints system specifications (OS, Python, Qt, CPU, GPU, RAM, Home Dir) to the output console."
    version = "1.2.0"

    def register(self):
        """
        Create the UI action for this plugin.
        """
        self.action = QAction("Print system info", self.editor)
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
        Gathers system information and prints it to the output console.
        """
        # 1. Show a temporary status bar message since GPU/RAM checks can take a moment
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

            # Network info
            hostname = platform.node() or socket.gethostname()
            try:
                ip_addr = socket.gethostbyname(hostname)
            except Exception:
                ip_addr = "Unknown IP"

            # Use BasePlugin API to get the current context
            host_context = self.self_context or "Standalone"

            # 2. Format system info as a python comment block
            lines = [
                f"# Hostname:   {hostname}",
                f"# IP Address: {ip_addr}",
                f"# Host App:   {host_context}",
                f"# OS:         {os_name}",
                f"# CPU:        {processor}",
                f"# GPU:        {gpu}",
                f"# RAM:        {ram}",
                f"# Home Dir:   {home_dir}",
                f"# Python:     {py_ver}",
                f"# Qt Binding: {qt_ver}"
            ]

            title = "# SYSTEM SPECIFICATIONS"
            max_len = max(len(line) for line in lines + [title])
            separator = "# " + "=" * (max_len - 2)

            info_block = (
                f"{separator}\n"
                f"{title}\n"
                f"{separator}\n"
                + "\n".join(lines) + "\n"
                f"{separator}\n"
            )

            # 3. Output the text to the editor's output console
            if self.self_output:
                self.self_output.appendPlainText(info_block)

                # Scroll to the bottom of the output
                from vendor.Qt.QtGui import QTextCursor
                self.self_output.moveCursor(QTextCursor.End)
                self.self_output.ensureCursorVisible()

        finally:
            # 4. Always clear the status bar message when done, even if an error occurs
            self.editor.statusBar().clearMessage()
