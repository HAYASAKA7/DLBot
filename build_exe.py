"""
Build script to create DLBot.exe using PyInstaller
Run this script from the project root directory:
    python build_exe.py
"""

import os
import sys
import subprocess
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    main_script = project_root / "main.py"
    
    # Ensure main.py exists
    if not main_script.exists():
        print(f"Error: {main_script} not found!")
        sys.exit(1)
    
    # PyInstaller command with optimizations
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=DLBot",
        "--onefile",  # Bundle into single executable
        "--windowed",  # No console window (GUI only)
        "--icon=DLBot.ico" if Path("DLBot.ico").exists() else "",
        "--add-data=config:config",  # Include config directory
        "--add-data=DLBot.jpg:.",  # Include icon image for window and tray
        "--hidden-import=yt_dlp",
        "--hidden-import=PyQt5",
        "--collect-all=yt_dlp",
        "--collect-all=PyQt5",
        "--distpath=dist",
        "--workpath=build",  # Changed from --buildpath to --workpath
        "--specpath=.",
        str(main_script),
    ]
    
    # Remove empty strings from command
    pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if cmd]
    
    print("=" * 60)
    print("DLBot - Building Executable")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Main script: {main_script}")
    print(f"\nRunning PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")
    print("=" * 60)
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(pyinstaller_cmd, cwd=project_root)
        
        if result.returncode == 0:
            exe_path = project_root / "dist" / "DLBot.exe"
            print()
            print("=" * 60)
            print("✓ Build completed successfully!")
            print("=" * 60)
            print(f"Executable location: {exe_path}")
            print()
            print("To run the application:")
            print(f"  {exe_path}")
            print()
            return True
        else:
            print()
            print("=" * 60)
            print("✗ Build failed!")
            print("=" * 60)
            return False
            
    except FileNotFoundError:
        print()
        print("=" * 60)
        print("✗ PyInstaller not found!")
        print("=" * 60)
        print("\nPlease install PyInstaller first:")
        print("  pip install pyinstaller")
        print()
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error during build: {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
