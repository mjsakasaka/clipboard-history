@echo off
chcp 65001 >nul
echo ========================================
echo  Clipboard History — Build
echo ========================================
echo.

:: Clean previous build
if exist dist\ rmdir /s /q dist
if exist build\ rmdir /s /q build
if exist *.spec del /q *.spec

echo [1/4] Installing dependencies...
pip install -r requirements.txt --quiet

echo [2/4] Building with PyInstaller...
pyinstaller ^
    --onedir ^
    --windowed ^
    --name "ClipboardHistory" ^
    --add-data "assets/icon.png;assets" ^
    --hidden-import win32clipboard ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import PIL._imaging ^
    --clean ^
    src/main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAIL] PyInstaller build failed!
    pause
    exit /b 1
)

echo [3/4] Preparing distributable folder...
:: Create data directories inside the output folder
mkdir "dist\ClipboardHistory\data\images" 2>nul

echo [4/4] Creating release zip...
:: Create zip for GitHub Release
powershell -Command "Compress-Archive -Path 'dist\ClipboardHistory\*' -DestinationPath 'dist\ClipboardHistory.zip' -Force"

echo.
echo ========================================
echo   Build complete!
echo ========================================
echo.
echo Output folder: dist\ClipboardHistory\
echo   ├── ClipboardHistory.exe
echo   ├── data/                (database and images)
echo   └── ...                  (runtime files)
echo.
echo Release zip:  dist\ClipboardHistory.zip
echo.
echo Folder structure ready for distribution.
pause
