"""Status indicator component"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.dot = QLabel("●")
        self.text = QLabel("Ready")
        self.text.setStyleSheet("color: #9CA3AF;")

        self.layout.addWidget(self.dot)
        self.layout.addWidget(self.text)
        self.setLayout(self.layout)
        self.set_status("ready")

    def set_status(self, status):
        colors = {"ready": "#10B981", "running": "#3B82F6", "error": "#EF4444"}
        self.dot.setStyleSheet(f"color: {colors.get(status, '#9CA3AF')};")
        self.text.setText(status.capitalize())
