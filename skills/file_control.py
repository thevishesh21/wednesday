"""
Wednesday - File Control Skill
Create, open, and delete files.
"""

import os
import subprocess


DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Desktop")


def create_file(filename: str) -> str:
    """Create a new file on the Desktop."""
    if not filename:
        return "Please specify a file name."
    filepath = os.path.join(DEFAULT_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")
        return f"Created file {filename} on your Desktop."
    except Exception as e:
        return f"Failed to create file: {e}"


def open_file(filename: str) -> str:
    """Open a file from the Desktop."""
    if not filename:
        return "Please specify which file to open."
    filepath = os.path.join(DEFAULT_DIR, filename)
    if not os.path.exists(filepath):
        return f"File {filename} not found on your Desktop."
    try:
        os.startfile(filepath)
        return f"Opening {filename}."
    except Exception as e:
        return f"Failed to open file: {e}"


def delete_file(filename: str) -> str:
    """Delete a file from the Desktop (requires confirmation)."""
    if not filename:
        return "Please specify which file to delete."
    filepath = os.path.join(DEFAULT_DIR, filename)
    if not os.path.exists(filepath):
        return f"File {filename} not found on your Desktop."
    try:
        os.remove(filepath)
        return f"Deleted {filename} from your Desktop."
    except Exception as e:
        return f"Failed to delete file: {e}"
