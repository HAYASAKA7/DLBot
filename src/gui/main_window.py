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
)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QObject

logger = logging.getLogger(__name__)


class SignalEmitter(QObject):
    """Signal emitter for thread-safe GUI updates."""

    status_changed = pyqtSignal(str, bool)  # account_name, is_listening
    video_found = pyqtSignal(str, str, str, bool, str)  # account, video_id, title, is_live, url
    download_complete = pyqtSignal(str, str)  # account_name, title


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

        self.setWindowTitle("DLBot - Content Listener & Downloader")
        self.setGeometry(100, 100, 1000, 600)

        self._init_ui()
        self._init_tray()
        self._setup_timer()

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
        self.account_table.setColumnWidth(0, 200)
        self.account_table.setColumnWidth(1, 100)
        self.account_table.setColumnWidth(2, 100)
        self.account_table.setColumnWidth(3, 150)
        self.account_table.setColumnWidth(4, 150)
        main_layout.addWidget(self.account_table)

        # Control buttons layout
        control_layout = QHBoxLayout()

        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.clicked.connect(self._on_start_all)
        control_layout.addWidget(self.start_all_btn)

        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.clicked.connect(self._on_stop_all)
        control_layout.addWidget(self.stop_all_btn)

        control_layout.addStretch()

        self.settings_btn = QPushButton("Settings")
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
            action_layout.setContentsMargins(0, 0, 0, 0)

            if is_listening:
                stop_btn = QPushButton("Stop")
                stop_btn.clicked.connect(lambda checked, name=account.name: self._on_stop_account(name))
                action_layout.addWidget(stop_btn)
            else:
                start_btn = QPushButton("Start")
                start_btn.clicked.connect(lambda checked, name=account.name: self._on_start_account(name))
                action_layout.addWidget(start_btn)

            edit_btn = QPushButton("Edit")
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
        """Start all listeners."""
        self.app_controller.start_all_listeners()
        self._refresh_account_table()

    def _on_stop_all(self) -> None:
        """Stop all listeners."""
        self.app_controller.stop_all_listeners()
        self._refresh_account_table()

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
