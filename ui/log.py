"""Activity log component"""
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt

class ActivityLog(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(
            "background: #000; color: #10B981; font-family: monospace; padding: 10px; border-radius: 8px;"
        )
        self.log("REVA initialized")

    def log(self, message, level="info"):
        colors = {"info": "#60A5FA", "success": "#10B981", "error": "#EF4444", "warning": "#F59E0B"}
        color = colors.get(level, "#60A5FA")
        self.append(f'<span style="color:{color}">[{level.upper()}]</span> {message}')
