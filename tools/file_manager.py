"""
Wednesday AI Assistant — File Manager Tool
Create, read, delete files and list directory contents.
"""

import os
import shutil
from utils.logger import get_logger

log = get_logger("file_mgr")


def create_file(path: str, content: str = "") -> str:
    """Create a file with optional content."""
    log.info(f"Creating file: {path}")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        log.error(f"Create file failed: {e}")
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read and return contents of a file."""
    log.info(f"Reading file: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:500]  # Limit to 500 chars for spoken output
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        log.error(f"Read file failed: {e}")
        return f"Error: {e}"


def delete_file(path: str) -> str:
    """Delete a file or folder."""
    log.info(f"Deleting: {path}")
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            return f"Not found: {path}"
        return f"Deleted: {path}"
    except Exception as e:
        log.error(f"Delete failed: {e}")
        return f"Error: {e}"


def list_files(path: str = ".") -> str:
    """List files in a directory."""
    log.info(f"Listing: {path}")
    try:
        items = os.listdir(path)
        if not items:
            return f"{path} is empty."
        return "Files: " + ", ".join(items[:20])  # Limit for speech
    except Exception as e:
        log.error(f"List failed: {e}")
        return f"Error: {e}"
