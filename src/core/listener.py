"""
Core listener module for monitoring YouTube and Bilibili accounts.
Handles automatic video/live download detection and management.
"""

import logging
import threading
import time
import json
import requests
import re
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
        auto_download_count: int = 1,  # Number of new videos to auto-download (1-5) - DEPRECATED
        bilibili_cookie: str = "",  # Bilibili SESSDATA cookie for authentication
        auto_download_videos: bool = True,  # Auto-download new videos
        auto_download_lives: bool = False,  # Auto-download live records
        auto_download_videos_count: int = 1,  # Number of new videos to auto-download (1-5)
        auto_download_lives_count: int = 1,  # Number of live records to auto-download (1-5)
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
            auto_download_count: Number of new videos to auto-download (1-5, default 1) - DEPRECATED
            bilibili_cookie: Bilibili SESSDATA cookie (required for Bilibili accounts)
            auto_download_videos: Auto-download new videos (default True)
            auto_download_lives: Auto-download live records (default False)
            auto_download_videos_count: Number of new videos to auto-download (1-5, default 1)
            auto_download_lives_count: Number of live records to auto-download (1-5, default 1)
            on_status_change: Callback when listener status changes
            on_video_found: Callback when new video is found
            on_download_complete: Callback when download finishes
        """
        self.account_url = account_url
        self.account_name = account_name
        self.download_path = Path(download_path)
        self.check_interval = check_interval
        self.auto_download_count = auto_download_count
        self.auto_download_videos_count = auto_download_videos_count
        self.auto_download_lives_count = auto_download_lives_count
        self.bilibili_cookie = bilibili_cookie
        self.auto_download_videos = auto_download_videos
        self.auto_download_lives = auto_download_lives
        self.on_status_change = on_status_change
        self.on_video_found = on_video_found
        self.on_download_complete = on_download_complete

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._is_listening = False
        self._lock = threading.Lock()
        self._last_videos: Dict[str, str] = {}  # Store last found videos
        self._last_lives: Dict[str, str] = {}  # Store last found live streams

        # Ensure download directory exists and create account subfolder
        self.download_path.mkdir(parents=True, exist_ok=True)
        # Create account-specific subfolder
        self.download_path = self.download_path / account_name
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Create lives subfolder if auto_download_lives is enabled
        self.lives_path = None
        if self.auto_download_lives:
            self.lives_path = self.download_path / "lives"
            self.lives_path.mkdir(parents=True, exist_ok=True)
        
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

    def _get_lives_cache_file(self) -> Path:
        """Get the lives cache file path for this account."""
        if self.lives_path:
            return self.lives_path / ".dlbot_lives_cache.json"
        return self.download_path / ".dlbot_lives_cache.json"

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
            
            # Load lives cache
            lives_cache_file = self._get_lives_cache_file()
            if lives_cache_file.exists():
                with open(lives_cache_file, 'r', encoding='utf-8') as f:
                    self._last_lives = json.load(f)
                logger.info(
                    f"Loaded lives cache for {self.account_name}: {len(self._last_lives)} lives"
                )
            else:
                self._last_lives = {}
        except Exception as e:
            logger.error(f"Error loading cache for {self.account_name}: {e}")
            self._last_videos = {}
            self._last_lives = {}

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
            
            # Save lives cache
            lives_cache_file = self._get_lives_cache_file()
            lives_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(lives_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._last_lives, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Saved lives cache for {self.account_name}: {len(self._last_lives)} lives to {lives_cache_file}"
            )
        except Exception as e:
            logger.error(f"Error saving cache for {self.account_name}: {e}", exc_info=True)

    def clear_cache(self) -> bool:
        """Clear the cache for this account (allows re-downloading of seen videos)."""
        try:
            with self._lock:
                self._last_videos.clear()
                logger.info(f"Cleared cache for {self.account_name}")
            self._save_cache()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache for {self.account_name}: {e}")
            return False

    def _file_exists_in_destination(self, video_id: str) -> bool:
        """Check if a video file already exists in the destination folder."""
        try:
            # Check if any file with the video_id exists in the download path
            for file in self.download_path.iterdir():
                if video_id in file.name:
                    logger.debug(f"File already exists: {file.name}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    def _listen_loop(self) -> None:
        """Main listening loop running in separate thread."""
        while self._running:
            try:
                threads = []
                
                # Check for new videos if auto_download_videos is enabled
                if self.auto_download_videos:
                    video_thread = threading.Thread(
                        target=self._check_for_new_videos,
                        daemon=True,
                    )
                    video_thread.start()
                    threads.append(video_thread)
                
                # Check for live streams if auto_download_lives is enabled
                if self.auto_download_lives:
                    lives_thread = threading.Thread(
                        target=self._check_for_new_lives,
                        daemon=True,
                    )
                    lives_thread.start()
                    threads.append(lives_thread)
                
                # Wait for both checks to complete before next interval
                for thread in threads:
                    thread.join()
                    
            except Exception as e:
                logger.error(f"Error checking {self.account_name}: {e}")

            time.sleep(self.check_interval)

    def _check_for_new_videos(self) -> None:
        """Check for new videos from the account."""
        try:
            # Detect if this is a Bilibili URL
            is_bilibili = "bilibili.com" in self.account_url or "b23.tv" in self.account_url
            
            logger.info(f"[Videos Check] Starting videos check for {self.account_name}")
            
            # For Bilibili with cookie, use the official API
            if is_bilibili and self.bilibili_cookie:
                self._check_bilibili_api(is_live=False)
                return
            
            # Otherwise use yt-dlp for YouTube and Bilibili without cookie
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Don't download, just get info
                "skip_download": True,
                "socket_timeout": 30,
            }
            
            # Add Bilibili-specific options (use web scraping for search, not API)
            if is_bilibili:
                ydl_opts.update({
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://search.bilibili.com/",
                    },
                    "retries": {"max_retries": 3, "backoff_factor": 1.5},
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # For YouTube channels: add /videos to get video list (not live)
                # For Bilibili: convert to search URL
                url = self._prepare_url(self.account_url, is_live=False)
                
                logger.info(f"[Videos Check] Fetching from URL: {url}")

                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.warning(f"[Videos Check] Could not fetch info for {self.account_name}: {e}")
                    return

                if "entries" not in info or not info["entries"]:
                    logger.info(f"[Videos Check] No entries found for {self.account_name}")
                    return

                # For Bilibili search results, filter out non-video content
                # Video entries have 'ext' field (content type)
                entries = info["entries"]
                logger.info(f"[Videos Check] Found {len(entries)} total entries for {self.account_name}")
                
                if is_bilibili:
                    # Filter to only include videos (vt=2 is video type in Bilibili search)
                    entries = [e for e in entries if e and e.get("ext") == "mp4" or (e.get("_type") == "video")]
                
                if not entries:
                    logger.info(f"[Videos Check] No video entries found for {self.account_name} after filtering")
                    return

                logger.info(f"[Videos Check] Found {len(entries)} video entries after filtering for {self.account_name}")

                # Check first N videos (based on auto_download_videos_count)
                new_videos_found = False
                for idx, entry in enumerate(entries[: self.auto_download_videos_count]):
                    if not entry:
                        logger.debug(f"[Videos Check] Entry {idx} is None, skipping")
                        continue

                    video_id = entry.get("id", entry.get("url", "unknown"))
                    title = entry.get("title", "Unknown")
                    
                    logger.info(f"[Videos Check] Processing entry {idx+1}: ID={video_id}, Title={title}")

                    # Skip if we've already seen this
                    if video_id in self._last_videos:
                        continue

                    # Skip if file already exists in destination folder
                    if self._file_exists_in_destination(video_id):
                        logger.info(f"File already exists in destination: {title}")
                        self._last_videos[video_id] = title  # Mark as seen anyway
                        continue

                    # Mark as seen
                    self._last_videos[video_id] = title

                    # For YouTube, the /videos endpoint should only return non-live videos
                    # For Bilibili, we already filtered them above
                    # Skip if it's marked as live (shouldn't happen if /videos is used)
                    is_live = entry.get("is_live", False)
                    if is_live:
                        logger.debug(f"Skipping live stream in videos check: {title}")
                        continue

                    new_videos_found = True

                    logger.info(f"Found new video: {title}")

                    if self.on_video_found:
                        self.on_video_found(
                            self.account_name,
                            video_id,
                            title,
                            False,
                            entry.get("url", ""),
                        )

                    # Automatically download in background thread to avoid blocking the listening loop
                    if new_videos_found:
                        download_thread = threading.Thread(
                            target=self._download_content,
                            args=(entry.get("url", ""), title, False),
                            daemon=True,
                        )
                        download_thread.start()

        except Exception as e:
            logger.error(f"Error in _check_for_new_videos for {self.account_name}: {e}")

    def _check_for_new_lives(self) -> None:
        """Check for new live streams from the account."""
        try:
            # Detect if this is a Bilibili URL
            is_bilibili = "bilibili.com" in self.account_url or "b23.tv" in self.account_url
            
            logger.info(f"[Lives Check] Starting live streams check for {self.account_name}")
            
            # For Bilibili with cookie, use the official API
            if is_bilibili and self.bilibili_cookie:
                logger.info(f"[Lives Check] Using Bilibili API for {self.account_name}")
                self._check_bilibili_api(is_live=True)
                return
            
            # Otherwise use yt-dlp for YouTube and Bilibili without cookie
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Don't download, just get info
                "skip_download": True,
                "socket_timeout": 30,
            }
            
            # Add Bilibili-specific options
            if is_bilibili:
                ydl_opts.update({
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://search.bilibili.com/",
                    },
                    "retries": {"max_retries": 3, "backoff_factor": 1.5},
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # For YouTube channels: add /streams to get live streams
                # For Bilibili: convert to search URL
                url = self._prepare_url(self.account_url, is_live=True)
                
                logger.info(f"[Lives Check] Fetching from URL: {url}")

                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.warning(f"[Lives Check] Could not fetch info for {self.account_name}: {e}")
                    return

                if "entries" not in info or not info["entries"]:
                    logger.info(f"[Lives Check] No entries found for {self.account_name}")
                    return

                entries = info["entries"]
                logger.info(f"[Lives Check] Found {len(entries)} total entries for {self.account_name}")
                
                # NOTE: YouTube's /streams endpoint returns content from the Streams tab
                # Filter out upcoming/scheduled streams that haven't started yet
                # Scheduled streams have duration=None (no content to download yet)
                live_entries = []
                for entry in entries:
                    if not entry:
                        continue
                    
                    duration = entry.get("duration")
                    title = entry.get("title", "Unknown")
                    
                    # Skip scheduled/upcoming streams that have no duration (no content yet)
                    if duration is None:
                        logger.info(f"[Lives Check] Skipping scheduled/upcoming stream (duration=None): {title}")
                        continue
                    
                    live_entries.append(entry)
                
                logger.info(f"[Lives Check] Found {len(live_entries)} stream entries after filtering upcoming for {self.account_name}")
                
                if not live_entries:
                    logger.info(f"[Lives Check] No live stream entries found for {self.account_name}")
                    return

                # Check first N live streams
                new_lives_found = False
                for idx, entry in enumerate(live_entries[: self.auto_download_lives_count]):
                    if not entry:
                        logger.debug(f"[Lives Check] Entry {idx} is None, skipping")
                        continue

                    video_id = entry.get("id", entry.get("url", "unknown"))
                    title = entry.get("title", "Unknown")
                    
                    logger.info(f"[Lives Check] Processing entry {idx+1}: ID={video_id}, Title={title}")

                    # Skip scheduled/upcoming streams (no content yet)
                    # YouTube marks upcoming streams as 'is_live', but they're actually scheduled
                    # Check if stream has actual content by looking for duration or other indicators
                    is_currently_live = entry.get("is_live", False)
                    duration = entry.get("duration")
                    
                    logger.debug(f"[Lives Check] Stream {title}: is_live={is_currently_live}, duration={duration}")
                    
                    # If is_live is True but duration is 0 or None, it's scheduled/upcoming
                    if is_currently_live and (duration is None or duration == 0):
                        logger.info(f"[Lives Check] Skipping scheduled/upcoming stream (no content yet): {title}")
                        continue

                    # Skip if we've already seen this live
                    if video_id in self._last_lives:
                        logger.debug(f"[Lives Check] Already seen: {title}")
                        continue

                    # Skip if file already exists in lives folder
                    if self.lives_path and self._file_exists_in_lives(video_id):
                        logger.info(f"[Lives Check] Live file already exists in destination: {title}")
                        self._last_lives[video_id] = title  # Mark as seen anyway
                        continue

                    # Mark as seen
                    self._last_lives[video_id] = title
                    new_lives_found = True

                    logger.info(f"[Lives Check] Found new live stream: {title}")

                    if self.on_video_found:
                        self.on_video_found(
                            self.account_name,
                            video_id,
                            title,
                            True,
                            entry.get("url", ""),
                        )

                    # Automatically download to lives folder in background thread to avoid blocking the listening loop
                    if new_lives_found and self.lives_path:
                        download_thread = threading.Thread(
                            target=self._download_content,
                            args=(entry.get("url", ""), title, True),
                            daemon=True,
                        )
                        download_thread.start()

        except Exception as e:
            logger.error(f"Error in _check_for_new_lives for {self.account_name}: {e}")

    def _file_exists_in_lives(self, video_id: str) -> bool:
        """Check if a live file already exists in the lives folder."""
        try:
            if not self.lives_path or not self.lives_path.exists():
                return False
            # Check if any file with the video_id exists in the lives path
            for file in self.lives_path.iterdir():
                if video_id in file.name and file.is_file():
                    logger.debug(f"Live file already exists: {file.name}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking live file existence: {e}")
            return False

    def _prepare_url(self, url: str, is_live: bool = False) -> str:
        """Prepare URL for extraction (handle YouTube and Bilibili differently)."""
        # For YouTube: add /videos to get video list, or search for Streams playlist for live content
        if "youtube.com" in url or "youtu.be" in url:
            if "/videos" not in url and "/streams" not in url and "/live" not in url and "playlist" not in url:
                if not url.endswith("/"):
                    url += "/"
                
                if is_live:
                    # For live content, try to find a "Streams" or "Premieres" playlist
                    # Many YouTubers organize livestream archives in a playlist
                    # For now, just append /streams tab - it may contain livestream replays
                    # Users can manually set up a "Streams" playlist if they want more control
                    url += "streams"
                else:
                    # For regular videos, use /videos endpoint
                    url += "videos"
        
        # For Bilibili: convert to search URL if it's a channel/user URL
        if "bilibili.com" in url or "b23.tv" in url:
            # If it's a channel/user page, convert to search with the channel name
            if "/space/" in url or "mid=" in url:
                # Extract channel/user identifier and convert to search
                url = self._convert_bilibili_to_search(url)
        
        return url
    
    def _convert_bilibili_to_search(self, url: str) -> str:
        """Convert Bilibili channel URL to search URL sorted by upload time."""
        try:
            # Try to extract channel name from the account_url if it's already provided
            # For now, we'll use yt-dlp to get the channel name first
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                uploader = info.get("uploader", "")
                
                if uploader:
                    # Create search URL with channel name, sorted by publish date
                    from urllib.parse import quote
                    search_url = f"https://search.bilibili.com/all?keyword={quote(uploader)}&from_source=webtop_search&order=pubdate&vt=35004072"
                    logger.info(f"Converted Bilibili channel to search URL: {search_url}")
                    return search_url
        except Exception as e:
            logger.warning(f"Could not convert Bilibili URL to search: {e}")
        
        return url
    
    def _extract_host_mid(self, url: str) -> Optional[str]:
        """Extract Bilibili user ID (mid) from URL."""
        logger.debug(f"[Extract Mid] Attempting to extract user ID from: {url}")
        
        try:
            # Try to extract mid from various Bilibili URL formats FIRST
            # Format 1: space.bilibili.com/123456 or bilibili.com/space/123456
            logger.debug(f"[Extract Mid] Trying regex pattern: space\\.bilibili\\.com/(\\d+)")
            match = re.search(r'space\.bilibili\.com/(\d+)', url)
            if match:
                mid = match.group(1)
                logger.info(f"[Extract Mid] Successfully extracted mid from URL: {mid}")
                return mid
            
            # Format 2: /space/123456 (with or without query params)
            logger.debug(f"[Extract Mid] Trying regex pattern: /space/(\\d+)")
            match = re.search(r'/space/(\d+)', url)
            if match:
                mid = match.group(1)
                logger.info(f"[Extract Mid] Successfully extracted mid from URL: {mid}")
                return mid
            
            # Format 3: mid=123456
            logger.debug(f"[Extract Mid] Trying regex pattern: [?&]mid=(\\d+)")
            match = re.search(r'[?&]mid=(\d+)', url)
            if match:
                mid = match.group(1)
                logger.info(f"[Extract Mid] Successfully extracted mid from query param: {mid}")
                return mid
            
            logger.warning(f"[Extract Mid] Could not extract mid using regex patterns from {url}")
            logger.debug(f"[Extract Mid] Will NOT attempt yt-dlp extraction due to rate limiting")
            
        except Exception as e:
            logger.error(f"[Extract Mid] Error during extraction: {e}")
        
        logger.warning(f"[Extract Mid] Failed to extract Bilibili user ID from {url}")
        return None
    
    def _check_bilibili_api(self, is_live: bool = False) -> None:
        """Check for new videos or lives using Bilibili's official API."""
        try:
            # Extract user ID from URL
            host_mid = self._extract_host_mid(self.account_url)
            if not host_mid:
                logger.error(f"Could not extract Bilibili user ID from {self.account_url}")
                return
            
            logger.info(f"[Bilibili API] Account: {self.account_name}, User ID: {host_mid}, Type: {'lives' if is_live else 'videos'}")
            
            # Build API URL
            api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={host_mid}"
            
            # Prepare headers with cookie
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"https://space.bilibili.com/{host_mid}",
                "Cookie": f"SESSDATA={self.bilibili_cookie}",
            }
            
            logger.info(f"[Bilibili API] Fetching: {api_url}")
            logger.debug(f"[Bilibili API] Headers: {headers}")
            
            response = requests.get(api_url, headers=headers, timeout=10)
            logger.info(f"[Bilibili API] Response Status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[Bilibili API] Response Code: {data.get('code')}, Message: {data.get('message', 'N/A')}")
            logger.debug(f"[Bilibili API] Full Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")  # Log first 500 chars
            
            # Check API response
            if data.get("code") != 0:
                logger.warning(f"Bilibili API error for {self.account_name}: {data.get('message', 'Unknown error')}")
                return
            
            # Extract items from response
            items = data.get("data", {}).get("items", [])
            logger.info(f"[Bilibili API] Found {len(items)} items for {self.account_name}")
            
            if not items:
                logger.debug(f"No items found for {self.account_name}")
                return
            
            if is_live:
                self._process_bilibili_lives(items)
            else:
                self._process_bilibili_videos(items)
            
            # Save cache
            self._save_cache()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Bilibili API] Request error for {self.account_name}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"[Bilibili API] JSON decode error for {self.account_name}: {e}")
        except Exception as e:
            logger.error(f"[Bilibili API] Unexpected error for {self.account_name}: {e}", exc_info=True)

    def _process_bilibili_videos(self, items: list) -> None:
        """Process Bilibili API items to extract videos."""
        # Filter for video uploads only (pub_action == "投稿了视频")
        new_videos_found = False
        processed_count = 0
        
        for idx, item in enumerate(items):
            if processed_count >= self.auto_download_videos_count:
                break
            
            logger.debug(f"[Bilibili API] Processing video item {idx+1}/{len(items)}")
            
            # Check if this is a video upload item
            modules = item.get("modules", {})
            if not modules:
                logger.debug(f"[Bilibili API] Item {idx+1}: No modules found")
                continue
            
            # Get module_author to check pub_action
            module_author = modules.get("module_author", {})
            if not module_author:
                logger.debug(f"[Bilibili API] Item {idx+1}: No module_author found")
                continue
            
            # CRITICAL: Only process items with pub_action == "投稿了视频" (video upload)
            pub_action = module_author.get("pub_action", "")
            logger.debug(f"[Bilibili API] Item {idx+1}: pub_action = '{pub_action}'")
            
            if pub_action != "投稿了视频":
                logger.debug(f"[Bilibili API] Item {idx+1}: Skipping - not a video upload (pub_action: {pub_action})")
                continue
            
            # Get video info from module_dynamic.major.archive (NOT from module_author)
            module_dynamic = modules.get("module_dynamic", {})
            if not module_dynamic:
                logger.debug(f"[Bilibili API] Item {idx+1}: No module_dynamic found")
                continue
            
            major = module_dynamic.get("major", {})
            if not major or major.get("type") != "MAJOR_TYPE_ARCHIVE":
                logger.debug(f"[Bilibili API] Item {idx+1}: Not an archive type or missing major data")
                continue
            
            archive = major.get("archive", {})
            if not archive:
                logger.debug(f"[Bilibili API] Item {idx+1}: No archive data found")
                continue
            
            # Extract video info from archive
            video_id = archive.get("bvid", "")
            title = archive.get("title", "Unknown")
            video_jump_url = archive.get("jump_url", "")
            
            if not video_id or not video_jump_url:
                logger.debug(f"[Bilibili API] Item {idx+1}: Missing BVID or jump_url in archive")
                continue
            
            # Clean up video URL (remove leading //)
            if video_jump_url.startswith("//"):
                video_jump_url = "https:" + video_jump_url
            elif not video_jump_url.startswith("http"):
                video_jump_url = "https://" + video_jump_url
            
            logger.debug(f"[Bilibili API] Item {idx+1}: Found archive - BVID: {video_id}, Title: {title}, URL: {video_jump_url}")
            
            logger.info(f"[Bilibili API] Item {idx+1}: Found video upload - ID: {video_id}, Title: {title}")
            
            # Skip if we've already seen this
            if video_id in self._last_videos:
                logger.debug(f"[Bilibili API] Item {idx+1}: {video_id} already seen, skipping")
                continue
            
            # Skip if file already exists in destination folder
            if self._file_exists_in_destination(video_id):
                logger.info(f"[Bilibili API] File already exists in destination: {title}")
                self._last_videos[video_id] = title
                continue
            
            # Mark as seen and prepare to download
            self._last_videos[video_id] = title
            new_videos_found = True
            processed_count += 1
            
            logger.info(f"[Bilibili API] Found new video: {title} (ID: {video_id})")
            
            if self.on_video_found:
                self.on_video_found(
                    self.account_name,
                    video_id,
                    title,
                    False,  # Not live
                    video_jump_url,
                )
            
            # Automatically download
            if new_videos_found:
                logger.info(f"[Bilibili API] Starting download for: {title}")
                self._download_content(video_jump_url, title, is_live=False)
        
        logger.info(f"[Bilibili API] Completed video check for {self.account_name}, processed {processed_count} new videos")

    def _process_bilibili_lives(self, items: list) -> None:
        """Process Bilibili API items to extract live streams."""
        # Filter for live records (pub_action contains "直播" for lives)
        new_lives_found = False
        processed_count = 0
        
        for idx, item in enumerate(items):
            if processed_count >= self.auto_download_lives_count:
                break
            
            logger.debug(f"[Bilibili API] Processing live item {idx+1}/{len(items)}")
            
            # Check if this is a live record item
            modules = item.get("modules", {})
            if not modules:
                logger.debug(f"[Bilibili API] Live item {idx+1}: No modules found")
                continue
            
            # Get module_author to check pub_action
            module_author = modules.get("module_author", {})
            if not module_author:
                logger.debug(f"[Bilibili API] Live item {idx+1}: No module_author found")
                continue
            
            # Check for live-related actions
            pub_action = module_author.get("pub_action", "")
            logger.debug(f"[Bilibili API] Live item {idx+1}: pub_action = '{pub_action}'")
            
            # Live records typically have "直播" in the pub_action
            if "直播" not in pub_action:
                logger.debug(f"[Bilibili API] Live item {idx+1}: Skipping - not a live record (pub_action: {pub_action})")
                continue
            
            # Get live info from module_dynamic.major
            module_dynamic = modules.get("module_dynamic", {})
            if not module_dynamic:
                logger.debug(f"[Bilibili API] Live item {idx+1}: No module_dynamic found")
                continue
            
            major = module_dynamic.get("major", {})
            if not major:
                logger.debug(f"[Bilibili API] Live item {idx+1}: No major data found")
                continue
            
            # Extract live stream info
            major_type = major.get("type", "")
            live_id = None
            title = "Unknown"
            live_url = None
            
            # Different types of live content
            if major_type == "MAJOR_TYPE_LIVE_RCMD":
                live_detail = major.get("live_rcmd", {})
                live_id = live_detail.get("live_id", "")
                title = live_detail.get("title", "Unknown")
                live_url = live_detail.get("jump_url", "")
            elif major_type == "MAJOR_TYPE_ARCHIVE":
                # Some archives might be live records
                archive = major.get("archive", {})
                live_id = archive.get("bvid", "")
                title = archive.get("title", "Unknown")
                live_url = archive.get("jump_url", "")
            else:
                logger.debug(f"[Bilibili API] Live item {idx+1}: Unsupported major type: {major_type}")
                continue
            
            if not live_id or not live_url:
                logger.debug(f"[Bilibili API] Live item {idx+1}: Missing live ID or URL")
                continue
            
            # Clean up URL
            if live_url.startswith("//"):
                live_url = "https:" + live_url
            elif not live_url.startswith("http"):
                live_url = "https://" + live_url
            
            logger.debug(f"[Bilibili API] Live item {idx+1}: Found live - ID: {live_id}, Title: {title}, URL: {live_url}")
            
            # Skip if we've already seen this live
            if live_id in self._last_lives:
                logger.debug(f"[Bilibili API] Live item {idx+1}: {live_id} already seen, skipping")
                continue
            
            # Skip if file already exists in lives folder
            if self.lives_path and self._file_exists_in_lives(live_id):
                logger.info(f"[Bilibili API] Live file already exists in destination: {title}")
                self._last_lives[live_id] = title
                continue
            
            # Mark as seen and prepare to download
            self._last_lives[live_id] = title
            new_lives_found = True
            processed_count += 1
            
            logger.info(f"[Bilibili API] Found new live: {title} (ID: {live_id})")
            
            if self.on_video_found:
                self.on_video_found(
                    self.account_name,
                    live_id,
                    title,
                    True,  # Is live
                    live_url,
                )
            
            # Automatically download to lives folder
            if new_lives_found and self.lives_path:
                logger.info(f"[Bilibili API] Starting download for live: {title}")
                self._download_content(live_url, title, is_live=True)
        
        logger.info(f"[Bilibili API] Completed live check for {self.account_name}, processed {processed_count} new lives")

    def _download_content(self, video_url: str, title: str, is_live: bool = False) -> None:
        """Download video/stream content with quality fallback for premium content."""
        try:
            logger.info(f"Starting download: {title}")

            # Sanitize the title for use in filename (remove invalid Windows characters)
            sanitized_title = self._sanitize_filename(title)
            
            # Choose download path based on content type
            if is_live and self.lives_path:
                download_dir = self.lives_path
            else:
                download_dir = self.download_path
            
            # Detect if this is a Bilibili URL
            is_bilibili = "bilibili.com" in video_url or "b23.tv" in video_url

            # Define quality levels based on platform
            if is_bilibili:
                # Bilibili separates video and audio streams
                # Video IDs: 30011, 30016 (360p), 30033, 30032 (480p), 30066, 30064 (720p), 30077, 30080 (1080p)
                # Audio IDs: 30216, 30232, 30280 (different bitrates)
                # We need to download video + audio separately and merge
                quality_levels = [
                    "30080+30216",  # 1080p video + audio (best)
                    "30077+30216",  # 1080p hevc + audio
                    "30064+30216",  # 720p video + audio
                    "30066+30216",  # 720p hevc + audio
                    "30032+30216",  # 480p video + audio
                    "30033+30216",  # 480p hevc + audio
                    "30016+30216",  # 360p video + audio
                    "30011+30216",  # 360p hevc + audio
                    "30232",        # Audio only (fallback)
                    "best",         # Catch-all
                ]
            else:
                # YouTube format codes (format_id for different quality levels)
                quality_levels = [
                    "best[ext=mp4]",           # Best quality in MP4 format
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",  # Best video + best audio merged
                    "bestvideo+bestaudio/best",  # Best video + best audio (any format)
                    "best",                    # Catch-all best available
                ]

            last_error = None
            
            for quality_level_idx, format_str in enumerate(quality_levels):
                try:
                    logger.info(f"[Download] Attempting quality level {quality_level_idx}: {format_str}")
                    
                    ydl_opts = {
                        "format": format_str,
                        "outtmpl": str(
                            download_dir / f"{self.account_name}_{sanitized_title}_%(id)s.%(ext)s"
                        ),
                        "quiet": False,
                        "no_warnings": False,
                        "progress_hooks": [self._progress_hook],
                        "socket_timeout": 30,
                    }
                    
                    # Add postprocessors only for formats that actually need merging
                    # For YouTube: only add merger if format explicitly requests multiple streams (+ in format string)
                    # For Bilibili: always add merger since we use video+audio format codes
                    if is_bilibili:
                        ydl_opts["postprocessors"] = [
                            {
                                "key": "FFmpegMerger",
                            },
                        ]
                    elif "+" in format_str and format_str not in ["best", "best[ext=mp4]"]:
                        # Only add merger if format string contains + (multiple streams to merge)
                        # This applies to formats like "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
                        ydl_opts["postprocessors"] = [
                            {
                                "key": "FFmpegMerger",
                            },
                        ]
                    else:
                        # Single format streams don't need merging postprocessor
                        ydl_opts["postprocessors"] = []
                    
                    # Add Bilibili-specific options for download (web scraping)
                    if is_bilibili:
                        ydl_opts.update({
                            "http_headers": {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Referer": "https://search.bilibili.com/",
                            },
                            "retries": {"max_retries": 3, "backoff_factor": 1.5},
                            "cookies_from_browser": ("chrome", None),  # Extract cookies from Chrome browser for Bilibili authentication
                        })

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    
                    # Success! Download completed
                    logger.info(f"Completed download: {title} at quality level {quality_level_idx}")
                    if self.on_download_complete:
                        self.on_download_complete(self.account_name, title)
                    return
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    last_error = e
                    
                    # Check if error is because stream is scheduled/upcoming/offline
                    is_scheduled_error = any(keyword in error_msg for keyword in [
                        "scheduled",
                        "upcoming",
                        "stream is offline",
                        "has not started",
                        "no video formats",
                        "no video format found",
                        "not yet started",
                        "scheduled to start",
                    ])
                    
                    if is_scheduled_error:
                        logger.warning(f"[Download] Stream is scheduled/offline/upcoming, cannot download yet: {title}")
                        logger.debug(f"[Download] Error: {e}")
                        return  # Don't retry, just skip this stream
                    
                    # Check if error is premium/membership related
                    is_premium_error = any(keyword in error_msg for keyword in [
                        "premium",
                        "membership",
                        "vip",
                        "大会员",
                        "需要大会员",
                        "requires",
                        "high quality",
                        "permission denied",
                        "access denied",
                        "不可用",
                        "无权限",
                        "missing",
                        "are missing",
                    ])
                    
                    
                    # Check if error is format not available (video format mismatch)
                    is_format_unavailable = any(keyword in error_msg for keyword in [
                        "format is not available",
                        "requested format is not available",
                        "no video format found",
                        "video format not found",
                        "not available in any format",
                    ])
                    
                    # Retry with next quality level if premium/format error and more levels available
                    if is_bilibili and (is_premium_error or is_format_unavailable) and quality_level_idx < len(quality_levels) - 1:
                        if is_premium_error:
                            logger.warning(f"[Download] Quality level {quality_level_idx} requires premium membership")
                        if is_format_unavailable:
                            logger.warning(f"[Download] Quality level {quality_level_idx} format not available for this video")
                        logger.warning(f"[Download] Error: {e}")
                        logger.info(f"[Download] Downgrading quality and retrying...")
                        continue  # Try next quality level
                    else:
                        # Not a premium error, or no more quality levels to try
                        logger.error(f"[Download] Failed at quality level {quality_level_idx}: {e}")
                        if quality_level_idx < len(quality_levels) - 1:
                            logger.info(f"[Download] Retrying with lower quality...")
                            continue
                        else:
                            # This was the last quality level
                            raise
            
            # Should not reach here, but just in case
            raise last_error if last_error else Exception("Download failed for unknown reason")

        except Exception as e:
            logger.error(f"Error downloading {title}: {e}", exc_info=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing or replacing invalid Windows characters."""
        import re
        # Invalid Windows filename characters: < > : " / \ | ? *
        # Also include lookalike characters that cause issues (division slash, etc.)
        invalid_chars = r'[<>:"/\\|?*\u00F7\u29F8\u2215\u3002]'
        sanitized = re.sub(invalid_chars, '_', filename)
        # Also remove control characters
        sanitized = ''.join(c for c in sanitized if ord(c) >= 32)
        # Limit filename length (Windows has 255 char limit, be conservative)
        # Account for account_name prefix and video ID suffix
        max_length = 80
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized.strip()

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
        check_interval: int = 300,
        auto_download_count: int = 1,
        bilibili_cookie: str = "",
        auto_download_videos: bool = True,
        auto_download_lives: bool = False,
        auto_download_videos_count: int = 1,
        auto_download_lives_count: int = 1,
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
                check_interval=check_interval,
                auto_download_count=auto_download_count,
                bilibili_cookie=bilibili_cookie,
                auto_download_videos=auto_download_videos,
                auto_download_lives=auto_download_lives,
                auto_download_videos_count=auto_download_videos_count,
                auto_download_lives_count=auto_download_lives_count,
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

    def clear_cache(self, account_name: str) -> bool:
        """Clear cache for a specific account."""
        listener = self.get_listener(account_name)
        if listener:
            return listener.clear_cache()
        return False

    def clear_all_caches(self) -> bool:
        """Clear cache for all listeners."""
        try:
            with self._lock:
                for listener in self._listeners.values():
                    try:
                        listener.clear_cache()
                    except Exception as e:
                        logger.error(f"Error clearing cache for {listener.account_name}: {e}")
            logger.info("Cleared all listener caches")
            return True
        except Exception as e:
            logger.error(f"Error clearing all caches: {e}")
            return False

