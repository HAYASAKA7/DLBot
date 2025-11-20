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
from PyQt5.QtCore import Qt, QTimer, QFileSystemWatcher, QMetaObject, Q_ARG

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
        
        # Guard flag to prevent recursive updates
        self._updating = False
        
        # Flag to track if this is the first load (to auto-scroll to bottom)
        self._first_load = True
        
        # Track the last log content to avoid unnecessary updates
        self._last_log_content = ""
        
        # Flag to indicate if we should scroll after update (only for manual refresh)
        self._scroll_after_update = False
        
        # Setup file watcher for real-time updates
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self._on_log_file_changed)
        
        # Setup timer to periodically reload logs (fallback)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._on_update_timer)
        self.update_timer.start(1000)  # Update every 1 second

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
        refresh_btn.clicked.connect(self._on_refresh_button_clicked)
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
        # Prevent recursive updates
        if self._updating:
            return
        
        try:
            self._updating = True
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
            
            # Only update if content has changed
            if content != self._last_log_content:
                self._last_log_content = content
                
                # Get scrollbar before updating
                scrollbar = self.log_text.verticalScrollBar()
                old_value = scrollbar.value()
                old_max = scrollbar.maximum()
                
                # Update the text - this will trigger scrollbar reset
                self.log_text.setPlainText(content)
                
                # Now adjust scrollbar based on the situation
                if self._scroll_after_update or self._first_load:
                    # User explicitly wants scroll to bottom (first load or manual refresh)
                    QTimer.singleShot(10, self._scroll_to_bottom)
                    self._first_load = False
                    self._scroll_after_update = False
                else:
                    # Auto-update: intelligently preserve scroll
                    new_max = scrollbar.maximum()
                    # If user was at/near bottom, keep at bottom (new logs)
                    # Otherwise restore their scroll position
                    if old_max > 0 and old_value >= old_max - 10:
                        # Was at bottom - stay at bottom
                        QTimer.singleShot(10, self._scroll_to_bottom)
                    else:
                        # Was somewhere else - restore position
                        QTimer.singleShot(10, lambda: scrollbar.setValue(old_value))
            else:
                # Content unchanged - just reset flags
                self._first_load = False
                self._scroll_after_update = False
                
        except Exception as e:
            error_msg = f"Failed to load logs: {e}"
            self.log_text.setText(error_msg)
        finally:
            self._updating = False

    def _scroll_to_bottom(self) -> None:
        """Scroll text edit to the bottom."""
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_refresh_button_clicked(self) -> None:
        """Handle manual refresh button click."""
        # Set flag to scroll after update for manual refresh
        self._scroll_after_update = True
        # Clear cached content to force update
        self._last_log_content = ""
        # Reload logs
        self._load_logs()

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
        except Exception as e:
            logger.error(f"Error refreshing log files: {e}")

    def _on_log_file_selected(self, filename: str) -> None:
        """Handle log file selection."""
        if filename and not filename.startswith("("):
            # Remove old file from watcher
            watched_files = self.file_watcher.files()
            for f in watched_files:
                self.file_watcher.removePath(f)
            
            # Add new file to watcher
            log_path = Path("logs") / filename
            if log_path.exists():
                self.file_watcher.addPath(str(log_path))
            
            # Reset first load flag so scroll resets when switching files
            self._first_load = True
            self._last_log_content = ""  # Clear cached content for new file
            
            # Load the logs
            self._load_logs()

    def _on_log_file_changed(self, filepath: str) -> None:
        """Handle log file change detected by file watcher."""
        # Reload the current log file
        selected_file = self.log_file_combo.currentText()
        if selected_file and not selected_file.startswith("("):
            log_path = Path("logs") / selected_file
            if str(log_path) == filepath:
                self._load_logs()

    def _on_update_timer(self) -> None:
        """Periodic timer callback to check for new log files and reload current logs."""
        selected_file = self.log_file_combo.currentText()
        
        # Always reload the current log file to get latest content
        if selected_file and not selected_file.startswith("("):
            self._load_logs()
        
        # Check if new log files were created (new day)
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = sorted(log_dir.glob("dlbot_*.log"), reverse=True)
            current_items = [self.log_file_combo.itemText(i) for i in range(self.log_file_combo.count())]
            
            # If we have new files, refresh the combo box
            new_file_names = [f.name for f in log_files]
            if new_file_names != current_items:
                self._refresh_log_files()
                # Restore selection if it still exists
                if selected_file in new_file_names:
                    self.log_file_combo.setCurrentText(selected_file)

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

    def closeEvent(self, event) -> None:
        """Handle dialog close to clean up resources."""
        # Stop the update timer
        self.update_timer.stop()
        
        # Remove watched files
        watched_files = self.file_watcher.files()
        for f in watched_files:
            self.file_watcher.removePath(f)
        
        super().closeEvent(event)
