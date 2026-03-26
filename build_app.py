#!/usr/bin/env python3
"""
Build REVA as Standalone Executable
Creates: REVA.exe (Windows), REVA.app (macOS), REVA (Linux)
"""
import os
import subprocess
import sys
import shutil
import platform

def clean_build():
    """Clean previous builds"""
    print("🧹 Cleaning old builds...")
    for folder in ["build", "dist", "__pycache__", ".pyinstaller"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    print("✅ Cleaned\n")

def build_app():
    """Build executable using PyInstaller"""
    print("🔨 Building REVA App...\n")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=REVA",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=requests",
        "--hidden-import=pyautogui",
        "--collect-all=PyQt5",
        "desktop_app.py"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Build failed:")
        print(result.stderr)
        return False
    
    print("✅ Build successful!\n")
    return True

def check_output():
    """Check build output"""
    system = platform.system()
    
    if system == "Windows":
        exe = "dist/REVA.exe"
        if os.path.exists(exe):
            size = os.path.getsize(exe) / (1024*1024)
            print(f"📦 Windows App: {exe} ({size:.1f}MB)")
            return True
    elif system == "Darwin":
        app = "dist/REVA.app"
        if os.path.exists(app):
            print(f"📦 macOS App: {app}")
            return True
    else:
        exe = "dist/REVA"
        if os.path.exists(exe):
            size = os.path.getsize(exe) / (1024*1024)
            print(f"📦 Linux App: {exe} ({size:.1f}MB)")
            return True
    
    return False

def main():
    """Main build process"""
    print("╔════════════════════════════════════════════╗")
    print("║     REVA - Building Standalone App         ║")
    print("╚════════════════════════════════════════════╝\n")
    
    system = platform.system()
    print(f"Platform: {system}\n")
    
    # Clean
    clean_build()
    
    # Build
    if not build_app():
        sys.exit(1)
    
    # Check
    if check_output():
        print("\n✅ APP READY FOR DOWNLOAD!\n")
        print("Next steps:")
        print("1. Upload to web server")
        print("2. Create download page")
        print("3. Share link with users")
        print("\nUsers can then:")
        print("• Click download")
        print("• Run the app")
        print("• No Python needed!")
    else:
        print("❌ Build output not found")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
