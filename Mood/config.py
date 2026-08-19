"""
Mood - Configuration
All paths and constants live here.
"""

from pathlib import Path

# ============================================================
# USER PATHS - change only these if needed
# ============================================================
APP_ROOT = Path(r"C:\Users\gamed\Desktop\Mood")          # Program folder
MEDIA_ROOT = APP_ROOT / "Media"                          # All performer folders live here
ARCHIVE_ROOT = APP_ROOT / "Archive"                      # Originals after conversion
DB_PATH = APP_ROOT / "mood.db"                           # SQLite database
THUMB_CACHE = APP_ROOT / "thumb_cache"                   # Thumbnail cache
TEMP_IMPORT = APP_ROOT / "temp_import"
DECRYPT_TEMP = APP_ROOT / "decrypt_temp"                   # Staging for new files

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

# macOS-inspired dark (Liquid Glass / Tahoe feel)
COLOR_BG = "#1c1c1e"
COLOR_SURFACE = "#2c2c2e"
COLOR_SURFACE_2 = "#3a3a3c"
COLOR_BORDER = "#48484a"
COLOR_TEXT = "#f5f5f7"
COLOR_TEXT_DIM = "#98989d"
COLOR_ACCENT = "#0a84ff"          # system blue
COLOR_ACCENT_HOVER = "#409cff"
COLOR_DANGER = "#ff453a"
COLOR_SUCCESS = "#30d158"
