"""
Mood - Configuration
All paths and constants live here.
"""

import os
import sys
from pathlib import Path


# ============================================================
# APP ROOT  (portable + cross-platform)
# ============================================================
# Resolution order:
#   1) MOOD_HOME environment variable, if set  -> data lives there
#   2) Frozen build (PyInstaller)              -> next to the .exe/binary
#   3) Portable default                        -> the folder holding these
#      source files, so you can copy the whole "Mood" folder to any
#      Windows / macOS / Linux machine (or a USB stick) and it just runs.
def _resolve_app_root() -> Path:
    env = os.environ.get("MOOD_HOME", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    if getattr(sys, "frozen", False):                      # PyInstaller / packaged
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_ROOT = _resolve_app_root()                           # Program / data folder
MEDIA_ROOT = APP_ROOT / "Media"                          # All performer folders live here
ARCHIVE_ROOT = APP_ROOT / "Archive"                      # Originals after conversion
DB_PATH = APP_ROOT / "mood.db"                           # SQLite database
THUMB_CACHE = APP_ROOT / "thumb_cache"                   # Thumbnail cache
TEMP_IMPORT = APP_ROOT / "temp_import"                   # Staging for new files
DECRYPT_TEMP = APP_ROOT / "decrypt_temp"                 # Plaintext playback staging

# ============================================================
# BEHAVIOUR
# ============================================================
SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".heic", ".heif", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
SUPPORTED_VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".m4v", ".webm", ".flv"}
TARGET_IMAGE_EXT = ".png"
TARGET_VIDEO_EXT = ".mp4"

# Date format for renamed files: 19-08-26
DATE_FORMAT = "%d-%m-%y"

# Default countdown max (user can change every session)
DEFAULT_COUNTDOWN_MAX = 0

# Thumbnail size for grid
THUMB_SIZE = (220, 220)

# ============================================================
# UI
# ============================================================
APP_NAME = "Mood"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 720

# macOS / iOS "Liquid Glass" (Tahoe / iOS 26) dark palette
COLOR_BG = "#141417"              # window base (top of gradient)
COLOR_BG_2 = "#0d0d10"           # window base (bottom of gradient)
COLOR_SURFACE = "#232327"        # frosted panel
COLOR_SURFACE_2 = "#34343a"      # raised element
COLOR_BORDER = "#48484a"
COLOR_TEXT = "#f5f5f7"
COLOR_TEXT_DIM = "#9a9aa2"
COLOR_ACCENT = "#0a84ff"          # system blue
COLOR_ACCENT_HOVER = "#3a9bff"
COLOR_ACCENT_2 = "#0060df"        # gradient bottom for liquid buttons
COLOR_DANGER = "#ff453a"
COLOR_SUCCESS = "#30d158"
