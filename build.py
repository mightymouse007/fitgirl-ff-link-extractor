#!/usr/bin/env python3
"""
Build script for FuckingFast Extractor
Run this to create the standalone executable.
"""
import subprocess
import sys
import shutil
import os

def main():
    print("=" * 50)
    print(" FuckingFast Extractor - EXE Builder")
    print("=" * 50)
    print()

    # Install dependencies
    print("[1/4] Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "pyinstaller", "curl_cffi", "beautifulsoup4"])

    # Build
    print()
    print("[2/4] Building standalone EXE...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "FuckingFast_Extractor",
        "--icon", "NONE",
        "--clean",
        "--hidden-import", "curl_cffi",
        "--hidden-import", "curl_cffi.requests",
        "--hidden-import", "_cffi_backend",
        "--collect-all", "curl_cffi",
        "gui_app.py"
    ]
    subprocess.check_call(cmd)

    # Cleanup
    print()
    print("[3/4] Cleaning up...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("FuckingFast_Extractor.spec"):
        os.remove("FuckingFast_Extractor.spec")

    print()
    print("[4/4] Done!")
    print(f"    Your EXE is at: dist{os.sep}FuckingFast_Extractor.exe")
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
