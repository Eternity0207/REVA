"""REVA Desktop UI"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.home import HomeScreen
from ui.save_api import SaveApiScreen

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REVA")
        self.setStyleSheet("background-color: #1a1a2e;")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomeScreen(self)
        self.save_api = SaveApiScreen(self)

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.save_api)

    def navigate_to(self, screen):
        if screen == "home":
            self.stack.setCurrentWidget(self.home)
        elif screen == "save_api":
            self.stack.setCurrentWidget(self.save_api)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainApp().show()
    sys.exit(app.exec())
