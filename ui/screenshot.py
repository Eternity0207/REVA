"""Screenshot preview widget"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import base64

class ScreenshotPreview(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #1F2937; border-radius: 8px; padding: 10px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setText("No screenshot")

    def set_image(self, base64_img):
        try:
            data = base64.b64decode(base64_img)
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
        except Exception as e:
            self.setText(f"Error: {e}")
