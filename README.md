# Clipboard History

A lightweight Windows clipboard manager that records everything you copy — text and images — and lets you browse, search, and re-paste anytime.

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Auto-record** — monitors clipboard in the background, saves text and images automatically
- **Card-based history** — browse all copied items as cards, sorted by time (newest first)
- **Pin & Delete** — pin important items to the top, delete anything you don't need
- **Search** — real-time fuzzy search across all text items
- **One-click re-paste** — click any card to copy its content back to the clipboard
- **Configurable retention** — set storage duration (1 / 3 / 5 days) and max item count
- **Global hotkey** — quickly open the history panel from any app (default: `Ctrl+Shift+V`)
- **System tray** — stays in the tray, out of your way until you need it

## Installation

### Option 1: Download & Extract (recommended)

1. Download `ClipboardHistory.zip` from the [latest release](https://github.com/mjsakasaka/clipboard-history/releases)
2. Extract the `ClipboardHistory/` folder to any location you like (e.g. `Desktop` or `Program Files`)
3. Double-click `ClipboardHistory.exe` to run

All data (database and images) will be stored inside the `data/` folder alongside the .exe, keeping everything contained.

### Option 2: Run from source

```bash
# 1. Clone the repo
git clone https://github.com/mjsakasaka/clipboard-history.git
cd clipboard-history

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python src/main.py
```

## Usage

| Action | How |
|--------|-----|
| Open history panel | Double-click tray icon, or press `Ctrl+Shift+V` |
| Copy a card | Click the card content area |
| Pin a card | Click the 📌 button |
| Delete a card | Click the 🗑 button, then confirm |
| Search | Type in the search bar at the top |
| Change settings | Right-click tray icon → Settings, or click ⚙ in the window |
| Pause monitoring | Right-click tray icon → Pause Monitoring |
| Quit | Right-click tray icon → Quit |

## Build from source

```bash
# Generate app icon
python generate_icon.py

# Build executable
build.bat
```

Output:
```
dist/ClipboardHistory/        ← distributable folder
├── ClipboardHistory.exe
├── data/images/
└── ...
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | PySide6 (Qt for Python) |
| Clipboard | pywin32 |
| Global hotkey | pynput |
| Image handling | Pillow |
| Database | SQLite |
| Packaging | PyInstaller |

## Project Structure

```
├── src/               # Source code
│   ├── main.py        # Entry point
│   ├── database.py    # SQLite operations
│   ├── config.py      # Settings management
│   ├── clipboard_monitor.py  # Background clipboard watcher
│   ├── cleanup.py     # Timed cleanup
│   ├── ui/            # GUI components
│   └── utils/         # Utilities (hotkey)
├── tests/             # Test scripts (52 tests)
├── docs/              # Documentation
├── assets/            # App icon
└── build.bat          # Build script
```

## License

MIT — see [LICENSE](LICENSE) for details.
