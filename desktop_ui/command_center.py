"""Command center tab for REVA"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QComboBox, QTextEdit, QSpinBox)
from PyQt5.QtCore import pyqtSignal


class CommandCenterTab(QWidget):
    """Send custom commands to agent"""
    
    send_command = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Command type selector
        layout.addWidget(QLabel("Command Type"))
        type_layout = QHBoxLayout()
        self.cmd_type = QComboBox()
        self.cmd_type.addItems([
            "press (keyboard)",
            "click (mouse)",
            "write (text)",
            "sleep (wait)",
            "system_info (info)",
        ])
        self.cmd_type.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.cmd_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Parameter inputs
        layout.addWidget(QLabel("Parameters"))
        self.param_layout = QVBoxLayout()
        self.update_params()
        layout.addLayout(self.param_layout)
        
        layout.addStretch()
        
        # Send button
        send_btn = QPushButton("🚀 Execute Command")
        send_btn.setStyleSheet("background-color: #10b981; font-size: 14px; padding: 10px;")
        send_btn.clicked.connect(self.execute)
        layout.addWidget(send_btn)
        
        self.setLayout(layout)
    
    def on_type_changed(self):
        """Update parameters based on command type"""
        # Clear existing
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.update_params()
    
    def update_params(self):
        """Setup parameter inputs"""
        cmd_type = self.cmd_type.currentText().split()[0].lower()
        
        if cmd_type == "press":
            self.param_layout.addWidget(QLabel("Keys (e.g., 'ctrl t' or 'alt tab')"))
            self.keys_input = QLineEdit()
            self.keys_input.setPlaceholderText("ctrl t")
            self.param_layout.addWidget(self.keys_input)
        
        elif cmd_type == "click":
            self.param_layout.addWidget(QLabel("X Coordinate"))
            self.click_x = QSpinBox()
            self.click_x.setValue(100)
            self.param_layout.addWidget(self.click_x)
            
            self.param_layout.addWidget(QLabel("Y Coordinate"))
            self.click_y = QSpinBox()
            self.click_y.setValue(100)
            self.param_layout.addWidget(self.click_y)
        
        elif cmd_type == "write":
            self.param_layout.addWidget(QLabel("Text to Type"))
            self.text_input = QTextEdit()
            self.text_input.setPlaceholderText("Enter text to type...")
            self.text_input.setMaximumHeight(100)
            self.param_layout.addWidget(self.text_input)
        
        elif cmd_type == "sleep":
            self.param_layout.addWidget(QLabel("Seconds to Sleep"))
            self.sleep_input = QSpinBox()
            self.sleep_input.setValue(1)
            self.sleep_input.setMaximum(300)
            self.param_layout.addWidget(self.sleep_input)
    
    def execute(self):
        """Send command"""
        cmd_type = self.cmd_type.currentText().split()[0].lower()
        params = {}
        
        try:
            if cmd_type == "press":
                keys = self.keys_input.text().split()
                if not keys:
                    keys = ["ctrl", "t"]
                params = {"keys": keys}
            
            elif cmd_type == "click":
                params = {"x": self.click_x.value(), "y": self.click_y.value()}
            
            elif cmd_type == "write":
                text = self.text_input.toPlainText()
                if not text:
                    text = "hello"
                params = {"text": text}
            
            elif cmd_type == "sleep":
                params = {"seconds": self.sleep_input.value()}
            
            self.send_command.emit(cmd_type, params)
        except Exception as e:
            print(f"Error: {e}")
