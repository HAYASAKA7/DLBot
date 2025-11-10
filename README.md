# DLBot - Content Listener & Downloader

A powerful Windows application that automatically monitors YouTube and Bilibili accounts for new videos and live streams, then downloads them automatically.

## Features

✅ **Multi-Platform Support**

- Monitor YouTube channels and users
- Monitor Bilibili channels and users
- Support for both videos and live streams

✅ **Automatic Downloading**

- Automatically detects new content
- Downloads videos/streams using yt-dlp
- Customizable check intervals
- Supports high-quality downloads

✅ **Individual Account Management**

- Separate listener thread for each account
- Enable/disable accounts individually
- Custom download paths per account
- Independent control for each account

✅ **User-Friendly GUI**

- Modern PyQt5 interface
- Real-time status indicators
- Account management interface
- Settings panel
- System tray integration

✅ **Smart Background Operation**

- Minimize to system tray
- Run in background
- Close to tray or quit
- Auto-start option

✅ **Easy Setup**

- One-click setup with setup.bat
- Automatic dependency installation
- Package verification
- Virtual environment support

## Installation

### Quick Start (Recommended)

1. **Download the project** and extract it to your desired location
2. **Run `setup.bat`** - This will:
   - Check Python installation
   - Create a virtual environment
   - Install all dependencies
   - Create necessary directories

3. **Run the application** using `run.bat` or `python main.py`

### Manual Installation

If you prefer to set up manually:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### First Launch

1. Open DLBot
2. Click **Settings** to configure
3. Click **Add Account** in the Accounts tab
4. Enter account details:
   - **Account Name**: Name for your reference (e.g., "PewDiePie")
   - **Platform**: Select YouTube or Bilibili
   - **Account URL**: Full URL to the channel/user
   - **Download Path**: Where to save videos
   - Click **OK** to save

### Managing Accounts

- **Start Listening**: Click "Start" button next to an account
- **Stop Listening**: Click "Stop" button while listening
- **Edit Account**: Click "Edit" to modify settings
- **Remove Account**: Select account and click "Remove"

### Application Settings

**Storage Tab**

- Set default download location
- Adjust check interval (60-3600 seconds)
- Enable/disable auto-download

**General Tab**

- Choose theme (Light/Dark)
- Minimize to tray instead of closing
- Start minimized on launch

### Status Indicators

- **● Green Circle**: Account is actively listening
- **○ Gray Circle**: Account is idle/stopped

## Project Structure

```
DLBot/
├── config/                 # Configuration files
│   └── config.json        # Main configuration (auto-created)
├── downloads/             # Downloaded videos (default)
├── logs/                  # Application logs
├── src/
│   ├── core/
│   │   ├── listener.py   # Content listener logic
│   │   └── app_controller.py  # App orchestration
│   ├── gui/
│   │   ├── main_window.py     # Main GUI window
│   │   └── settings_dialog.py # Settings dialogs
│   └── utils/
│       └── config.py     # Configuration management
├── main.py               # Application entry point
├── setup.bat             # Setup script
├── run.bat              # Application launcher
└── requirements.txt     # Python dependencies
```

## Configuration

Configuration is stored in `config/config.json`. You can edit it directly, but it's easier to use the GUI Settings panel.

### Example config.json

```json
{
  "accounts": [
    {
      "name": "YUNO",
      "url": "https://www.youtube.com/c/yuno_yumemita",
      "platform": "youtube",
      "download_path": "D:/Videos/YUNO",
      "enabled": true,
      "check_interval": 300
    }
  ],
  "default_download_path": "D:/Videos",
  "check_interval": 300,
  "auto_download": true,
  "minimize_to_tray": true,
  "start_minimized": false,
  "theme": "light"
}
```

## How It Works

1. **Listener Thread**: Each account has a dedicated listener thread
2. **Periodic Checks**: Every 5 minutes (or configured interval), the listener checks for new content
3. **Content Detection**: Uses yt-dlp to fetch account information and detect new videos/streams
4. **Automatic Download**: When new content is found, it's automatically downloaded to the specified directory
5. **Status Updates**: GUI updates show listening status with visual indicators

## Supported URLs

### YouTube

- Channel: `https://www.youtube.com/c/ChannelName`
- User: `https://www.youtube.com/user/UserName`
- Custom URL: `https://www.youtube.com/@CustomName`
- Handle: `https://www.youtube.com/@Handle`

### Bilibili

- User Space: `https://space.bilibili.com/123456789`
- Channel: `https://www.bilibili.com/v/channel/MCxxxxxx`

## Troubleshooting

### Application won't start

**Error: "Python is not installed"**

- Install Python from <https://www.python.org/>
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after installation

**Error: "Failed to create virtual environment"**

- Make sure you have write permissions in the DLBot directory
- Try running setup.bat as Administrator

### Dependencies installation fails

**Error during pip install**

- Check your internet connection
- Try running setup.bat as Administrator
- Check Windows Firewall settings

### No downloads happening

- Verify the URL format is correct
- Check the download path has write permissions
- Increase verbosity in logs (check `logs/dlbot.log`)
- Ensure yt-dlp is up to date

### Can't connect to YouTube/Bilibili

- Check your internet connection
- The account URL might be invalid or private
- yt-dlp might need updating: `pip install -U yt-dlp`

## System Requirements

- **OS**: Windows 7 or later
- **Python**: 3.8 or later
- **RAM**: Minimum 256MB
- **Storage**: 500MB for Python + dependencies + videos
- **Internet**: Required for monitoring accounts

## Dependencies

- **yt-dlp**: Video downloading
- **PyQt5**: GUI framework
- **requests**: HTTP library (for future enhancements)

## Keyboard Shortcuts

- `Ctrl+Q`: Quit application
- `Ctrl+S`: Open Settings
- `F5`: Refresh account list

## Tips & Tricks

1. **Multiple Accounts**: Create separate entries for different creators
2. **Custom Paths**: Use different download paths for different content types
3. **Check Interval**: Lower values = more frequent checks but more CPU/network usage
4. **Backup**: Regularly backup your `config/config.json` file
5. **Auto-Start**: Use Windows Task Scheduler to run DLBot at startup

## Known Limitations

- YouTube/Bilibili may rate-limit frequent requests
- Very large video files may take time to download
- Some live streams may not be downloadable if ended

## Future Features (Planned)

- [ ] Notification system
- [ ] Video quality/format selection
- [ ] Download queue management
- [ ] Statistics and history
- [ ] Email notifications
- [ ] Discord integration
- [ ] Proxy support
- [ ] Multi-language support

## License

This project is provided as-is for personal use.

## Support

For issues or questions:

1. Check `logs/dlbot.log` for error details
2. Verify all account URLs are correct
3. Try updating dependencies: `pip install -U yt-dlp PyQt5`

## Contributing

Feel free to fork and modify this project for your needs!

## Disclaimer

This tool is for personal, non-commercial use only. Always respect content creators' rights and platform terms of service.
