#!/bin/bash
echo "========================================"
echo " Clipboard History — Build"
echo "========================================"
echo ""

# Clean previous build
rm -rf dist build *.spec

echo "[1/4] Installing dependencies..."
pip install -r requirements.txt --quiet

echo "[2/4] Building with PyInstaller..."
pyinstaller \
    --onedir \
    --windowed \
    --name "ClipboardHistory" \
    --add-data "assets/icon.png;assets" \
    --hidden-import win32clipboard \
    --hidden-import pynput.keyboard._win32 \
    --hidden-import PIL._imaging \
    --clean \
    src/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[FAIL] PyInstaller build failed!"
    exit 1
fi

echo "[3/4] Preparing distributable folder..."
mkdir -p "dist/ClipboardHistory/data/images"

echo "[4/4] Creating release zip..."
powershell -Command "Compress-Archive -Path 'dist\ClipboardHistory' -DestinationPath 'dist\ClipboardHistory.zip' -Force"

echo ""
echo "========================================"
echo "  Build complete!"
echo "========================================"
echo ""
echo "Output folder: dist/ClipboardHistory/"
echo "  ├── ClipboardHistory.exe"
echo "  ├── data/                (database and images)"
echo "  └── ...                  (runtime files)"
echo ""
echo "Release zip:  dist/ClipboardHistory.zip"
echo ""
echo "Folder structure ready for distribution."
