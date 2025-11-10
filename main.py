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

# Create handlers with proper encoding
file_handler = logging.FileHandler(log_dir / "dlbot.log", encoding='utf-8')
console_handler = logging.StreamHandler(sys.stdout)
# Set console encoding to UTF-8 if running on Windows
if sys.platform == 'win32' and sys.stdout is not None:
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, ValueError):
        # If stdout is None or doesn't have buffer (e.g., running as EXE without console)
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[file_handler, console_handler],
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
