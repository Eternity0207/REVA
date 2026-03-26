"""Dashboard tab for REVA"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from .widgets import TaskCard


class DashboardTab(QWidget):
    """Main dashboard showing agent status and recent tasks"""
    
    command_requested = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Status section
        layout.addWidget(QLabel("🔌 Agent Status"))
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #1e293b; padding: 15px; border-radius: 4px;")
        status_layout = QVBoxLayout()
        
        self.status_text = QLabel("Status: Initializing...")
        self.status_text.setStyleSheet("color: #e2e8f0;")
        status_layout.addWidget(self.status_text)
        
        self.server_text = QLabel("Server: http://localhost:8002")
        self.server_text.setStyleSheet("color: #94a3b8;")
        status_layout.addWidget(self.server_text)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        # Quick commands
        layout.addWidget(QLabel("⚡ Quick Commands"))
        quick_layout = QHBoxLayout()
        
        self.quick_buttons = []
        commands = [
            ("📸 Screenshot", "screenshot", {}),
            ("🔤 Type Text", "write", {"text": "hello"}),
            ("💤 Sleep", "sleep", {"seconds": 1}),
            ("ℹ️ System Info", "system_info", {}),
        ]
        
        for label, cmd_type, params in commands:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, t=cmd_type, p=params: self.command_requested.emit(t, p))
            quick_layout.addWidget(btn)
        
        layout.addLayout(quick_layout)
        
        # Recent tasks
        layout.addWidget(QLabel("📋 Recent Tasks"))
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout()
        self.tasks_container.setLayout(self.tasks_layout)
        self.tasks_scroll.setWidget(self.tasks_container)
        layout.addWidget(self.tasks_scroll)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_status(self, agent_id: str, is_connected: bool):
        """Update status display"""
        status_text = "✅ Connected" if is_connected else "❌ Disconnected"
        self.status_text.setText(f"Status: {status_text} ({agent_id})")
    
    def add_task(self, task_id: str, command: str, status: str):
        """Add task to display"""
        card = TaskCard(task_id, command, status, "")
        self.tasks_layout.insertWidget(0, card)
        
        # Keep only 10 recent tasks
        while self.tasks_layout.count() > 10:
            item = self.tasks_layout.takeAt(self.tasks_layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()
