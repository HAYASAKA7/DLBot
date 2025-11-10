"""
Main entry point for DLBot application.
Initializes and runs the PyQt5 GUI.
"""

import sys
import logging
from pathlib import Path

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "dlbot.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import QApplication
from src.core.app_controller import AppController
from src.gui.main_window import MainWindow


def main():
    """Main entry point."""
    try:
        # Initialize application
        app = QApplication(sys.argv)

        # Create controller
        controller = AppController("config/config.json")

        # Create main window
        window = MainWindow(controller)

        # Show window
        config = controller.config_manager.get_config()
        if config.start_minimized:
            window.hide()
        else:
            window.show()

        logger.info("Application started")

        # Run event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
