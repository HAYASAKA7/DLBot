"""
Configuration management for the DLBot application.
Handles loading, saving, and validating user configurations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Represents a monitored account."""

    name: str
    url: str
    platform: str  # 'youtube' or 'bilibili'
    download_path: str
    enabled: bool = True
    check_interval: int = 300  # seconds
    auto_download_count: int = 1  # Number of new videos to auto-download (1-5) - DEPRECATED, use auto_download_videos_count
    bilibili_cookie: str = ""  # Bilibili SESSDATA cookie (required for Bilibili accounts)
    auto_download_videos: bool = True  # Auto-download new videos
    auto_download_lives: bool = False  # Auto-download live records
    auto_download_videos_count: int = 1  # Number of new videos to auto-download (1-5)
    auto_download_lives_count: int = 1  # Number of live records to auto-download (1-5)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AppConfig:
    """Main application configuration."""

    accounts: List[Account]
    default_download_path: str
    check_interval: int = 300
    auto_download: bool = True
    minimize_to_tray: bool = True
    start_minimized: bool = False
    theme: str = "light"  # 'light' or 'dark'

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "accounts": [acc.to_dict() for acc in self.accounts],
            "default_download_path": self.default_download_path,
            "check_interval": self.check_interval,
            "auto_download": self.auto_download,
            "minimize_to_tray": self.minimize_to_tray,
            "start_minimized": self.start_minimized,
            "theme": self.theme,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Create from dictionary."""
        accounts = [
            Account.from_dict(acc) for acc in data.get("accounts", [])
        ]
        return cls(
            accounts=accounts,
            default_download_path=data.get("default_download_path", "downloads"),
            check_interval=data.get("check_interval", 300),
            auto_download=data.get("auto_download", True),
            minimize_to_tray=data.get("minimize_to_tray", True),
            start_minimized=data.get("start_minimized", False),
            theme=data.get("theme", "light"),
        )


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: str = "config/config.json"):
        """Initialize configuration manager."""
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config: Optional[AppConfig] = None
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load configuration from file or create default."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config = AppConfig.from_dict(data)
                    logger.info(f"Loaded config from {self.config_path}")
            else:
                self._config = self._create_default_config()
                self.save()
        except Exception as e:
            logger.error(f"Error loading config: {e}. Creating default.")
            self._config = self._create_default_config()

    def _create_default_config(self) -> AppConfig:
        """Create default configuration."""
        downloads_path = str(Path("downloads").absolute())
        return AppConfig(
            accounts=[],
            default_download_path=downloads_path,
            check_interval=300,
            auto_download=True,
            minimize_to_tray=True,
            start_minimized=False,
            theme="light",
        )

    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            self._load_or_create()
        return self._config

    def save(self) -> bool:
        """Save configuration to file."""
        try:
            if self._config is None:
                logger.error("No configuration to save")
                return False

            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved config to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def add_account(self, account: Account) -> bool:
        """Add an account to configuration."""
        if self._config is None:
            return False

        # Check if account already exists
        if any(acc.name == account.name for acc in self._config.accounts):
            logger.warning(f"Account {account.name} already exists")
            return False

        self._config.accounts.append(account)
        logger.info(f"Added account: {account.name}")
        return self.save()

    def remove_account(self, account_name: str) -> bool:
        """Remove an account from configuration."""
        if self._config is None:
            return False

        self._config.accounts = [
            acc for acc in self._config.accounts if acc.name != account_name
        ]
        logger.info(f"Removed account: {account_name}")
        return self.save()

    def update_account(self, account: Account) -> bool:
        """Update an account in configuration."""
        if self._config is None:
            return False

        for i, acc in enumerate(self._config.accounts):
            if acc.name == account.name:
                self._config.accounts[i] = account
                logger.info(f"Updated account: {account.name}")
                return self.save()

        logger.warning(f"Account {account.name} not found")
        return False

    def get_account(self, account_name: str) -> Optional[Account]:
        """Get a specific account."""
        if self._config is None:
            return None

        for acc in self._config.accounts:
            if acc.name == account_name:
                return acc
        return None

    def get_accounts(self) -> List[Account]:
        """Get all accounts."""
        if self._config is None:
            return []
        return self._config.accounts.copy()

    def update_default_download_path(self, path: str) -> bool:
        """Update default download path."""
        if self._config is None:
            return False

        self._config.default_download_path = path
        return self.save()

    def update_check_interval(self, interval: int) -> bool:
        """Update default check interval."""
        if self._config is None:
            return False

        if interval < 60:
            logger.warning("Check interval should be at least 60 seconds")
            return False

        self._config.check_interval = interval
        return self.save()

    def update_theme(self, theme: str) -> bool:
        """Update theme setting."""
        if self._config is None:
            return False

        if theme not in ["light", "dark"]:
            logger.warning(f"Invalid theme: {theme}")
            return False

        self._config.theme = theme
        return self.save()

    def set_minimize_to_tray(self, enabled: bool) -> bool:
        """Set minimize to tray preference."""
        if self._config is None:
            return False

        self._config.minimize_to_tray = enabled
        return self.save()

    def set_start_minimized(self, enabled: bool) -> bool:
        """Set start minimized preference."""
        if self._config is None:
            return False

        self._config.start_minimized = enabled
        return self.save()
