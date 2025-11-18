"""
PyQt5 GUI for DLBot application.
Main window with account list, status indicators, and control buttons.
"""

import sys
import logging
from typing import Optional, Callable
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMenuBar,
    QMenu,
    QDialog,
    QLabel,
    QSystemTrayIcon,
    QMessageBox,
)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QObject

logger = logging.getLogger(__name__)

# Modern stylesheet with rounded corners
STYLESHEET = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    
    QTableWidget {
        background-color: white;
        alternate-background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        gridline-color: #e0e0e0;
    }
    
    QTableWidget::item {
        padding: 4px;
    }
    
    QTableWidget::item:selected {
        background-color: #e3f2fd;
    }
    
    QHeaderView::section {
        background-color: #f0f0f0;
        color: #333;
        padding: 5px;
        border: none;
        border-bottom: 1px solid #e0e0e0;
        font-weight: bold;
    }
    
    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 11px;
        min-width: 60px;
    }
    
    QPushButton:hover {
        background-color: #1976D2;
    }
    
    QPushButton:pressed {
        background-color: #1565C0;
    }
    
    QPushButton:disabled {
        background-color: #bdbdbd;
        color: #757575;
    }
    
    QPushButton#startBtn {
        background-color: #4CAF50;
    }
    
    QPushButton#startBtn:hover {
        background-color: #388E3C;
    }
    
    QPushButton#stopBtn {
        background-color: #f44336;
    }
    
    QPushButton#stopBtn:hover {
        background-color: #d32f2f;
    }
    
    QPushButton#editBtn {
        background-color: #FF9800;
    }
    
    QPushButton#editBtn:hover {
        background-color: #F57C00;
    }
    
    QPushButton#settingsBtn {
        background-color: #FF9800;
    }
    
    QPushButton#settingsBtn:hover {
        background-color: #F57C00;
    }
    
    QPushButton#batchDownloadBtn {
        background-color: #4CAF50;
    }
    
    QPushButton#batchDownloadBtn:hover {
        background-color: #388E3C;
    }

    QPushButton#logsBtn {
        background-color: #9C27B0;
    }

    QPushButton#logsBtn:hover {
        background-color: #7B1FA2;
    }
    
    QPushButton#startAllBtn {
        background-color: #4CAF50;
    }
    
    QPushButton#startAllBtn:hover {
        background-color: #388E3C;
    }
    
    QPushButton#stopAllBtn {
        background-color: #f44336;
    }
    
    QPushButton#stopAllBtn:hover {
        background-color: #d32f2f;
    }
    
    QLabel {
        color: #333;
    }
    
    QWidget {
        background-color: #f5f5f5;
    }
    
    QMenuBar {
        background-color: white;
        border-bottom: 1px solid #e0e0e0;
    }
    
    QMenuBar::item:selected {
        background-color: #e3f2fd;
    }
    
    QMenu {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
    }
    
    QMenu::item:selected {
        background-color: #e3f2fd;
    }
    
    /* QMessageBox button styling */
    QMessageBox QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 11px;
        min-width: 80px;
        min-height: 24px;
    }
    
    QMessageBox QPushButton:hover {
        background-color: #1976D2;
    }
    
    QMessageBox QPushButton:pressed {
        background-color: #1565C0;
    }
    
    QMessageBox QPushButton:focus {
        background-color: #1976D2;
        outline: none;
    }
    
    QMessageBox QPushButton:default {
        background-color: #4CAF50;
    }
    
    QMessageBox QPushButton:default:hover {
        background-color: #388E3C;
    }
    
    /* Style for No button - make it red */
    QMessageBox QPushButton[text="&No"],
    QMessageBox QPushButton[text="No"] {
        background-color: #f44336;
    }
    
    QMessageBox QPushButton[text="&No"]:hover,
    QMessageBox QPushButton[text="No"]:hover {
        background-color: #d32f2f;
    }
    
    QMessageBox QPushButton[text="&No"]:pressed,
    QMessageBox QPushButton[text="No"]:pressed {
        background-color: #b71c1c;
    }
    
    QMessageBox {
        background-color: white;
    }
    
    QMessageBox QLabel {
        color: #333;
    }
"""


class SignalEmitter(QObject):
    """Signal emitter for thread-safe GUI updates."""

    status_changed = pyqtSignal(str, bool)  # account_name, is_listening
    video_found = pyqtSignal(str, str, str, bool, str)  # account, video_id, title, is_live, url
    download_complete = pyqtSignal(str, str)  # account_name, title
    cookie_needed = pyqtSignal(str, str)  # account_name, error_msg


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, app_controller, parent=None):
        """
        Initialize main window.

        Args:
            app_controller: Application controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.signal_emitter = SignalEmitter()

        # Connect signals
        self.signal_emitter.status_changed.connect(self._on_listener_status_changed)
        self.signal_emitter.video_found.connect(self._on_video_found)
        self.signal_emitter.download_complete.connect(self._on_download_complete)
        self.signal_emitter.cookie_needed.connect(self._on_cookie_needed)
        
        # Set cookie needed callback
        self.app_controller.set_cookie_needed_callback(self._handle_cookie_needed)

        self.setWindowTitle("DLBot - Content Listener & Downloader")
        self.setGeometry(100, 100, 1000, 600)
        
        # Apply stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Set window icon
        icon_path = Path(__file__).parent.parent.parent / "DLBot.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Window icon loaded from {icon_path}")
        else:
            logger.warning(f"Icon file not found at {icon_path}")

        self._init_ui()
        self._init_tray()
        self._setup_timer()
        
        # Show first run dialog if this is the first time
        config = self.app_controller.config_manager.get_config()
        if config.first_run:
            self._show_first_run_dialog()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Monitored Accounts")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title)

        # Account table
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(5)
        self.account_table.setHorizontalHeaderLabels([
            "Account", "Platform", "Status", "Last Check", "Actions"
        ])
        self.account_table.setColumnWidth(0, 180)
        self.account_table.setColumnWidth(1, 100)
        self.account_table.setColumnWidth(2, 100)
        self.account_table.setColumnWidth(3, 120)
        self.account_table.setColumnWidth(4, 200)
        self.account_table.horizontalHeader().setStretchLastSection(True)
        # Disable row selection - make table non-selectable
        self.account_table.setSelectionMode(QTableWidget.NoSelection)
        self.account_table.setFocusPolicy(Qt.NoFocus)
        main_layout.addWidget(self.account_table, 1)  # Give table stretch factor

        # Control buttons layout
        control_layout = QHBoxLayout()

        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.setObjectName("startAllBtn")
        self.start_all_btn.clicked.connect(self._on_start_all)
        control_layout.addWidget(self.start_all_btn)

        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.setObjectName("stopAllBtn")
        self.stop_all_btn.clicked.connect(self._on_stop_all)
        control_layout.addWidget(self.stop_all_btn)

        self.batch_download_btn = QPushButton("Batch Download")
        self.batch_download_btn.setObjectName("batchDownloadBtn")
        self.batch_download_btn.clicked.connect(self._on_batch_download)
        control_layout.addWidget(self.batch_download_btn)

        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setObjectName("logsBtn")
        self.logs_btn.clicked.connect(self._on_logs)
        control_layout.addWidget(self.logs_btn)

        control_layout.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.clicked.connect(self._on_settings)
        control_layout.addWidget(self.settings_btn)

        main_layout.addLayout(control_layout)

        central_widget.setLayout(main_layout)

        # Menu bar
        self._init_menu_bar()

        self._refresh_account_table()

    def _init_menu_bar(self) -> None:
        """Initialize menu bar."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self._on_exit)

        view_menu = menu_bar.addMenu("View")
        refresh_action = view_menu.addAction("Refresh")
        refresh_action.triggered.connect(self._refresh_account_table)

        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._on_about)

    def _init_tray(self) -> None:
        """Initialize system tray."""
        tray_menu = QMenu()

        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_window)

        hide_action = tray_menu.addAction("Hide")
        hide_action.triggered.connect(self.hide_window)

        tray_menu.addSeparator()

        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self._on_exit)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setContextMenu(tray_menu)
        
        # Set tray icon
        icon_path = Path(__file__).parent.parent.parent / "DLBot.jpg"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
            logger.info(f"Tray icon loaded from {icon_path}")
        
        self.tray_icon.show()

    def _setup_timer(self) -> None:
        """Setup update timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._refresh_account_table)
        self.update_timer.start(1000)  # Update every second

    def _refresh_account_table(self) -> None:
        """Refresh the account table."""
        accounts = self.app_controller.get_all_accounts()
        listeners = self.app_controller.get_all_listeners()

        self.account_table.setRowCount(len(accounts))

        for row, account in enumerate(accounts):
            # Account name
            name_item = QTableWidgetItem(account.name)
            self.account_table.setItem(row, 0, name_item)

            # Platform
            platform_item = QTableWidgetItem(account.platform.upper())
            self.account_table.setItem(row, 1, platform_item)

            # Status indicator
            listener = listeners.get(account.name)
            is_listening = listener.is_listening() if listener else False

            status_item = QTableWidgetItem("● Listening" if is_listening else "○ Idle")
            status_item.setForeground(QColor("green" if is_listening else "gray"))
            self.account_table.setItem(row, 2, status_item)

            # Last check (placeholder)
            last_check_item = QTableWidgetItem("Just now")
            self.account_table.setItem(row, 3, last_check_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            # Check if this is a Bilibili account
            is_bilibili = account.platform.lower() == "bilibili"

            if is_listening:
                stop_btn = QPushButton("Stop")
                stop_btn.setObjectName("stopBtn")
                stop_btn.setMaximumWidth(70)
                stop_btn.clicked.connect(lambda checked, name=account.name: self._on_stop_account(name))
                action_layout.addWidget(stop_btn)
            else:
                start_btn = QPushButton("Start")
                start_btn.setObjectName("startBtn")
                start_btn.setMaximumWidth(70)
                # Disable start button for Bilibili accounts
                if is_bilibili:
                    start_btn.setEnabled(False)
                    start_btn.setToolTip("Bilibili support is currently disabled.")
                else:
                    start_btn.clicked.connect(lambda checked, name=account.name: self._on_start_account(name))
                action_layout.addWidget(start_btn)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("editBtn")
            edit_btn.setMaximumWidth(70)
            edit_btn.clicked.connect(lambda checked, name=account.name: self._on_edit_account(name))
            action_layout.addWidget(edit_btn)

            action_widget.setLayout(action_layout)
            self.account_table.setCellWidget(row, 4, action_widget)

    def _on_start_account(self, account_name: str) -> None:
        """Start listening for an account."""
        self.app_controller.start_listener(account_name)
        self._refresh_account_table()

    def _on_stop_account(self, account_name: str) -> None:
        """Stop listening for an account."""
        self.app_controller.stop_listener(account_name)
        self._refresh_account_table()

    def _on_start_all(self) -> None:
        """Start all listeners except Bilibili."""
        accounts = self.app_controller.get_all_accounts()
        # Start only non-Bilibili accounts
        for account in accounts:
            if account.platform.lower() != "bilibili":
                self.app_controller.start_listener(account.name)
        self._refresh_account_table()

    def _on_stop_all(self) -> None:
        """Stop all listeners."""
        self.app_controller.stop_all_listeners()
        self._refresh_account_table()

    def _on_batch_download(self) -> None:
        """Open batch download dialog."""
        from src.gui.batch_download_dialog import BatchDownloadDialog

        dialog = BatchDownloadDialog(self.app_controller, self)
        dialog.exec_()

    def _on_logs(self) -> None:
        """Open logs viewer dialog."""
        from src.gui.logs_dialog import LogsDialog

        dialog = LogsDialog(self)
        dialog.exec_()

    def _on_edit_account(self, account_name: str) -> None:
        """Edit an account."""
        from src.gui.settings_dialog import AccountEditDialog

        dialog = AccountEditDialog(self.app_controller, account_name, self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_account_table()

    def _on_settings(self) -> None:
        """Open settings dialog."""
        from src.gui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.app_controller, self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_account_table()

    def _on_about(self) -> None:
        """Show about dialog."""
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "About DLBot",
            "DLBot - Content Listener & Downloader\n\n"
            "Monitor YouTube and Bilibili accounts for new content.\n"
            "Automatically download videos and live streams.\n\n"
            "Version 1.0"
        )

    def _on_listener_status_changed(self, account_name: str, is_listening: bool) -> None:
        """Handle listener status change."""
        logger.info(f"Listener status changed: {account_name} -> {is_listening}")
        self._refresh_account_table()

    def _on_video_found(self, account: str, video_id: str, title: str, is_live: bool, url: str) -> None:
        """Handle new video found."""
        logger.info(f"New {'live' if is_live else 'video'} found: {title}")
        self._refresh_account_table()

    def _on_download_complete(self, account_name: str, title: str) -> None:
        """Handle download completion."""
        logger.info(f"Download complete: {title}")
        self._refresh_account_table()

    def _on_exit(self) -> None:
        """Exit application."""
        self.app_controller.shutdown()
        sys.exit(0)

    def show_window(self) -> None:
        """Show window from tray."""
        self.showNormal()
        self.activateWindow()

    def hide_window(self) -> None:
        """Hide window to tray."""
        self.hide()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        config = self.app_controller.config_manager.get_config()
        if config.minimize_to_tray:
            event.ignore()
            self.hide_window()
        else:
            self._on_exit()

    def _show_first_run_dialog(self) -> None:
        """Show first-run dialog asking about YouTube cookie usage."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Welcome to DLBot")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            "Welcome to DLBot!\n\n"
            "YouTube sometimes requires authentication to download videos.\n"
            "Do you want to use cookies from your Chrome browser for YouTube authentication?\n\n"
            "You can change this setting later in Settings > General."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        result = msg.exec_()
        
        # Save the choice
        use_cookies = (result == QMessageBox.Yes)
        self.app_controller.config_manager.set_use_youtube_cookies(use_cookies)
        self.app_controller.config_manager.set_first_run(False)
        
        logger.info(f"First run: User chose to {'use' if use_cookies else 'not use'} YouTube cookies")

    def _handle_cookie_needed(self, account_name: str, error_msg: str) -> None:
        """Handle cookie needed callback from listener."""
        # Emit signal to ensure this runs on the main GUI thread
        self.signal_emitter.cookie_needed.emit(account_name, error_msg)

    def _on_cookie_needed(self, account_name: str, error_msg: str) -> None:
        """Handle cookie needed signal (runs on main thread)."""
        retry = self.show_cookie_warning_dialog(account_name, error_msg)
        
        if retry:
            # Restart the listener with cookies enabled
            logger.info(f"Restarting listener for {account_name} with cookies enabled")
            self.app_controller.stop_listener(account_name)
            # Update the listener with new cookie setting
            # The listener will pick up the new config automatically when restarted
            self.app_controller.start_listener(account_name)
            self._refresh_account_table()

    def show_cookie_warning_dialog(self, account_name: str, error_msg: str) -> bool:
        """
        Show warning dialog when cookies are needed but not enabled.
        
        Returns:
            True if user wants to enable cookies and retry, False otherwise
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Authentication Required")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"YouTube requires authentication for account '{account_name}'.\n\n"
            f"Error: {error_msg}\n\n"
            "Do you want to enable browser cookies and retry?"
        )
        msg.setInformativeText(
            "If you enable cookies, the application will extract cookies from your Chrome browser.\n"
            "You can disable this later in Settings > General."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        result = msg.exec_()
        
        if result == QMessageBox.Yes:
            # Enable cookies
            self.app_controller.config_manager.set_use_youtube_cookies(True)
            logger.info(f"User enabled YouTube cookies after authentication error for {account_name}")
            return True
        else:
            logger.info(f"User chose to ignore authentication error for {account_name}")
            return False
