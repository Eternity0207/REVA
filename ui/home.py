"""Home screen"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from operate.operate import main

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("REVA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #60A5FA;")
        layout.addWidget(title)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command...")
        self.command_input.setStyleSheet("background: #1F2937; color: white; padding: 12px;")
        layout.addWidget(self.command_input)

        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setStyleSheet("background: #3B82F6; color: white; padding: 12px;")
        self.execute_btn.clicked.connect(self.execute)
        layout.addWidget(self.execute_btn)

        self.setLayout(layout)

    def execute(self):
        cmd = self.command_input.text().strip()
        if cmd:
            main(model="fast-gpt", terminal_prompt=cmd)
            self.command_input.clear()
