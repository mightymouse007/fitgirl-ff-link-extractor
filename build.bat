@echo off
echo ==========================================
echo  FuckingFast Extractor - EXE Builder
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install pyinstaller curl_cffi beautifulsoup4

echo.
echo [2/4] Building standalone EXE...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "FuckingFast_Extractor" ^
    --icon NONE ^
    --clean ^
    --hidden-import curl_cffi ^
    --hidden-import curl_cffi.requests ^
    --hidden-import _cffi_backend ^
    --collect-all curl_cffi ^
    gui_app.py

echo.
echo [3/4] Cleaning up build files...
if exist build rmdir /s /q build
if exist "FuckingFast_Extractor.spec" del "FuckingFast_Extractor.spec"

echo.
echo [4/4] Done! Your EXE is here:
echo     dist\FuckingFast_Extractor.exe
echo.
pause
