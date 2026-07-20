# FuckingFast Direct Link Extractor - GUI Edition

## What is this?
A standalone Windows GUI app that extracts direct `/dl/` download links from fuckingfast.co landing pages.

## Features
- **Copy-paste ANY text** — paste messy chat logs, HTML, raw URLs, whatever. The app auto-finds all fuckingfast links.
- **One-click extract** — hit the button and watch it work through all links with a progress bar.
- **Copy or Save** — copy results to clipboard or save to a `.txt` file for your download manager.
- **No command line needed** — fully graphical, dark-themed UI.

## How to Build the EXE

### Option 1: Double-click (Windows)
1. Make sure Python 3.9+ is installed
2. Double-click `build.bat`
3. Wait ~2 minutes
4. Your `FuckingFast_Extractor.exe` will be in the `dist/` folder

### Option 2: Command Line
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name "FuckingFast_Extractor" gui_app.py
```

## How to Use
1. **Paste** your messy text into the top box (can contain URLs anywhere)
2. Click **"EXTRACT DIRECT LINKS"**
3. Wait for the progress bar to finish
4. **Copy** to clipboard or **Save** to file
5. Paste into IDM, aria2c, wget, or any download manager

## Example Input
You can paste something like this and it will find all links:
```
Hey check these out:
https://fuckingfast.co/abc123#game.part1.rar
Also: https://fuckingfast.co/xyz789#patch.zip
And maybe some other text here...
```

## System Requirements
- Windows 10/11 (64-bit)
- ~50MB disk space for the EXE
- Internet connection
