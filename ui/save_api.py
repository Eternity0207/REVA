"""API key screen"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from operate.config import Config

class SaveApiScreen(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Enter Groq API Key")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: #60A5FA;")
        layout.addWidget(title)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("gsk_...")
        self.api_input.setStyleSheet("background: #1F2937; color: white; padding: 12px;")
        layout.addWidget(self.api_input)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background: #3B82F6; color: white; padding: 12px;")
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("background: #374151; color: white; padding: 12px;")
        self.back_btn.clicked.connect(lambda: self.parent.navigate_to("home"))
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    def save(self):
        key = self.api_input.text().strip()
        if key.startswith("gsk_"):
            Config().save_api_key("groq", key)
            self.parent.navigate_to("home")
