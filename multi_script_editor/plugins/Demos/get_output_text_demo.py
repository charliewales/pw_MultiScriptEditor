from vendor.Qt.QtGui import QTextCursor
from vendor.Qt.QtWidgets import QAction
from plugins.plugin_base import BasePlugin


class GetOutputTextDemoPlugin(BasePlugin):
    name = "Get output text"
    description = "Demonstrates how to get selected text from the output widget."
    version = "1.0.0"

    def register(self):
        self.action = QAction("Get output text", self.editor)
        self.action.triggered.connect(self.run_demo)

        if hasattr(self.editor, 'plugin_manager'):
            self.editor.plugin_manager.add_plugin_action(self, self.action)

    def unregister(self):
        if hasattr(self, 'action'):
            self.action.deleteLater()
            del self.action

    def run_demo(self):
        selected_text = self.get_output_selected_text()

        if not selected_text:
            report = ">>> No text selected in the output widget."
        else:
            report = f"--- Selected Text in Output ---\n{selected_text}\n-------------------------------\n"

        if self.self_output:
            self.self_output.appendPlainText(report)
            self.self_output.moveCursor(QTextCursor.End)
            self.self_output.ensureCursorVisible()
