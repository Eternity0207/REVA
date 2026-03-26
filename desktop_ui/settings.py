"""Settings tab for REVA"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QMessageBox)
from PyQt5.QtCore import pyqtSignal


class SettingsTab(QWidget):
    """Settings and configuration"""
    
    connect_requested = pyqtSignal(str, str, str)
    disconnect_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Connection settings
        layout.addWidget(QLabel("🔗 Connection Settings"))
        
        layout.addWidget(QLabel("Agent ID"))
        self.agent_id_input = QLineEdit()
        self.agent_id_input.setPlaceholderText("e.g., my-agent")
        layout.addWidget(self.agent_id_input)
        
        layout.addWidget(QLabel("Agent Token"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Your secret token")
        self.token_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.token_input)
        
        layout.addWidget(QLabel("Server URL"))
        self.server_input = QLineEdit()
        self.server_input.setText("http://localhost:8002")
        self.server_input.setPlaceholderText("http://localhost:8002")
        layout.addWidget(self.server_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("✅ Connect")
        self.connect_btn.setStyleSheet("background-color: #10b981;")
        self.connect_btn.clicked.connect(self.connect)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Disconnect")
        self.disconnect_btn.setStyleSheet("background-color: #ef4444;")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(btn_layout)
        
        # Info
        layout.addWidget(QLabel("ℹ️ Information"))
        self.info_label = QLabel(
            "Ready to connect.\n\n"
            "1. Get credentials from https://reva.webhop.me\n"
            "2. Paste Agent ID and Token above\n"
            "3. Click Connect\n"
            "4. Start sending commands!"
        )
        self.info_label.setStyleSheet("color: #94a3b8; padding: 10px; background-color: #1e293b; border-radius: 4px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def connect(self):
        """Connect to backend"""
        agent_id = self.agent_id_input.text().strip()
        token = self.token_input.text().strip()
        server_url = self.server_input.text().strip()
        
        if not agent_id or not token:
            QMessageBox.warning(self, "Invalid Input", "Please enter Agent ID and Token")
            return
        
        self.connect_requested.emit(agent_id, token, server_url)
    
    def disconnect(self):
        """Disconnect"""
        self.disconnect_requested.emit()
    
    def set_connected(self, connected: bool):
        """Update UI based on connection state"""
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.agent_id_input.setReadOnly(connected)
        self.token_input.setReadOnly(connected)
        
        if connected:
            self.info_label.setText("✅ Connected and ready!")
        else:
            self.info_label.setText("❌ Disconnected")
