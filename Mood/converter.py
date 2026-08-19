"""
Mood - Media conversion (parallel)
Images → PNG, Videos → MP4. Originals archived.
Unique names are collision-free (uuid) so parallel workers never overwrite.
"""

import os
import uuid
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, List, Callable
from PIL import Image
from pillow_heif import register_heif_opener
import config
from logger import log

register_heif_opener()

MAX_WORKERS = max(2, (os.cpu_count() or 4) - 1)


def _resolve_ffmpeg() -> Optional[str]:
    """
    Find an ffmpeg binary in a portable way:
      1) a system ffmpeg on PATH
      2) the ffmpeg bundled with the imageio-ffmpeg wheel (cross-platform,
         no separate install needed)
    Returns the executable path/name, or None if nothing is available.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


FFMPEG_BIN = _resolve_ffmpeg()


def _unique_name(folder: Path, base: str, ext: str) -> str:
    """Always unique even under parallel load."""
    candidate = f"{base}{ext}"
    if not (folder / candidate).exists():
        # still race-prone → add short uuid if file appears during write
        return candidate
    return f"{base}_{uuid.uuid4().hex[:8]}{ext}"


def convert_image(src: Path, dest_folder: Path, date_str: str) -> Tuple[Optional[Path], str]:
    try:
        dest_folder.mkdir(parents=True, exist_ok=True)
        # always unique under parallel workers
        new_name = f"{date_str}_{uuid.uuid4().hex[:10]}{config.TARGET_IMAGE_EXT}"
        dest = dest_folder / new_name
        with Image.open(src) as im:
            if im.mode in ("P", "LA"):
                im = im.convert("RGBA")
            elif im.mode == "CMYK":
                im = im.convert("RGB")
            elif im.mode not in ("RGB", "RGBA", "L"):
                im = im.convert("RGB")
            im.save(dest, "PNG", optimize=True)
        return dest, src.name
    except Exception as e:
        return None, str(e)


def convert_video(src: Path, dest_folder: Path, date_str: str) -> Tuple[Optional[Path], str]:
    try:
        dest_folder.mkdir(parents=True, exist_ok=True)
        new_name = f"{date_str}_{uuid.uuid4().hex[:10]}{config.TARGET_VIDEO_EXT}"
        dest = dest_folder / new_name

        if src.suffix.lower() == ".mp4":
            shutil.copy2(src, dest)
            return dest, src.name

        if not FFMPEG_BIN:
            # No system ffmpeg and imageio-ffmpeg not installed:
            # keep the original file instead of losing it.
            fallback = dest.with_suffix(src.suffix.lower())
            shutil.copy2(src, fallback)
            log.warning(f"ffmpeg missing – kept original format: {fallback.name}")
            return fallback, src.name

        cmd = [
            FFMPEG_BIN, "-y", "-i", str(src),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            "-threads", "0",
            str(dest)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return None, (result.stderr or "ffmpeg failed")[-400:]
        return dest, src.name
    except Exception as e:
        return None, str(e)


def archive_original(src: Path, archive_root: Path = config.ARCHIVE_ROOT) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    dest_dir = archive_root / day
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / src.name
    if target.exists():
        stem, ext = src.stem, src.suffix
        c = 1
        while target.exists():
            target = dest_dir / f"{stem}_{c:03d}{ext}"
            c += 1
    try:
        shutil.move(str(src), str(target))
    except Exception:
        # source may already be gone or locked – ignore
        pass
    return target


def detect_media_type(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in config.SUPPORTED_IMAGE_EXT:
        return "image"
    if ext in config.SUPPORTED_VIDEO_EXT:
        return "video"
    return None


def process_file(src: Path, dest_folder: Path, date_str: str) -> Tuple[Optional[Path], str, str]:
    media_type = detect_media_type(src)
    if media_type is None:
        return None, f"Unsupported: {src.suffix}", ""

    if media_type == "image":
        new_path, original_name = convert_image(src, dest_folder, date_str)
    else:
        new_path, original_name = convert_video(src, dest_folder, date_str)

    if new_path is None:
        return None, original_name, ""

    try:
        archive_original(src)
    except Exception:
        pass

    return new_path, original_name, media_type


def process_files_parallel(
    files: List[Path],
    dest_folder: Path,
    date_str: str,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> List[Tuple[Path, str, str]]:
    results = []
    total = len(files)
    done = 0
    log.info(f"Parallel convert: {total} files, workers={MAX_WORKERS}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(process_file, f, dest_folder, date_str): f for f in files}
        for fut in as_completed(futures):
            src = futures[fut]
            done += 1
            try:
                new_path, original, mtype = fut.result()
                if new_path and new_path.exists():
                    results.append((new_path, original, mtype))
                    log.debug(f"  OK {src.name} → {new_path.name}")
                else:
                    log.warning(f"  FAIL {src.name}: {original}")
            except Exception as e:
                log.error(f"  EXC {src.name}: {e}")
            if progress_cb:
                progress_cb(done, total, src.name)

    log.info(f"Parallel done: {len(results)}/{total}")
    return results
