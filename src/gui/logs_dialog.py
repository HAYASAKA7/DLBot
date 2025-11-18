"""
Logs viewer dialog for DLBot application.
Displays application logs and allows users to clear them.
"""

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

# Logs dialog stylesheet
LOGS_STYLESHEET = """
    QDialog {
        background-color: #f5f5f5;
    }
    
    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 11px;
        min-width: 80px;
    }
    
    QPushButton:hover {
        background-color: #1976D2;
    }
    
    QPushButton:pressed {
        background-color: #1565C0;
    }
    
    QPushButton#refreshBtn {
        background-color: #2196F3;
    }
    
    QPushButton#refreshBtn:hover {
        background-color: #1976D2;
    }
    
    QPushButton#clearBtn {
        background-color: #f44336;
    }
    
    QPushButton#clearBtn:hover {
        background-color: #d32f2f;
    }
    
    QPushButton#closeBtn {
        background-color: #757575;
    }
    
    QPushButton#closeBtn:hover {
        background-color: #616161;
    }
    
    QTextEdit {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 4px;
        font-family: Courier New, Monospace;
        font-size: 10px;
    }
    
    QLabel {
        color: #333;
    }
"""


class LogsDialog(QDialog):
    """Dialog for viewing and managing application logs."""

    def __init__(self, parent=None):
        """
        Initialize logs dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("DLBot Logs")
        self.setGeometry(100, 100, 800, 600)
        
        # Apply stylesheet
        self.setStyleSheet(LOGS_STYLESHEET)

        self._init_ui()
        self._load_logs()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Application Logs")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Log file info
        log_path = Path("logs") / "dlbot.log"
        info_label = QLabel(f"Log file: {log_path.absolute()}")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(info_label)

        # Text edit for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._load_logs)
        button_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._on_clear_logs)
        button_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_logs(self) -> None:
        """Load and display logs from file."""
        try:
            log_path = Path("logs") / "dlbot.log"
            
            if not log_path.exists():
                self.log_text.setText("No logs found.")
                return

            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Display the logs
            self.log_text.setPlainText(content)
            
            # Scroll to the bottom to show the latest logs
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
            
            logger.info("Logs loaded successfully")
        except Exception as e:
            error_msg = f"Failed to load logs: {e}"
            self.log_text.setText(error_msg)
            logger.error(error_msg)

    def _on_clear_logs(self) -> None:
        """Clear log file with confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                log_path = Path("logs") / "dlbot.log"
                
                if log_path.exists():
                    # Clear the file
                    open(log_path, "w").close()
                    
                    self.log_text.setPlainText("Logs cleared.")
                    QMessageBox.information(
                        self,
                        "Success",
                        "Logs have been cleared successfully."
                    )
                    logger.info("Logs cleared by user")
                else:
                    QMessageBox.information(
                        self,
                        "Info",
                        "No log file found to clear."
                    )
            except Exception as e:
                error_msg = f"Failed to clear logs: {e}"
                QMessageBox.warning(
                    self,
                    "Error",
                    error_msg
                )
                logger.error(error_msg)
