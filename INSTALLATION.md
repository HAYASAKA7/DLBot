# Installation & Setup Guide

## System Requirements

- **OS**: Windows 7 or later (Windows 10/11 recommended)
- **Python**: 3.8 or later (3.10+ recommended)
- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk Space**: 1GB total (including dependencies)
- **Internet**: Required for account monitoring

## Pre-Installation Checklist

- [ ] Windows system is up to date
- [ ] You have administrator access to your computer
- [ ] At least 1GB of free disk space
- [ ] Internet connection is stable

## Installation Methods

### Method 1: Automated Setup (Recommended)

This is the easiest way to get started!

#### Requirements
- Python must be installed and in PATH

#### Steps

1. **Extract DLBot**
   - Extract the DLBot folder to your desired location
   - Example: `C:\Users\YourName\Documents\DLBot`

2. **Run Setup**
   - Navigate to the DLBot folder
   - Double-click `setup.bat`
   - Wait for the installation to complete
   - You should see "Setup Completed Successfully!"

3. **Start Application**
   - Double-click `run.bat`
   - DLBot window should open

### Method 2: Manual Setup

For advanced users or if automated setup fails:

#### Prerequisites
- Python 3.8+ installed
- pip package manager

#### Steps

1. **Open Command Prompt/PowerShell**
   - Navigate to DLBot folder
   - ```powershell
     cd C:\Path\To\DLBot
     ```

2. **Create Virtual Environment**
   ```powershell
   python -m venv venv
   ```

3. **Activate Virtual Environment**
   - On PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - On Command Prompt:
     ```cmd
     venv\Scripts\activate.bat
     ```

4. **Upgrade pip**
   ```powershell
   python -m pip install --upgrade pip
   ```

5. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

6. **Create Directories**
   ```powershell
   mkdir config downloads logs
   ```

7. **Run Application**
   ```powershell
   python main.py
   ```

### Method 3: Docker (Advanced)

If you want to run DLBot in Docker:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## Python Installation

If Python is not installed:

### Windows 10/11

1. Open Microsoft Store
2. Search for "Python"
3. Click Python 3.11 (or latest)
4. Click "Install"
5. Wait for installation to complete

### Manual Installation

1. Visit https://www.python.org/downloads/
2. Click "Download Python 3.11" (or latest)
3. Run the installer
4. **IMPORTANT**: Check ✓ "Add Python to PATH"
5. Click "Install Now"
6. Restart your computer

### Verify Python Installation

Open Command Prompt and run:
```powershell
python --version
```

Should show: `Python 3.x.x`

## Troubleshooting Installation

### "Python is not installed or not in PATH"

**Solution 1**: Reinstall Python with PATH option
1. Uninstall Python from Control Panel
2. Download Python installer from python.org
3. Run installer
4. **Check** "Add Python to PATH"
5. Complete installation
6. Restart computer

**Solution 2**: Add Python to PATH manually
1. Install Python normally
2. Right-click "This PC" → Properties
3. Click "Advanced system settings"
4. Click "Environment Variables"
5. Under System variables, click "New"
6. Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python310`
7. Click OK, OK, OK
8. Restart computer

### "Failed to create virtual environment"

**Causes**: Permission issues, disk space, or antivirus blocking

**Solutions**:
- Run Command Prompt as Administrator
- Check free disk space (at least 500MB needed)
- Disable antivirus temporarily during setup
- Try alternate location with more permissions

### "Module not found" or "Import error"

**Solution**:
1. Ensure virtual environment is activated
2. Verify all packages installed: `pip list`
3. Reinstall packages: `pip install -r requirements.txt --force-reinstall`

### "Permission denied" errors

**Solution**:
- Run setup.bat as Administrator
- Check folder permissions
- Ensure you own the DLBot folder

## Dependency Verification

After installation, verify all dependencies:

```powershell
# Activate virtual environment first
venv\Scripts\activate

# Check packages
pip list
```

You should see:
- yt-dlp (>=2023.12.30)
- PyQt5 (>=5.15.9)
- requests (>=2.31.0)

### Updating Dependencies

To update to latest versions:
```powershell
pip install -U yt-dlp PyQt5 requests
```

## File Structure After Installation

```
DLBot/
├── venv/                          # Python virtual environment
│   ├── Scripts/
│   ├── Lib/
│   └── pyvenv.cfg
├── config/
│   └── config.json               # Application configuration
├── downloads/                     # Default download location
├── logs/                         # Application logs
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── listener.py          # Core listener logic
│   │   └── app_controller.py    # App orchestration
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py       # Main GUI window
│   │   └── settings_dialog.py   # Settings dialogs
│   └── utils/
│       ├── __init__.py
│       └── config.py            # Configuration management
├── main.py                       # Entry point
├── setup.bat                    # Setup script
├── run.bat                      # Run script
├── requirements.txt             # Dependencies
├── README.md                    # Full documentation
├── QUICKSTART.md               # Quick start guide
├── DEVELOPER.md                # Developer documentation
└── INSTALLATION.md             # This file
```

## First Launch

When you run DLBot for the first time:

1. Application starts with empty account list
2. `config/config.json` is created with default settings
3. `logs/` directory is created
4. No downloads happen until you add accounts

## Next Steps

1. **Read QUICKSTART.md** for 5-minute setup guide
2. **Add your first account** (YouTube or Bilibili)
3. **Start listening** and watch videos download!

## Uninstallation

To completely remove DLBot:

1. Delete the DLBot folder
2. That's it! No registry changes or residual files

To only reset configuration:
- Delete `config/config.json`
- Application will recreate default config on next launch

## Getting Help

If you encounter issues:

1. **Check logs**: Look in `logs/dlbot.log`
2. **Read documentation**: Check README.md and DEVELOPER.md
3. **Try troubleshooting**: See sections above
4. **Reinstall**: Run setup.bat again

## System Administration

### Running as Administrator

Some users may need to run DLBot as Administrator:

**Method 1: One-time**
- Right-click `run.bat` → Run as Administrator

**Method 2: Always**
1. Right-click `run.bat` → Properties
2. Click Advanced
3. Check "Run as an administrator"
4. Click OK

### Firewall Configuration

If DLBot can't access accounts:

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Click "Change settings"
4. Find Python in the list
5. Check boxes for both Private and Public
6. Click OK

### Antivirus Configuration

If setup fails or DLBot won't run:

1. Add DLBot folder to antivirus whitelist
2. Disable antivirus during setup (temporarily)
3. Check quarantine for blocked files

## Performance Tips

### For Slower Systems

- Increase check interval to 600+ seconds
- Reduce number of monitored accounts
- Close other applications while DLBot runs

### For Better Performance

- SSD installation location
- More RAM allocated
- Latest Python version
- Current yt-dlp version

## Keeping DLBot Updated

### Update Dependencies

```powershell
# Activate virtual environment
venv\Scripts\activate

# Update all packages
pip install -U -r requirements.txt
```

### Update DLBot

When new versions are available:
1. Backup `config/config.json`
2. Download new DLBot version
3. Replace files (keep config folder)
4. Run setup.bat to update dependencies

## Advanced Configuration

### Startup Parameters

You can add command-line arguments to `run.bat`:

```bat
@echo off
call venv\Scripts\activate.bat
python main.py --headless      # Start without GUI
python main.py --config custom.json  # Custom config path
```

### Environment Variables

Set environment variables for advanced use:

```powershell
$env:DLBOT_CONFIG = "D:\MyConfig\config.json"
$env:DLBOT_DOWNLOADS = "D:\MyDownloads"
python main.py
```

## System Compatibility

### Windows 7/8
- Python 3.10.x max (3.11+ dropped support)
- Otherwise fully compatible

### Windows 10
- Fully compatible with Python 3.8+
- Recommended Python 3.10 or 3.11

### Windows 11
- Fully compatible with Python 3.10+
- Recommended Python 3.11 or newer

### Windows Server
- Tested on Windows Server 2019+
- May need headless mode (see Advanced Configuration)

## License & Support

DLBot is provided free for personal use.

For issues, consult the documentation or check the code in `src/`.

---

Last Updated: November 10, 2025
Happy downloading! 🎉
