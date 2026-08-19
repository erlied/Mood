"""
Mood - Thumbnail generation & cache
"""

from pathlib import Path
from typing import Optional
from PIL import Image
import config

# Ensure HEIF support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


def _thumb_path(media_path: Path) -> Path:
    """Deterministic cache path for a media file."""
    # Use relative path hash-ish name so different performers don't collide
    key = str(media_path).replace("\\", "/").replace(":", "")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[-180:]
    return config.THUMB_CACHE / f"{safe}.jpg"


def get_thumbnail(media_path: Path, size: tuple = config.THUMB_SIZE) -> Optional[Path]:
    """
    Return path to a cached thumbnail (JPEG).
    Creates it if missing. Returns None on failure.
    """
    if not media_path.exists():
        return None

    config.THUMB_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = _thumb_path(media_path)

    if cache_file.exists():
        return cache_file

    try:
        if media_path.suffix.lower() in config.SUPPORTED_VIDEO_EXT:
            return _video_thumb(media_path, cache_file, size)
        else:
            return _image_thumb(media_path, cache_file, size)
    except Exception:
        return None


def _image_thumb(src: Path, dest: Path, size: tuple) -> Optional[Path]:
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail(size, Image.Resampling.LANCZOS)
        # Center on black background so all thumbs are same size
        bg = Image.new("RGB", size, (20, 20, 20))
        offset = ((size[0] - im.width) // 2, (size[1] - im.height) // 2)
        bg.paste(im, offset)
        bg.save(dest, "JPEG", quality=85)
    return dest


def _video_thumb(src: Path, dest: Path, size: tuple) -> Optional[Path]:
    """Grab a frame near the start with OpenCV."""
    import cv2
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        return None
    # Seek a little into the video to avoid black frames
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(30, total // 10))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(frame)
    im.thumbnail(size, Image.Resampling.LANCZOS)
    bg = Image.new("RGB", size, (20, 20, 20))
    offset = ((size[0] - im.width) // 2, (size[1] - im.height) // 2)
    bg.paste(im, offset)
    bg.save(dest, "JPEG", quality=85)
    return dest


def clear_cache():
    """Delete all cached thumbnails."""
    if config.THUMB_CACHE.exists():
        for f in config.THUMB_CACHE.glob("*.jpg"):
            try:
                f.unlink()
            except OSError:
                pass
