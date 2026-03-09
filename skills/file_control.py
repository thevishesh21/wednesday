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


def rename_file(old_name: str, new_name: str = "") -> str:
    """Rename a file on the Desktop."""
    if not old_name:
        return "Please specify the file to rename."
    if not new_name:
        return "Please specify the new name."
    old_path = os.path.join(DEFAULT_DIR, old_name)
    new_path = os.path.join(DEFAULT_DIR, new_name)
    if not os.path.exists(old_path):
        return f"File {old_name} not found on your Desktop."
    try:
        os.rename(old_path, new_path)
        return f"Renamed {old_name} to {new_name}."
    except Exception as e:
        return f"Failed to rename file: {e}"


def open_folder(folder_name: str) -> str:
    """Open a folder. Supports common folder names and absolute paths."""
    folder_map = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
        "music": os.path.join(os.path.expanduser("~"), "Music"),
        "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    }

    normalized = folder_name.lower().strip()
    # Strip common prefixes
    for prefix in ("my ", "the "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]

    # Add "folder" stripping
    if normalized.endswith(" folder"):
        normalized = normalized[:-7].strip()

    path = folder_map.get(normalized, folder_name)
    if os.path.isdir(path):
        try:
            os.startfile(path)
            return f"Opening {folder_name} folder."
        except Exception as e:
            return f"Failed to open folder: {e}"
    return f"Folder '{folder_name}' not found."


def find_file(query: str) -> str:
    """Search common user directories for a file matching the query."""
    if not query:
        return "What file should I look for?"

    search_dirs = [
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Downloads"),
    ]

    matches = []
    query_lower = query.lower()

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            # Limit depth to 3 levels
            depth = root.replace(search_dir, "").count(os.sep)
            if depth > 3:
                dirs.clear()
                continue
            for fname in files:
                if query_lower in fname.lower():
                    matches.append(os.path.join(root, fname))
                    if len(matches) >= 5:
                        break
            if len(matches) >= 5:
                break

    if not matches:
        return f"Could not find any files matching '{query}'."

    if len(matches) == 1:
        return f"Found: {matches[0]}"

    result = f"Found {len(matches)} files: "
    result += ", ".join(os.path.basename(m) for m in matches)
    return result
