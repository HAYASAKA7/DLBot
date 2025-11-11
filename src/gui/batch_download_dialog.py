"""
Batch download dialog for DLBot application.
Allows users to add multiple video URLs and download them in batch.
"""

import logging
import re
from typing import List, Optional, Callable
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """Worker thread for batch downloading videos."""
    
    progress = pyqtSignal(int)  # Current progress
    status = pyqtSignal(str)  # Status message
    finished = pyqtSignal(bool, int, int)  # (success, successful_count, failed_count)
    
    def __init__(self, urls: List[str], download_callback: Callable):
        """
        Initialize download worker.
        
        Args:
            urls: List of video URLs to download
            download_callback: Callback function that handles individual URL download
        """
        super().__init__()
        self.urls = urls
        self.download_callback = download_callback
        self.is_running = True
    
    def run(self) -> None:
        """Run download in background thread."""
        successful = 0
        failed = 0
        
        try:
            total = len(self.urls)
            
            for index, url in enumerate(self.urls):
                if not self.is_running:
                    break
                
                self.status.emit(f"Downloading [{index + 1}/{total}]: {url}")
                
                try:
                    # Call the download callback for each URL
                    result = self.download_callback(url)
                    
                    if result:
                        successful += 1
                        self.status.emit(f"✓ Downloaded [{index + 1}/{total}]: {url}")
                    else:
                        failed += 1
                        self.status.emit(f"✗ Failed [{index + 1}/{total}]: {url}")
                    
                    self.progress.emit((index + 1) * 100 // total)
                except Exception as e:
                    failed += 1
                    logger.error(f"Error downloading {url}: {e}")
                    self.status.emit(f"✗ Error [{index + 1}/{total}]: {url} - {str(e)}")
            
            # Only report success if all downloads succeeded
            success = failed == 0
            self.finished.emit(success, successful, failed)
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            self.status.emit(f"Download failed: {str(e)}")
            self.finished.emit(False, successful, failed)
    
    def stop(self) -> None:
        """Stop the download worker."""
        self.is_running = False


class BatchDownloadDialog(QDialog):
    """Dialog for batch downloading videos."""
    
    def __init__(self, app_controller, parent=None):
        """
        Initialize batch download dialog.
        
        Args:
            app_controller: Application controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.download_urls: List[str] = []
        self.download_worker: Optional[DownloadWorker] = None
        self.is_downloading = False
        self.successful_downloads = 0
        self.failed_downloads = 0
        
        self.setWindowTitle("Batch Download Videos")
        self.setGeometry(200, 200, 700, 600)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Batch Download Videos")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Input section
        input_label = QLabel("Paste video URLs below (one per line):")
        layout.addWidget(input_label)
        
        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(
            "Paste video URLs here, one per line.\n"
            "Supported: YouTube, Bilibili, and other yt-dlp supported sites"
        )
        self.url_input.setMaximumHeight(120)
        layout.addWidget(self.url_input)
        
        # Add button
        add_btn = QPushButton("Add to List")
        add_btn.clicked.connect(self._on_add_urls)
        layout.addWidget(add_btn)
        
        # URL list section
        list_label = QLabel("URLs to Download:")
        list_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)
        
        self.url_list = QListWidget()
        self.url_list.setMinimumHeight(200)
        layout.addWidget(self.url_list)
        
        # List control buttons
        list_button_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._on_remove_url)
        list_button_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_list)
        list_button_layout.addWidget(clear_btn)
        
        list_button_layout.addStretch()
        layout.addLayout(list_button_layout)
        
        # Download path section
        path_label = QLabel("Download to:")
        path_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QPlainTextEdit()
        self.path_input.setMaximumHeight(40)
        
        # Set default download path
        config = self.app_controller.config_manager.get_config()
        if config.default_download_path:
            default_path = config.default_download_path
        else:
            default_path = str(Path("downloads"))
        
        self.path_input.setPlainText(default_path)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self._on_download)
        self.download_btn.setMinimumWidth(100)
        button_layout.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("Cancel Download")
        self.cancel_btn.clicked.connect(self._on_cancel_download)
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_add_urls(self) -> None:
        """Add URLs from input text to the list."""
        text = self.url_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "No URLs", "Please paste at least one URL.")
            return
        
        # Split by newlines and filter out empty lines
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        
        # Add valid URLs to the list
        added_count = 0
        for url in urls:
            if self._is_valid_url(url):
                self.download_urls.append(url)
                item = QListWidgetItem(url)
                self.url_list.addItem(item)
                added_count += 1
            else:
                logger.warning(f"Invalid URL format: {url}")
        
        if added_count > 0:
            self.url_input.clear()
            QMessageBox.information(
                self,
                "URLs Added",
                f"Added {added_count} URL(s) to the list.\n"
                f"Total URLs: {len(self.download_urls)}"
            )
        else:
            QMessageBox.warning(
                self,
                "No Valid URLs",
                "No valid URLs found in the input."
            )
    
    def _on_remove_url(self) -> None:
        """Remove selected URL from the list."""
        current_row = self.url_list.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a URL to remove.")
            return
        
        self.url_list.takeItem(current_row)
        self.download_urls.pop(current_row)
    
    def _on_clear_list(self) -> None:
        """Clear all URLs from the list."""
        if not self.download_urls:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All",
            f"Remove all {len(self.download_urls)} URL(s) from the list?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.url_list.clear()
            self.download_urls.clear()
    
    def _on_browse_path(self) -> None:
        """Browse for download directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            self.path_input.toPlainText()
        )
        
        if path:
            self.path_input.setPlainText(path)
    
    def _on_download(self) -> None:
        """Start batch download."""
        if not self.download_urls:
            QMessageBox.warning(
                self,
                "No URLs",
                "Please add at least one URL to the list before downloading."
            )
            return
        
        download_path = self.path_input.toPlainText().strip()
        
        if not download_path:
            QMessageBox.warning(
                self,
                "No Path",
                "Please specify a download directory."
            )
            return
        
        # Create download directory if it doesn't exist
        try:
            Path(download_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Invalid Path",
                f"Cannot create download directory:\n{str(e)}"
            )
            return
        
        # Confirm download
        reply = QMessageBox.question(
            self,
            "Confirm Download",
            f"Download {len(self.download_urls)} video(s)?\n"
            f"Download to: {download_path}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start download
        self._start_batch_download(download_path)
    
    def _start_batch_download(self, download_path: str) -> None:
        """Start batch download in background thread."""
        self.is_downloading = True
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create worker thread
        def download_callback(url: str) -> bool:
            """Callback to download a single URL. Returns True if successful."""
            return self.app_controller.download_url(url, download_path)
        
        self.download_worker = DownloadWorker(self.download_urls, download_callback)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.status.connect(self._on_download_status)
        self.download_worker.finished.connect(self._on_download_finished)
        
        self.download_worker.start()
    
    def _on_download_progress(self, value: int) -> None:
        """Update download progress."""
        self.progress_bar.setValue(value)
    
    def _on_download_status(self, status: str) -> None:
        """Update download status."""
        self.status_label.setText(status)
        logger.info(status)
    
    def _on_download_finished(self, success: bool, successful_count: int, failed_count: int) -> None:
        """Handle download completion."""
        self.is_downloading = False
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        total = successful_count + failed_count
        
        if success:
            # All downloads succeeded
            QMessageBox.information(
                self,
                "Download Complete",
                f"✓ Successfully downloaded all {total} video(s)!"
            )
            # Clear the list after successful download
            self.url_list.clear()
            self.download_urls.clear()
            self.url_input.clear()
        elif successful_count > 0:
            # Some downloads succeeded
            QMessageBox.warning(
                self,
                "Partial Download",
                f"⚠ Downloaded {successful_count}/{total} video(s).\n"
                f"✗ Failed: {failed_count} video(s)\n\n"
                f"Check logs for error details."
            )
        else:
            # All downloads failed
            QMessageBox.critical(
                self,
                "Download Failed",
                f"✗ Failed to download all {total} video(s).\n\n"
                f"Check logs for error details:\n"
                f"logs/dlbot.log"
            )
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
    
    def _on_cancel_download(self) -> None:
        """Cancel the ongoing download."""
        if self.download_worker and self.is_downloading:
            reply = QMessageBox.question(
                self,
                "Cancel Download",
                "Are you sure you want to cancel the download?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.download_worker.stop()
                self.status_label.setText("Download cancelled by user")
                self.is_downloading = False
                self.download_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)
                self.progress_bar.setVisible(False)
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validate if a string is a valid URL.
        
        Args:
            url: String to validate
            
        Returns:
            True if URL appears valid, False otherwise
        """
        # Simple URL validation - check for common patterns
        url_pattern = re.compile(
            r'https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        if self.is_downloading and self.download_worker:
            reply = QMessageBox.question(
                self,
                "Stop Download?",
                "Download is in progress. Stop and close?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.download_worker.stop()
                self.download_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
