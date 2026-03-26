"""Task history tab for REVA"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                            QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt


class TaskHistoryTab(QWidget):
    """View task history"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📋 Task History"))
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Task ID",
            "Command",
            "Status",
            "Time",
            "Result"
        ])
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 150)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def add_task(self, task_id: str, command: str, status: str, timestamp: str):
        """Add task to history"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Task ID (truncated)
        task_cell = QTableWidgetItem(task_id[:8] + "...")
        task_cell.setForeground(self.get_color("#0ea5e9"))
        self.table.setItem(row, 0, task_cell)
        
        # Command
        self.table.setItem(row, 1, QTableWidgetItem(command))
        
        # Status
        status_cell = QTableWidgetItem(status)
        if status == "completed":
            status_cell.setForeground(self.get_color("#22c55e"))
        elif status == "running":
            status_cell.setForeground(self.get_color("#f59e0b"))
        elif status == "failed":
            status_cell.setForeground(self.get_color("#ef4444"))
        self.table.setItem(row, 2, status_cell)
        
        # Timestamp
        time_cell = QTableWidgetItem(timestamp)
        time_cell.setForeground(self.get_color("#94a3b8"))
        self.table.setItem(row, 3, time_cell)
        
        # Result
        result_cell = QTableWidgetItem("See dashboard")
        result_cell.setForeground(self.get_color("#64748b"))
        self.table.setItem(row, 4, result_cell)
        
        # Auto-scroll to top
        self.table.scrollToTop()
    
    def clear_history(self):
        """Clear all history"""
        self.table.setRowCount(0)
    
    @staticmethod
    def get_color(hex_color):
        """Convert hex color to QColor"""
        from PyQt5.QtGui import QColor
        return QColor(hex_color)
