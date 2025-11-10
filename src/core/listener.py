"""
Core listener module for monitoring YouTube and Bilibili accounts.
Handles automatic video/live download detection and management.
"""

import logging
import threading
import time
import json
from typing import Callable, Optional, Dict
from pathlib import Path
import yt_dlp
from datetime import datetime

logger = logging.getLogger(__name__)


class Listener:
    """
    Monitors a single account for new videos or live streams.
    Runs in a separate thread and downloads content automatically.
    """

    def __init__(
        self,
        account_url: str,
        account_name: str,
        download_path: str,
        check_interval: int = 300,  # 5 minutes
        on_status_change: Optional[Callable] = None,
        on_video_found: Optional[Callable] = None,
        on_download_complete: Optional[Callable] = None,
    ):
        """
        Initialize a listener for an account.

        Args:
            account_url: YouTube or Bilibili channel/user URL
            account_name: Human-readable account name
            download_path: Directory to download videos
            check_interval: Seconds between checks (default 300)
            on_status_change: Callback when listener status changes
            on_video_found: Callback when new video is found
            on_download_complete: Callback when download finishes
        """
        self.account_url = account_url
        self.account_name = account_name
        self.download_path = Path(download_path)
        self.check_interval = check_interval
        self.on_status_change = on_status_change
        self.on_video_found = on_video_found
        self.on_download_complete = on_download_complete

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._is_listening = False
        self._lock = threading.Lock()
        self._last_videos: Dict[str, str] = {}  # Store last found videos

        # Ensure download directory exists and create account subfolder
        self.download_path.mkdir(parents=True, exist_ok=True)
        # Create account-specific subfolder
        self.download_path = self.download_path / account_name
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Load cache from disk
        self._load_cache()

    def start(self) -> bool:
        """Start listening for new content."""
        with self._lock:
            if self._running:
                logger.warning(f"Listener for {self.account_name} already running")
                return False

            self._running = True
            self._is_listening = True

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

        logger.info(f"Started listener for {self.account_name}")
        if self.on_status_change:
            self.on_status_change(self.account_name, True)

        return True

    def stop(self) -> bool:
        """Stop listening for new content."""
        with self._lock:
            if not self._running:
                logger.warning(f"Listener for {self.account_name} not running")
                return False

            self._running = False

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        self._is_listening = False
        
        # Save cache to disk before stopping
        self._save_cache()
        
        logger.info(f"Stopped listener for {self.account_name}")
        if self.on_status_change:
            self.on_status_change(self.account_name, False)

        return True

    def is_listening(self) -> bool:
        """Check if currently listening."""
        with self._lock:
            return self._is_listening

    def _get_cache_file(self) -> Path:
        """Get the cache file path for this account."""
        return self.download_path / ".dlbot_cache.json"

    def _load_cache(self) -> None:
        """Load cached video IDs from disk."""
        try:
            cache_file = self._get_cache_file()
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self._last_videos = json.load(f)
                logger.info(
                    f"Loaded cache for {self.account_name}: {len(self._last_videos)} videos"
                )
            else:
                self._last_videos = {}
        except Exception as e:
            logger.error(f"Error loading cache for {self.account_name}: {e}")
            self._last_videos = {}

    def _save_cache(self) -> None:
        """Save cached video IDs to disk."""
        try:
            cache_file = self._get_cache_file()
            # Ensure parent directory exists
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._last_videos, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Saved cache for {self.account_name}: {len(self._last_videos)} videos to {cache_file}"
            )
        except Exception as e:
            logger.error(f"Error saving cache for {self.account_name}: {e}", exc_info=True)

    def _listen_loop(self) -> None:
        """Main listening loop running in separate thread."""
        while self._running:
            try:
                self._check_for_new_content()
            except Exception as e:
                logger.error(f"Error checking {self.account_name}: {e}")

            time.sleep(self.check_interval)

    def _check_for_new_content(self) -> None:
        """Check for new videos or live streams from the account."""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Don't download, just get info
                "skip_download": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # For YouTube channels: add /videos to get video list
                url = self._prepare_url(self.account_url)

                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.debug(f"Could not fetch info for {self.account_name}: {e}")
                    return

                if "entries" not in info or not info["entries"]:
                    return

                # Check first few videos/streams
                new_videos_found = False
                for entry in info["entries"][:5]:
                    if not entry:
                        continue

                    video_id = entry.get("id", entry.get("url", "unknown"))
                    title = entry.get("title", "Unknown")

                    # Skip if we've already seen this
                    if video_id in self._last_videos:
                        continue

                    # Mark as seen
                    self._last_videos[video_id] = title

                    # Check if it's a live stream or new video
                    is_live = entry.get("is_live", False)
                    new_videos_found = True

                    logger.info(
                        f"Found new {'live stream' if is_live else 'video'}: {title}"
                    )

                    if self.on_video_found:
                        self.on_video_found(
                            self.account_name,
                            video_id,
                            title,
                            is_live,
                            entry.get("url", ""),
                        )

                    # Automatically download
                    if new_videos_found:
                        self._download_content(entry.get("url", ""), title)

        except Exception as e:
            logger.error(f"Error in _check_for_new_content for {self.account_name}: {e}")

    def _prepare_url(self, url: str) -> str:
        """Prepare URL for extraction (add /videos for YouTube channels)."""
        if "youtube.com" in url or "youtu.be" in url:
            if "/videos" not in url and "/live" not in url:
                if not url.endswith("/"):
                    url += "/"
                url += "videos"
        return url

    def _download_content(self, video_url: str, title: str) -> None:
        """Download video/stream content."""
        try:
            logger.info(f"Starting download: {title}")

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",  # Highest quality: best video + best audio
                "postprocessors": [
                    {
                        "key": "FFmpegMerger",
                    },
                ],
                "outtmpl": str(
                    self.download_path / f"{self.account_name}_%(title)s_%(id)s.%(ext)s"
                ),
                "quiet": False,
                "no_warnings": False,
                "progress_hooks": [self._progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            logger.info(f"Completed download: {title}")
            if self.on_download_complete:
                self.on_download_complete(self.account_name, title)

        except Exception as e:
            logger.error(f"Error downloading {title}: {e}")

    def _progress_hook(self, d: dict) -> None:
        """Handle download progress."""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "N/A")
            speed = d.get("_speed_str", "N/A")
            logger.debug(f"Downloading: {percent} at {speed}")
        elif d["status"] == "finished":
            logger.info(f"Finished downloading: {d.get('filename', 'unknown')}")


class ListenerManager:
    """
    Manages multiple listeners for different accounts.
    Coordinates listening threads and account operations.
    """

    def __init__(self):
        """Initialize the listener manager."""
        self._listeners: Dict[str, Listener] = {}
        self._lock = threading.Lock()

    def add_listener(
        self,
        account_name: str,
        account_url: str,
        download_path: str,
        on_status_change: Optional[Callable] = None,
        on_video_found: Optional[Callable] = None,
        on_download_complete: Optional[Callable] = None,
    ) -> Listener:
        """Add a new listener for an account."""
        with self._lock:
            if account_name in self._listeners:
                logger.warning(f"Listener for {account_name} already exists")
                return self._listeners[account_name]

            listener = Listener(
                account_url=account_url,
                account_name=account_name,
                download_path=download_path,
                on_status_change=on_status_change,
                on_video_found=on_video_found,
                on_download_complete=on_download_complete,
            )
            self._listeners[account_name] = listener
            logger.info(f"Added listener for {account_name}")
            return listener

    def remove_listener(self, account_name: str) -> bool:
        """Remove a listener."""
        with self._lock:
            if account_name not in self._listeners:
                return False

            listener = self._listeners[account_name]
            if listener.is_listening():
                listener.stop()

            del self._listeners[account_name]
            logger.info(f"Removed listener for {account_name}")
            return True

    def get_listener(self, account_name: str) -> Optional[Listener]:
        """Get a listener by account name."""
        with self._lock:
            return self._listeners.get(account_name)

    def get_all_listeners(self) -> Dict[str, Listener]:
        """Get all listeners."""
        with self._lock:
            return self._listeners.copy()

    def start_listener(self, account_name: str) -> bool:
        """Start listening for an account."""
        listener = self.get_listener(account_name)
        if listener:
            return listener.start()
        return False

    def stop_listener(self, account_name: str) -> bool:
        """Stop listening for an account."""
        listener = self.get_listener(account_name)
        if listener:
            return listener.stop()
        return False

    def stop_all(self) -> None:
        """Stop all listeners."""
        with self._lock:
            for listener in self._listeners.values():
                try:
                    listener.stop()
                except Exception as e:
                    logger.error(f"Error stopping listener: {e}")
