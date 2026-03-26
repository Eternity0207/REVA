"""Main window for REVA desktop app"""
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from .styles import DARK_STYLE
from .dashboard import DashboardTab
from .command_center import CommandCenterTab
from .task_history import TaskHistoryTab
from .settings import SettingsTab
from .widgets import StatusIndicator


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, agent_service):
        super().__init__()
        self.agent_service = agent_service
        self.init_ui()
        self.setup_signals()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("🤖 REVA - AI OS Control Agent")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(DARK_STYLE)
        
        # Central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Status bar at top
        self.status_indicator = StatusIndicator()
        layout.addWidget(self.status_indicator)
        
        # Tabs
        self.tabs = QTabWidget()
        
        self.dashboard = DashboardTab()
        self.command_center = CommandCenterTab()
        self.task_history = TaskHistoryTab()
        self.settings = SettingsTab()
        
        self.tabs.addTab(self.dashboard, "📊 Dashboard")
        self.tabs.addTab(self.command_center, "⚡ Command Center")
        self.tabs.addTab(self.task_history, "📋 History")
        self.tabs.addTab(self.settings, "⚙️ Settings")
        
        layout.addWidget(self.tabs)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)
    
    def setup_signals(self):
        """Connect signals"""
        # Dashboard commands
        self.dashboard.command_requested.connect(self.on_command_requested)
        
        # Command center
        self.command_center.send_command.connect(self.on_command_requested)
        
        # Settings
        self.settings.connect_requested.connect(self.on_connect)
        self.settings.disconnect_requested.connect(self.on_disconnect)
        
        # Agent service callbacks
        self.agent_service.on_connected = self.on_agent_connected
        self.agent_service.on_disconnected = self.on_agent_disconnected
        self.agent_service.on_task_start = self.on_task_start
        self.agent_service.on_task_complete = self.on_task_complete
        self.agent_service.on_task_error = self.on_task_error
    
    def on_connect(self, agent_id: str, token: str, server_url: str):
        """Connect to backend"""
        self.status_bar.showMessage(f"🔄 Connecting to {server_url}...")
        
        # Update agent service
        self.agent_service.server_url = server_url
        
        # Initialize and start
        if self.agent_service.initialize(agent_id, token):
            self.agent_service.start()
            self.status_indicator.set_connected(True)
            self.settings.set_connected(True)
            self.status_bar.showMessage(f"✅ Connected as {agent_id}")
            self.dashboard.update_status(agent_id, True)
        else:
            self.status_bar.showMessage("❌ Failed to connect")
    
    def on_disconnect(self):
        """Disconnect from backend"""
        self.agent_service.stop()
        self.status_indicator.set_connected(False)
        self.settings.set_connected(False)
        self.status_bar.showMessage("Disconnected")
        self.dashboard.update_status("", False)
    
    def on_agent_connected(self):
        """Agent connected"""
        self.status_indicator.set_connected(True)
        self.status_bar.showMessage("✅ Agent connected")
    
    def on_agent_disconnected(self):
        """Agent disconnected"""
        self.status_indicator.set_connected(False)
        self.status_bar.showMessage("❌ Agent disconnected")
    
    def on_command_requested(self, cmd_type: str, params: dict):
        """User requested command"""
        task_id = self.agent_service.send_command_direct(cmd_type, params)
        
        if task_id:
            self.status_bar.showMessage(f"📤 Command sent: {task_id[:8]}...")
            self.dashboard.add_task(task_id, cmd_type, "queued")
            self.task_history.add_task(task_id, cmd_type, "queued", datetime.now().strftime("%H:%M:%S"))
        else:
            self.status_bar.showMessage("❌ Failed to send command")
    
    def on_task_start(self, task_id: str):
        """Task started"""
        self.dashboard.add_task(task_id, "executing", "running")
        self.status_bar.showMessage(f"⏳ Task running: {task_id[:8]}...")
    
    def on_task_complete(self, task_id: str, result: dict):
        """Task completed"""
        self.status_bar.showMessage(f"✅ Task completed: {task_id[:8]}...")
    
    def on_task_error(self, task_id: str, error: str):
        """Task error"""
        self.status_bar.showMessage(f"❌ Task error: {error}")
