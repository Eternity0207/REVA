"""Home screen"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from operate.config import Config
from operate.operate import main

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Title
        title = QLabel("REVA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #60A5FA;")
        layout.addWidget(title)

        subtitle = QLabel("AI OS Controlling Agent")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #9CA3AF; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # API status
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #F87171; padding: 10px;")
        layout.addWidget(self.status_label)

        # Command input
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter your command...")
        self.command_input.setStyleSheet(
            "background: #1F2937; color: white; padding: 15px; border-radius: 8px; font-size: 14px;"
        )
        self.command_input.returnPressed.connect(self.execute)
        layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()

        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3B82F6,stop:1 #8B5CF6); "
            "color: white; padding: 15px; border-radius: 8px; font-weight: bold;"
        )
        self.execute_btn.clicked.connect(self.execute)
        btn_layout.addWidget(self.execute_btn)

        self.settings_btn = QPushButton("API Key")
        self.settings_btn.setStyleSheet(
            "background: #374151; color: white; padding: 15px; border-radius: 8px;"
        )
        self.settings_btn.clicked.connect(lambda: self.parent.navigate_to("save_api"))
        btn_layout.addWidget(self.settings_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.check_api()

    def check_api(self):
        if Config().validation("groq", False):
            self.status_label.setText("API key not configured")
            self.status_label.setVisible(True)
            self.execute_btn.setEnabled(False)
        else:
            self.status_label.setVisible(False)
            self.execute_btn.setEnabled(True)

    def execute(self):
        cmd = self.command_input.text().strip()
        if not cmd:
            return

        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("Running...")

        try:
            main(model="fast-gpt", terminal_prompt=cmd)
        finally:
            self.execute_btn.setEnabled(True)
            self.execute_btn.setText("Execute")
            self.command_input.clear()
