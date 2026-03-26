#!/usr/bin/env python3
"""REVA Desktop Application - AI OS Control Agent"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from desktop_agent.agent_service import AgentService
from desktop_ui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    logger.info("🚀 Starting REVA Desktop Application")
    
    # Create PyQt5 app
    app = QApplication(sys.argv)
    app.setApplicationName("REVA")
    app.setApplicationVersion("1.0.0")
    
    # Create agent service
    agent_service = AgentService(server_url="http://localhost:8002")
    
    # Create main window
    window = MainWindow(agent_service)
    window.show()
    
    logger.info("✅ Application ready")
    
    # Run
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
