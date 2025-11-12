"""
Settings dialog for DLBot application.
Allows users to manage accounts, download paths, and preferences.
"""

import logging
from typing import Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QFormLayout,
    QPlainTextEdit,
)
from PyQt5.QtCore import Qt

from src.utils.config import Account

logger = logging.getLogger(__name__)

# Settings dialog stylesheet with colored buttons
SETTINGS_STYLESHEET = """
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
    
    QPushButton#okBtn {
        background-color: #4CAF50;
    }
    
    QPushButton#okBtn:hover {
        background-color: #388E3C;
    }
    
    QPushButton#cancelBtn {
        background-color: #f44336;
    }
    
    QPushButton#cancelBtn:hover {
        background-color: #d32f2f;
    }
    
    QPushButton#addBtn {
        background-color: #2196F3;
    }
    
    QPushButton#addBtn:hover {
        background-color: #1976D2;
    }
    
    QPushButton#removeBtn {
        background-color: #FF9800;
    }
    
    QPushButton#removeBtn:hover {
        background-color: #F57C00;
    }
    
    QPushButton#browseBtn {
        background-color: #2196F3;
    }
    
    QPushButton#browseBtn:hover {
        background-color: #1976D2;
    }
    
    QLineEdit {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
    }
    
    QListWidget {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    QLabel {
        color: #333;
    }
    
    QCheckBox {
        color: #333;
    }
    
    QComboBox {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 4px;
    }
    
    QSpinBox {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 4px;
    }
"""


class SettingsDialog(QDialog):
    """Main settings dialog with tabs for different settings."""

    def __init__(self, app_controller, parent=None):
        """
        Initialize settings dialog.

        Args:
            app_controller: Application controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 700, 500)
        
        # Apply stylesheet
        self.setStyleSheet(SETTINGS_STYLESHEET)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Tab widget
        tabs = QTabWidget()

        # Accounts tab
        accounts_widget = self._create_accounts_tab()
        tabs.addTab(accounts_widget, "Accounts")

        # Storage tab
        storage_widget = self._create_storage_tab()
        tabs.addTab(storage_widget, "Storage")

        # General tab
        general_widget = self._create_general_tab()
        tabs.addTab(general_widget, "General")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_accounts_tab(self) -> QWidget:
        """Create accounts management tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("Manage Accounts")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Accounts list
        self.accounts_list = QListWidget()
        self._refresh_accounts_list()
        layout.addWidget(self.accounts_list)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Account")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self._on_add_account)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit_account_from_list)
        button_layout.addWidget(edit_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("removeBtn")
        remove_btn.clicked.connect(self._on_remove_account)
        button_layout.addWidget(remove_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_storage_tab(self) -> QWidget:
        """Create storage settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Default download path
        path_layout = QHBoxLayout()
        self.download_path_input = QLineEdit()
        config = self.app_controller.config_manager.get_config()
        self.download_path_input.setText(config.default_download_path)
        path_layout.addWidget(self.download_path_input)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseBtn")
        browse_btn.clicked.connect(self._on_browse_download_path)
        path_layout.addWidget(browse_btn)

        layout.addRow("Default Download Path:", path_layout)

        # Check interval
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setMinimum(60)
        self.check_interval_spin.setMaximum(3600)
        self.check_interval_spin.setSuffix(" seconds")
        self.check_interval_spin.setValue(config.check_interval)
        layout.addRow("Check Interval:", self.check_interval_spin)

        # Auto-download
        self.auto_download_check = QCheckBox("Auto-download new content")
        self.auto_download_check.setChecked(config.auto_download)
        layout.addRow("", self.auto_download_check)

        widget.setLayout(layout)
        return widget

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        main_layout = QVBoxLayout()
        layout = QFormLayout()

        config = self.app_controller.config_manager.get_config()

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText(config.theme.capitalize())
        layout.addRow("Theme:", self.theme_combo)

        # Minimize to tray
        self.minimize_to_tray_check = QCheckBox("Minimize to tray instead of closing")
        self.minimize_to_tray_check.setChecked(config.minimize_to_tray)
        layout.addRow("", self.minimize_to_tray_check)

        # Start minimized
        self.start_minimized_check = QCheckBox("Start application minimized")
        self.start_minimized_check.setChecked(config.start_minimized)
        layout.addRow("", self.start_minimized_check)

        main_layout.addLayout(layout)
        main_layout.addStretch()

        # Cache management section
        cache_section_layout = QVBoxLayout()
        cache_label = QLabel("Cache Management")
        cache_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        cache_section_layout.addWidget(cache_label)

        clear_all_btn = QPushButton("Clear All Caches")
        clear_all_btn.setToolTip("Clear cache for all accounts. They will re-download content.")
        clear_all_btn.clicked.connect(self._on_clear_all_caches)
        cache_section_layout.addWidget(clear_all_btn)

        main_layout.addLayout(cache_section_layout)
        widget.setLayout(main_layout)
        return widget

    def _on_clear_all_caches(self) -> None:
        """Clear all caches globally."""
        reply = QMessageBox.question(
            self,
            "Clear All Caches",
            "Are you sure you want to clear the cache for all accounts?\n\n"
            "This will allow all listeners to re-download content that was previously seen.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.app_controller.clear_all_caches():
                QMessageBox.information(
                    self,
                    "Success",
                    "Cache cleared for all accounts."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to clear caches."
                )

    def _refresh_accounts_list(self) -> None:
        """Refresh accounts list."""
        self.accounts_list.clear()
        accounts = self.app_controller.get_all_accounts()

        for account in accounts:
            item = QListWidgetItem(f"{account.name} ({account.platform})")
            item.setData(Qt.UserRole, account.name)
            self.accounts_list.addItem(item)

    def _on_add_account(self) -> None:
        """Add a new account."""
        dialog = AccountEditDialog(self.app_controller, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_accounts_list()

    def _on_edit_account_from_list(self) -> None:
        """Edit selected account."""
        current_item = self.accounts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an account to edit.")
            return

        account_name = current_item.data(Qt.UserRole)
        dialog = AccountEditDialog(self.app_controller, account_name, self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_accounts_list()

    def _on_remove_account(self) -> None:
        """Remove selected account."""
        current_item = self.accounts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an account to remove.")
            return

        account_name = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove '{account_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.app_controller.remove_account(account_name):
                self._refresh_accounts_list()
                QMessageBox.information(self, "Success", "Account removed successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to remove account.")

    def _on_browse_download_path(self) -> None:
        """Browse for download path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            self.download_path_input.text()
        )
        if path:
            self.download_path_input.setText(path)

    def accept(self) -> None:
        """Accept and save changes."""
        try:
            # Update download path
            download_path = self.download_path_input.text()
            if download_path:
                self.app_controller.config_manager.update_default_download_path(download_path)

            # Update check interval
            check_interval = self.check_interval_spin.value()
            self.app_controller.config_manager.update_check_interval(check_interval)

            # Update theme
            theme = self.theme_combo.currentText().lower()
            self.app_controller.config_manager.update_theme(theme)

            # Update minimize to tray
            minimize_to_tray = self.minimize_to_tray_check.isChecked()
            self.app_controller.config_manager.set_minimize_to_tray(minimize_to_tray)

            # Update start minimized
            start_minimized = self.start_minimized_check.isChecked()
            self.app_controller.config_manager.set_start_minimized(start_minimized)

            QMessageBox.information(self, "Success", "Settings saved successfully.")
            super().accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")


class AccountEditDialog(QDialog):
    """Dialog for adding or editing an account."""

    def __init__(self, app_controller, account_name: Optional[str], parent=None):
        """
        Initialize account edit dialog.

        Args:
            app_controller: Application controller instance
            account_name: Account name to edit, or None for new account
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.account_name = account_name
        self.is_new = account_name is None

        title = "Add Account" if self.is_new else "Edit Account"
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 500, 300)
        
        # Apply stylesheet
        self.setStyleSheet(SETTINGS_STYLESHEET)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Account name
        self.name_input = QLineEdit()
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.name_input.setText(account.name)
                self.name_input.setReadOnly(True)  # Can't change name
        form_layout.addRow("Account Name:", self.name_input)

        # Platform
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["YouTube", "Bilibili"])
        
        # Disable Bilibili option - not currently supported
        bilibili_index = self.platform_combo.findText("Bilibili")
        if bilibili_index >= 0:
            model = self.platform_combo.model()
            item = model.item(bilibili_index)
            item.setEnabled(False)
        
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.platform_combo.setCurrentText(account.platform.capitalize())
        form_layout.addRow("Platform:", self.platform_combo)

        # Account URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/c/ChannelName")
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.url_input.setText(account.url)
        form_layout.addRow("Account URL:", self.url_input)

        # Bilibili Cookie (only shown for Bilibili accounts)
        self.cookie_label = QLabel("Bilibili SESSDATA Cookie:")
        self.cookie_input = QPlainTextEdit()
        self.cookie_input.setPlaceholderText("Paste your SESSDATA cookie here (required for Bilibili accounts)")
        self.cookie_input.setMaximumHeight(80)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account and account.bilibili_cookie:
                self.cookie_input.setPlainText(account.bilibili_cookie)
        
        # Initially hide cookie field, show it when Bilibili is selected
        self.cookie_label.setVisible(False)
        self.cookie_input.setVisible(False)
        form_layout.addRow(self.cookie_label, self.cookie_input)
        
        # Connect platform combo to show/hide cookie field
        self.platform_combo.currentTextChanged.connect(self._on_platform_changed)
        self._on_platform_changed(self.platform_combo.currentText())

        # Download path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.path_input.setText(account.download_path)
        else:
            config = self.app_controller.config_manager.get_config()
            self.path_input.setText(config.default_download_path)

        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseBtn")
        browse_btn.clicked.connect(self._on_browse_path)
        path_layout.addWidget(browse_btn)

        form_layout.addRow("Download Path:", path_layout)

        # Auto-download count (kept for backward compatibility, but hidden)
        self.auto_download_count_spin = QSpinBox()
        self.auto_download_count_spin.setMinimum(1)
        self.auto_download_count_spin.setMaximum(5)
        self.auto_download_count_spin.setValue(1)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.auto_download_count_spin.setValue(account.auto_download_count)

        # Enabled checkbox
        self.enabled_check = QCheckBox("Enable listening for this account")
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.enabled_check.setChecked(account.enabled)
        else:
            self.enabled_check.setChecked(True)
        form_layout.addRow("", self.enabled_check)

        # Auto-download options
        auto_download_label = QLabel("Auto-Download Settings:")
        auto_download_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(auto_download_label)

        # Auto-download new videos checkbox
        self.auto_download_videos_check = QCheckBox("Auto-download new videos")
        self.auto_download_videos_check.setChecked(True)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.auto_download_videos_check.setChecked(account.auto_download_videos)
        form_layout.addRow("", self.auto_download_videos_check)

        # Auto-download videos count
        self.auto_download_videos_count_spin = QSpinBox()
        self.auto_download_videos_count_spin.setMinimum(1)
        self.auto_download_videos_count_spin.setMaximum(5)
        self.auto_download_videos_count_spin.setValue(1)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.auto_download_videos_count_spin.setValue(account.auto_download_videos_count)
        form_layout.addRow("  Videos to download:", self.auto_download_videos_count_spin)

        # Auto-download live records checkbox
        self.auto_download_lives_check = QCheckBox("Auto-download live records")
        self.auto_download_lives_check.setChecked(False)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.auto_download_lives_check.setChecked(account.auto_download_lives)
        form_layout.addRow("", self.auto_download_lives_check)

        # Auto-download lives count
        self.auto_download_lives_count_spin = QSpinBox()
        self.auto_download_lives_count_spin.setMinimum(1)
        self.auto_download_lives_count_spin.setMaximum(5)
        self.auto_download_lives_count_spin.setValue(1)
        if not self.is_new:
            account = self.app_controller.config_manager.get_account(self.account_name)
            if account:
                self.auto_download_lives_count_spin.setValue(account.auto_download_lives_count)
        form_layout.addRow("  Lives to download:", self.auto_download_lives_count_spin)

        layout.addLayout(form_layout)

        # Clear cache button (only for existing accounts)
        if not self.is_new:
            cache_button_layout = QHBoxLayout()
            cache_button_layout.addStretch()
            clear_cache_btn = QPushButton("Clear Cache for This Account")
            clear_cache_btn.setObjectName("removeBtn")
            clear_cache_btn.clicked.connect(self._on_clear_cache)
            cache_button_layout.addWidget(clear_cache_btn)
            layout.addLayout(cache_button_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_browse_path(self) -> None:
        """Browse for download path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            self.path_input.text()
        )
        if path:
            self.path_input.setText(path)

    def _on_clear_cache(self) -> None:
        """Clear cache for this account."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            f"Are you sure you want to clear the cache for '{self.account_name}'?\n\n"
            "This will allow the listener to re-download content that was previously seen.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.app_controller.clear_account_cache(self.account_name):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Cache cleared for '{self.account_name}'."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to clear cache for '{self.account_name}'."
                )

    def _on_platform_changed(self, platform_text: str) -> None:
        """Show/hide Bilibili cookie field based on selected platform."""
        is_bilibili = platform_text.lower() == "bilibili"
        self.cookie_label.setVisible(is_bilibili)
        self.cookie_input.setVisible(is_bilibili)

    def _on_accept(self) -> None:
        """Accept and save account."""
        name = self.name_input.text().strip()
        platform = self.platform_combo.currentText().lower()
        url = self.url_input.text().strip()
        download_path = self.path_input.text().strip()
        cookie = self.cookie_input.toPlainText().strip()

        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Account name is required.")
            return

        if not url:
            QMessageBox.warning(self, "Validation Error", "Account URL is required.")
            return

        if not download_path:
            QMessageBox.warning(self, "Validation Error", "Download path is required.")
            return
        
        # Check if Bilibili URL is pasted
        if "bilibili.com" in url.lower() or "b23.tv" in url.lower():
            QMessageBox.warning(
                self,
                "Bilibili Not Supported",
                "Bilibili support is currently disabled.\n\n"
                "We apologize for the inconvenience. Bilibili platform support is under development.\n"
                "Please use YouTube or other supported platforms instead."
            )
            return
        
        # Bilibili cookie is required for Bilibili accounts
        if platform == "bilibili" and not cookie:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Bilibili SESSDATA cookie is required for Bilibili accounts.\n\n"
                "How to get your SESSDATA cookie:\n"
                "1. Go to bilibili.com and log in\n"
                "2. Open DevTools (F12)\n"
                "3. Go to Application → Cookies → bilibili.com\n"
                "4. Find the 'SESSDATA' cookie and copy its value\n"
                "5. Paste it here"
            )
            return

        try:
            account = Account(
                name=name,
                url=url,
                platform=platform,
                download_path=download_path,
                enabled=self.enabled_check.isChecked(),
                auto_download_count=self.auto_download_count_spin.value(),
                bilibili_cookie=cookie if platform == "bilibili" else "",
                auto_download_videos=self.auto_download_videos_check.isChecked(),
                auto_download_lives=self.auto_download_lives_check.isChecked(),
                auto_download_videos_count=self.auto_download_videos_count_spin.value(),
                auto_download_lives_count=self.auto_download_lives_count_spin.value(),
            )

            if self.is_new:
                if self.app_controller.add_account(account):
                    QMessageBox.information(self, "Success", "Account added successfully.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to add account.")
            else:
                if self.app_controller.update_account(account):
                    QMessageBox.information(self, "Success", "Account updated successfully.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update account.")

        except Exception as e:
            logger.error(f"Error saving account: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save account: {e}")
