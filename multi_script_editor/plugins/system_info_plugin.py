import os
import sys
import platform
import subprocess

from vendor.Qt.QtWidgets import QAction
from .plugin_base import BasePlugin
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
    Plugin that inserts system specifications (OS, Python, Qt, CPU, GPU, RAM, Home Dir) at the current cursor position.
    """
    name = "System Info"
    description = "Inserts system specifications (OS, Python, Qt, CPU, GPU, RAM, Home Dir) at the current cursor position."
    version = "1.2.0"

    def register(self):
        # Create action
        self.action = QAction("Insert System Info", self.editor)
        self.action.triggered.connect(self.insert_system_info)
        
        # Add to the Plugins menu if it exists
        if hasattr(self.editor, 'plugin_manager') and self.editor.plugin_manager.menu:
            self.editor.plugin_manager.menu.addAction(self.action)

    def unregister(self):
        # Remove action from menu and delete it
        if hasattr(self, 'action'):
            if hasattr(self.editor, 'plugin_manager') and self.editor.plugin_manager.menu:
                self.editor.plugin_manager.menu.removeAction(self.action)
            self.action.deleteLater()
            del self.action

    def insert_system_info(self):
        idx = self.editor.tab.currentIndex()
        if idx < 0:
            return
            
        widget = self.editor.tab.widget(idx)
        if not widget or not hasattr(widget, 'edit'):
            return

        # Show a temporary status bar message since GPU check can take a moment
        self.editor.statusBar().showMessage("Gathering system information...")
        
        try:
            # Gather system information
            os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
            py_ver = sys.version.replace("\n", " ")
            qt_ver = f"{vendor.Qt.__binding__} {vendor.Qt.__binding_version__}"
            processor = platform.processor() or "Unknown CPU"
            ram = get_ram_info()
            gpu = get_gpu_info()
            home_dir = os.path.expanduser("~")
            
            # Determine host app context
            host_context = getattr(self.editor, 'ver', 'Standalone')

            # Format system info as a python comment block
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

            edit = widget.edit
            cursor = edit.textCursor()
            
            # Insert at current cursor position within an edit block for undo/redo
            cursor.beginEditBlock()
            try:
                cursor.insertText(info_block)
            finally:
                cursor.endEditBlock()
        finally:
            self.editor.statusBar().clearMessage()
