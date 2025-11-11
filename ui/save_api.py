from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
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
        layout.setSpacing(15)
        self.setMaximumWidth(800)

        # Title
        title = QLabel("Enter your Groq API Key")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #60A5FA; margin-bottom: 40px;")
        layout.addWidget(title)

        # Main Content Frame
        main_frame = QFrame()
        main_frame.setStyleSheet("background-color: #111827; border-radius: 12px; padding: 20px;")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(15)

        # Info Label
        info_label = QLabel("Get your free API key from https://console.groq.com")
        info_label.setStyleSheet("color: #9CA3AF; font-size: 13px; margin-bottom: 10px;")
        main_layout.addWidget(info_label)

        # Error Message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #F87171; margin-bottom: 10px;")
        self.error_label.setVisible(False)
        main_layout.addWidget(self.error_label)

        # API Key Input
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Enter your Groq API key (gsk_...)...")
        self.api_input.setStyleSheet("""
            background-color: #1F2937;
            color: #D1D5DB;
            padding: 12px;
            border-radius: 5px;
            font-size: 14px;
        """)
        main_layout.addWidget(self.api_input)

        # Save Button
        self.save_btn = QPushButton("Save API Key")
        self.save_btn.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #9333EA);
            color: white;
            padding: 12px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        main_layout.addWidget(self.save_btn)

        # Back Button
        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("""
            background-color: #374151;
            color: white;
            padding: 12px;
            border-radius: 5px;
            font-size: 14px;
            margin-top: 10px;
        """)
        self.back_btn.clicked.connect(lambda: self.parent.navigate_to("home"))
        main_layout.addWidget(self.back_btn)

        layout.addWidget(main_frame)
        self.setLayout(layout)

        # Connect signals
        self.api_input.returnPressed.connect(self.save_api_key)
        self.save_btn.clicked.connect(self.save_api_key)

    def save_api_key(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.error_label.setText("API Key cannot be empty")
            self.error_label.setVisible(True)
            return

        if not api_key.startswith("gsk_"):
            self.error_label.setText("Invalid Groq API key format (should start with gsk_)")
            self.error_label.setVisible(True)
            return

        try:
            self.save_btn.setText("Saving...")
            self.save_btn.setEnabled(False)
            config = Config()
            config.save_api_key("groq", api_key)

            self.api_input.clear()
            self.error_label.setVisible(False)
            self.parent.navigate_to("home")
        except Exception as e:
            self.error_label.setText(f"Error saving API Key: {str(e)}")
            self.error_label.setVisible(True)
        finally:
            self.save_btn.setText("Save API Key")
            self.save_btn.setEnabled(True)
