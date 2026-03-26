"""PyQt5 stylesheet for REVA"""

DARK_STYLE = """
    QMainWindow, QDialog, QWidget {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    
    QTabWidget::pane {
        border: 1px solid #1e293b;
    }
    
    QTabBar::tab {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 8px 20px;
        border: none;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: #0ea5e9;
        color: white;
    }
    
    QPushButton {
        background-color: #0ea5e9;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #0284c7;
    }
    
    QPushButton:pressed {
        background-color: #0369a1;
    }
    
    QPushButton:disabled {
        background-color: #475569;
        color: #94a3b8;
    }
    
    QLineEdit, QTextEdit, QComboBox {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        padding: 8px;
        border-radius: 4px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 2px solid #0ea5e9;
    }
    
    QLabel {
        color: #e2e8f0;
    }
    
    QStatusBar {
        background-color: #1e293b;
        color: #94a3b8;
    }
    
    QTableWidget, QTableWidgetItem {
        background-color: #1e293b;
        gridline-color: #334155;
        color: #e2e8f0;
    }
    
    QHeaderView::section {
        background-color: #0f172a;
        color: #94a3b8;
        padding: 5px;
        border: none;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    
    QScrollBar:vertical {
        background-color: #1e293b;
        width: 12px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #475569;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #64748b;
    }
"""
