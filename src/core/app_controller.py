"""
Application controller that orchestrates the listener and GUI.
Manages the overall application state and lifecycle.
"""

import logging
import subprocess
import sys
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta

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
        self._cookie_needed_callback = None
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
                    bilibili_cookie=account.bilibili_cookie,
                    auto_download_videos=account.auto_download_videos,
                    auto_download_lives=account.auto_download_lives,
                    auto_download_videos_count=account.auto_download_videos_count,
                    auto_download_lives_count=account.auto_download_lives_count,
                    use_youtube_cookies=config.use_youtube_cookies,
                    on_status_change=self._on_listener_status_change,
                    on_video_found=self._on_video_found,
                    on_download_complete=self._on_download_complete,
                    on_cookie_needed=self._on_cookie_needed,
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
            config = self.config_manager.get_config()
            self.listener_manager.add_listener(
                account_name=account.name,
                account_url=account.url,
                download_path=account.download_path,
                auto_download_count=account.auto_download_count,
                bilibili_cookie=account.bilibili_cookie,
                auto_download_videos=account.auto_download_videos,
                auto_download_lives=account.auto_download_lives,
                auto_download_videos_count=account.auto_download_videos_count,
                auto_download_lives_count=account.auto_download_lives_count,
                use_youtube_cookies=config.use_youtube_cookies,
                on_status_change=self._on_listener_status_change,
                on_video_found=self._on_video_found,
                on_download_complete=self._on_download_complete,
                on_cookie_needed=self._on_cookie_needed,
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
        # Get the old account to compare auto-download settings
        old_account = self.config_manager.get_account(account.name)
        
        # Update in config
        if self.config_manager.update_account(account):
            # Check if auto-download settings changed
            auto_download_changed = (
                old_account is not None and (
                    old_account.auto_download_videos != account.auto_download_videos or
                    old_account.auto_download_lives != account.auto_download_lives or
                    old_account.auto_download_videos_count != account.auto_download_videos_count or
                    old_account.auto_download_lives_count != account.auto_download_lives_count
                )
            )
            
            # Update or recreate listener
            existing = self.listener_manager.get_listener(account.name)
            if existing:
                existing.stop()
                self.listener_manager.remove_listener(account.name)

            config = self.config_manager.get_config()
            self.listener_manager.add_listener(
                account_name=account.name,
                account_url=account.url,
                download_path=account.download_path,
                auto_download_count=account.auto_download_count,
                bilibili_cookie=account.bilibili_cookie,
                auto_download_videos=account.auto_download_videos,
                auto_download_lives=account.auto_download_lives,
                auto_download_videos_count=account.auto_download_videos_count,
                auto_download_lives_count=account.auto_download_lives_count,
                use_youtube_cookies=config.use_youtube_cookies,
                on_status_change=self._on_listener_status_change,
                on_video_found=self._on_video_found,
                on_download_complete=self._on_download_complete,
                on_cookie_needed=self._on_cookie_needed,
            )
            
            # Log if auto-download settings changed
            if auto_download_changed:
                logger.info(
                    f"Auto-download settings changed for {account.name}: "
                    f"videos={account.auto_download_videos} (count={account.auto_download_videos_count}), "
                    f"lives={account.auto_download_lives} (count={account.auto_download_lives_count}) - Listener restarted"
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

    def download_url(self, url: str, download_path: str) -> bool:
        """
        Download a single video from URL using yt-dlp.
        
        Args:
            url: Video URL to download
            download_path: Directory to save the video
            
        Returns:
            True if download was successful, False otherwise
        """
        try:
            # Ensure download directory exists
            Path(download_path).mkdir(parents=True, exist_ok=True)
            
            # Use yt-dlp to download
            # Format: best available quality with fallback
            output_template = str(Path(download_path) / "%(title)s.%(ext)s")
            
            command = [
                "yt-dlp",
                "--format", "best",
                "--output", output_template,
                "--no-warnings",
                url
            ]
            
            logger.info(f"Starting download: {url} to {download_path}")
            
            # Configure subprocess to hide window on Windows
            startup_info = None
            if sys.platform == 'win32':
                # Hide console window on Windows
                startup_info = subprocess.STARTUPINFO()
                startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup_info.wShowWindow = subprocess.SW_HIDE
            
            # Run yt-dlp command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                startupinfo=startup_info  # Hide window on Windows
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully downloaded: {url}")
                return True
            else:
                logger.error(f"Failed to download {url}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Download timeout for {url}")
            return False
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return False

    def _on_listener_status_change(self, account_name: str, is_listening: bool) -> None:
        """Handle listener status change."""
        logger.info(f"Listener status change: {account_name} -> {is_listening}")

    def _on_video_found(self, account: str, video_id: str, title: str, is_live: bool, url: str) -> None:
        """Handle new video found."""
        logger.info(f"Video found for {account}: {title}")

    def _on_download_complete(self, account_name: str, title: str) -> None:
        """Handle download completion."""
        logger.info(f"Download complete for {account_name}: {title}")

    def _on_cookie_needed(self, account_name: str, error_msg: str) -> None:
        """Handle cookie authentication needed."""
        logger.warning(f"Cookie authentication needed for {account_name}: {error_msg}")
        # Call the callback if set (usually the main window to show a dialog)
        if self._cookie_needed_callback:
            self._cookie_needed_callback(account_name, error_msg)

    def set_cookie_needed_callback(self, callback) -> None:
        """Set callback for when cookies are needed."""
        self._cookie_needed_callback = callback

    def cleanup_old_logs(self) -> bool:
        """
        Clean up old log files based on retention policy.
        Checks all dlbot_*.log files in the logs folder.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            config = self.config_manager.get_config()
            retention_days = config.log_retention_days
            
            log_dir = Path("logs")
            
            if not log_dir.exists():
                logger.info("Logs directory does not exist")
                return True
            
            # Calculate the cutoff time
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            # Find all dlbot_*.log files
            log_files = list(log_dir.glob("dlbot_*.log"))
            
            if not log_files:
                logger.debug("No log files found for cleanup")
                return True
            
            deleted_count = 0
            for log_file in log_files:
                try:
                    # Get file modification time
                    file_mod_time = log_file.stat().st_mtime
                    file_datetime = datetime.fromtimestamp(file_mod_time)
                    
                    # Delete if older than retention period
                    if file_datetime < cutoff_time:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file.name} (age: {(datetime.now() - file_datetime).days} days)")
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting log file {log_file.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old log file(s) (retention: {retention_days} days)")
            else:
                logger.debug(f"No log files older than {retention_days} days to delete")
            
            return True
                
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown application."""
        logger.info("Shutting down application")
        self.stop_all_listeners()
        self.config_manager.save()

