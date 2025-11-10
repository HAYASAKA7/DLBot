"""
Application controller that orchestrates the listener and GUI.
Manages the overall application state and lifecycle.
"""

import logging
from typing import Dict, Optional
from pathlib import Path

from src.core.listener import Listener, ListenerManager
from src.utils.config import ConfigManager, Account

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller."""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize application controller.

        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.listener_manager = ListenerManager()
        self._initialize_listeners()

    def _initialize_listeners(self) -> None:
        """Initialize listeners from configuration."""
        config = self.config_manager.get_config()

        for account in config.accounts:
            if account.enabled:
                self.listener_manager.add_listener(
                    account_name=account.name,
                    account_url=account.url,
                    download_path=account.download_path,
                    auto_download_count=account.auto_download_count,
                    on_status_change=self._on_listener_status_change,
                    on_video_found=self._on_video_found,
                    on_download_complete=self._on_download_complete,
                )

    def get_all_accounts(self) -> list:
        """Get all accounts from configuration."""
        return self.config_manager.get_accounts()

    def get_account(self, account_name: str) -> Optional[Account]:
        """Get a specific account."""
        return self.config_manager.get_account(account_name)

    def add_account(self, account: Account) -> bool:
        """Add a new account."""
        if self.config_manager.add_account(account):
            # Create listener for this account
            self.listener_manager.add_listener(
                account_name=account.name,
                account_url=account.url,
                download_path=account.download_path,
                auto_download_count=account.auto_download_count,
                on_status_change=self._on_listener_status_change,
                on_video_found=self._on_video_found,
                on_download_complete=self._on_download_complete,
            )
            return True
        return False

    def remove_account(self, account_name: str) -> bool:
        """Remove an account."""
        # Stop listener
        self.listener_manager.remove_listener(account_name)
        return self.config_manager.remove_account(account_name)

    def update_account(self, account: Account) -> bool:
        """Update an account."""
        # Update in config
        if self.config_manager.update_account(account):
            # Update or recreate listener
            existing = self.listener_manager.get_listener(account.name)
            if existing:
                existing.stop()
                self.listener_manager.remove_listener(account.name)

            self.listener_manager.add_listener(
                account_name=account.name,
                account_url=account.url,
                download_path=account.download_path,
                auto_download_count=account.auto_download_count,
                on_status_change=self._on_listener_status_change,
                on_video_found=self._on_video_found,
                on_download_complete=self._on_download_complete,
            )
            return True
        return False

    def get_all_listeners(self) -> Dict[str, Listener]:
        """Get all listeners."""
        return self.listener_manager.get_all_listeners()

    def start_listener(self, account_name: str) -> bool:
        """Start a listener."""
        return self.listener_manager.start_listener(account_name)

    def stop_listener(self, account_name: str) -> bool:
        """Stop a listener."""
        return self.listener_manager.stop_listener(account_name)

    def start_all_listeners(self) -> None:
        """Start all listeners."""
        for listener in self.listener_manager.get_all_listeners().values():
            try:
                listener.start()
            except Exception as e:
                logger.error(f"Error starting listener: {e}")

    def stop_all_listeners(self) -> None:
        """Stop all listeners."""
        self.listener_manager.stop_all()

    def clear_account_cache(self, account_name: str) -> bool:
        """Clear cache for a specific account."""
        return self.listener_manager.clear_cache(account_name)

    def clear_all_caches(self) -> bool:
        """Clear cache for all accounts."""
        return self.listener_manager.clear_all_caches()

    def _on_listener_status_change(self, account_name: str, is_listening: bool) -> None:
        """Handle listener status change."""
        logger.info(f"Listener status change: {account_name} -> {is_listening}")

    def _on_video_found(self, account: str, video_id: str, title: str, is_live: bool, url: str) -> None:
        """Handle new video found."""
        logger.info(f"Video found for {account}: {title}")

    def _on_download_complete(self, account_name: str, title: str) -> None:
        """Handle download completion."""
        logger.info(f"Download complete for {account_name}: {title}")

    def shutdown(self) -> None:
        """Shutdown application."""
        logger.info("Shutting down application")
        self.stop_all_listeners()
        self.config_manager.save()
