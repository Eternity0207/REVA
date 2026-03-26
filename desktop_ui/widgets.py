"""Custom PyQt5 widgets for REVA"""
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor


class StatusIndicator(QWidget):
    """Live status indicator"""
    
    def __init__(self):
        super().__init__()
        self.is_connected = False
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #ef4444; font-size: 16px;")
        
        self.text = QLabel("Disconnected")
        self.text.setStyleSheet("color: #94a3b8;")
        
        layout.addWidget(self.dot)
        layout.addWidget(self.text)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def set_connected(self, connected: bool):
        """Update status"""
        self.is_connected = connected
        if connected:
            self.dot.setStyleSheet("color: #22c55e; font-size: 16px;")
            self.text.setText("✅ Connected")
            self.text.setStyleSheet("color: #22c55e;")
        else:
            self.dot.setStyleSheet("color: #ef4444; font-size: 16px;")
            self.text.setText("❌ Disconnected")
            self.text.setStyleSheet("color: #ef4444;")


class TaskCard(QWidget):
    """Single task display card"""
    
    def __init__(self, task_id: str, command: str, status: str, result: str = ""):
        super().__init__()
        self.init_ui(task_id, command, status, result)
    
    def init_ui(self, task_id: str, command: str, status: str, result: str):
        layout = QHBoxLayout()
        
        # Task ID
        task_label = QLabel(task_id[:8] + "...")
        task_label.setStyleSheet("color: #0ea5e9; font-weight: bold; min-width: 80px;")
        layout.addWidget(task_label)
        
        # Command
        cmd_label = QLabel(command)
        cmd_label.setStyleSheet("color: #e2e8f0; min-width: 100px;")
        layout.addWidget(cmd_label)
        
        # Status
        status_label = QLabel(status)
        if status == "completed":
            status_label.setStyleSheet("color: #22c55e;")
        elif status == "running":
            status_label.setStyleSheet("color: #f59e0b;")
        elif status == "failed":
            status_label.setStyleSheet("color: #ef4444;")
        else:
            status_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(status_label)
        
        # Result
        result_label = QLabel(result)
        result_label.setStyleSheet("color: #64748b;")
        layout.addWidget(result_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("QWidget { background-color: #1e293b; padding: 10px; border-radius: 4px; margin: 5px 0; }")
