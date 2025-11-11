"""
Convert DLBot.jpg to DLBot.ico for use in PyInstaller build
Run this script before running build_exe.py
"""

from PIL import Image
from pathlib import Path
import sys

def create_icon():
    """Convert DLBot.jpg to DLBot.ico"""
    
    jpg_path = Path("DLBot.jpg")
    ico_path = Path("DLBot.ico")
    
    if not jpg_path.exists():
        print(f"Error: {jpg_path} not found!")
        sys.exit(1)
    
    try:
        print(f"Converting {jpg_path} to {ico_path}...")
        
        # Open the image
        img = Image.open(jpg_path)
        
        # Convert to RGB if needed (ICO doesn't support RGBA)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to standard icon size (256x256)
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        
        # Save as ICO
        img.save(ico_path, format='ICO')
        
        print(f"✓ Icon created successfully: {ico_path}")
        print(f"✓ File size: {ico_path.stat().st_size / 1024:.1f} KB")
        
    except ImportError:
        print("Error: Pillow (PIL) not installed!")
        print("Install it with: pip install Pillow")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting image: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_icon()
