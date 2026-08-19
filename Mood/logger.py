"""
Mood - simple file + console logger
Writes to Mood/mood.log so Axion can copy it.
"""

import logging
from pathlib import Path
import config

LOG_FILE = config.APP_ROOT / "mood.log"

def setup_logger() -> logging.Logger:
    config.APP_ROOT.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("mood")
    logger.setLevel(logging.DEBUG)

    # clear old handlers so we don't double-log on reload
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File (overwrite each run so the log stays clean)
    fh = logging.FileHandler(str(LOG_FILE), mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info("=== Mood started ===")
    logger.info(f"APP_ROOT   = {config.APP_ROOT}")
    logger.info(f"MEDIA_ROOT = {config.MEDIA_ROOT}")
    logger.info(f"DB         = {config.DB_PATH}")
    return logger

log = setup_logger()
