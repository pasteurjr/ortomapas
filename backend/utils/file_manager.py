"""
File management utilities for uploads, exports, and cleanup.
"""

import logging
import os
import shutil
import time
import uuid
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger(__name__)


async def save_upload(
    file: UploadFile,
    destination_dir: str,
    filename: Optional[str] = None,
) -> str:
    """
    Save an uploaded file to the destination directory.

    Args:
        file: The FastAPI UploadFile object.
        destination_dir: Directory where the file will be saved.
        filename: Optional filename override. If None, uses original or generates UUID.

    Returns:
        Full path to the saved file.
    """
    ensure_dir(destination_dir)

    if filename is None:
        if file.filename:
            # Sanitize and make unique
            base, ext = os.path.splitext(file.filename)
            safe_base = "".join(c if c.isalnum() or c in "-_" else "_" for c in base)
            filename = f"{safe_base}_{uuid.uuid4().hex[:8]}{ext}"
        else:
            filename = f"{uuid.uuid4().hex}.bin"

    filepath = os.path.join(destination_dir, filename)

    try:
        with open(filepath, "wb") as buffer:
            # Read in chunks for memory efficiency
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                buffer.write(chunk)

        logger.info(f"File saved: {filepath} ({get_file_size_mb(filepath):.2f} MB)")
        return filepath

    except Exception as e:
        # Clean up partial file on error
        if os.path.exists(filepath):
            os.remove(filepath)
        logger.error(f"Error saving upload to {filepath}: {e}")
        raise


def get_file_size_mb(filepath: str) -> float:
    """Return the file size in megabytes."""
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    except OSError as e:
        logger.error(f"Error getting file size for {filepath}: {e}")
        return 0.0


def cleanup_old_exports(exports_dir: str, max_age_hours: int = 24) -> int:
    """
    Remove export files older than max_age_hours.

    Args:
        exports_dir: Directory containing export files.
        max_age_hours: Maximum age in hours before files are removed.

    Returns:
        Number of files removed.
    """
    if not os.path.exists(exports_dir):
        return 0

    removed = 0
    cutoff = time.time() - (max_age_hours * 3600)

    try:
        for entry in os.scandir(exports_dir):
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                os.remove(entry.path)
                logger.info(f"Removed old export: {entry.path}")
                removed += 1
            elif entry.is_dir() and entry.stat().st_mtime < cutoff:
                shutil.rmtree(entry.path)
                logger.info(f"Removed old export dir: {entry.path}")
                removed += 1
    except Exception as e:
        logger.error(f"Error during export cleanup: {e}")

    if removed:
        logger.info(f"Cleanup complete: {removed} old export(s) removed.")
    return removed


def ensure_dir(path: str) -> str:
    """Create directory if it does not exist. Returns the path."""
    os.makedirs(path, exist_ok=True)
    return path
