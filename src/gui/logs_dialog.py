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
    QComboBox,
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

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Application Logs")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Log file selector layout
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Log File:"))
        
        self.log_file_combo = QComboBox()
        self.log_file_combo.currentTextChanged.connect(self._on_log_file_selected)
        selector_layout.addWidget(self.log_file_combo)
        selector_layout.addStretch()
        
        layout.addLayout(selector_layout)

        # Text edit for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._refresh_log_files)
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
        
        # Load available log files after UI is created
        self._refresh_log_files()

    def _load_logs(self) -> None:
        """Load and display logs from selected file."""
        try:
            selected_file = self.log_file_combo.currentText()
            if not selected_file:
                self.log_text.setText("No log files available.")
                return
            
            log_path = Path("logs") / selected_file
            
            if not log_path.exists():
                self.log_text.setText(f"Log file not found: {selected_file}")
                return

            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Display the logs
            if content:
                self.log_text.setPlainText(content)
                # Scroll to the bottom to show the latest logs
                self.log_text.verticalScrollBar().setValue(
                    self.log_text.verticalScrollBar().maximum()
                )
            else:
                self.log_text.setPlainText(f"(Empty log file)")
            
            logger.info(f"Logs loaded from: {selected_file}")
        except Exception as e:
            error_msg = f"Failed to load logs: {e}"
            self.log_text.setText(error_msg)
            logger.error(error_msg)

    def _refresh_log_files(self) -> None:
        """Refresh the list of available log files."""
        try:
            log_dir = Path("logs")
            
            if not log_dir.exists():
                self.log_file_combo.clear()
                self.log_file_combo.addItem("(no logs folder)")
                return
            
            # Find all dlbot_*.log files and sort them in reverse (newest first)
            log_files = sorted(log_dir.glob("dlbot_*.log"), reverse=True)
            
            # Store current selection
            current_selection = self.log_file_combo.currentText()
            
            self.log_file_combo.clear()
            
            if not log_files:
                self.log_file_combo.addItem("(no log files found)")
                self.log_text.setText("No log files found in logs folder.")
                return
            
            for log_file in log_files:
                self.log_file_combo.addItem(log_file.name)
            
            # Try to restore previous selection, otherwise load the first (newest) file
            if current_selection in [log_file.name for log_file in log_files]:
                self.log_file_combo.setCurrentText(current_selection)
            else:
                self._load_logs()
            
            logger.debug(f"Found {len(log_files)} log files")
        except Exception as e:
            logger.error(f"Error refreshing log files: {e}")

    def _on_log_file_selected(self, filename: str) -> None:
        """Handle log file selection."""
        if filename and not filename.startswith("("):
            self._load_logs()

    def _on_clear_logs(self) -> None:
        """Clear log file with confirmation."""
        selected_file = self.log_file_combo.currentText()
        
        if not selected_file or selected_file.startswith("("):
            QMessageBox.warning(self, "Warning", "No log file selected.")
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            f"Are you sure you want to clear '{selected_file}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                log_path = Path("logs") / selected_file
                
                if log_path.exists():
                    # Clear the file
                    open(log_path, "w").close()
                    
                    self.log_text.setPlainText("(Empty log file)")
                    QMessageBox.information(
                        self,
                        "Success",
                        f"'{selected_file}' has been cleared successfully."
                    )
                    logger.info(f"Log file cleared: {selected_file}")
                else:
                    QMessageBox.information(
                        self,
                        "Info",
                        f"Log file not found: {selected_file}"
                    )
            except Exception as e:
                error_msg = f"Failed to clear logs: {e}"
                QMessageBox.warning(
                    self,
                    "Error",
                    error_msg
                )
                logger.error(error_msg)
