"""
WEDNESDAY AI OS — File Organizer Skill
"""
import os
import shutil
from pathlib import Path
from typing import Any
from core.interfaces import ISkill, SkillResult

_EXT_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".csv", ".pptx"],
    "Media": [".mp4", ".mp3", ".wav", ".mkv", ".mov", ".avi"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Executables": [".exe", ".msi"]
}

class OrganizeFolderSkill(ISkill):
    @property
    def name(self) -> str: return "organize_folder"
    @property
    def description(self) -> str: return "Organize a folder by grouping files into subfolders by type."
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {"folder_path": {"type": "string", "description": "Path to organize. If empty, defaults to Downloads."}}
        }
        
    def execute(self, **kwargs: Any) -> SkillResult:
        folder = kwargs.get("folder_path", "")
        if not folder:
            # Default to downloads
            folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            
        path = Path(folder)
        if not path.exists() or not path.is_dir():
            return SkillResult.fail(self.name, f"Invalid folder: {folder}")
            
        moved_count = 0
        try:
            for item in path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    target_dir = "Others"
                    for cat, exts in _EXT_MAP.items():
                        if ext in exts:
                            target_dir = cat
                            break
                            
                    target_path = path / target_dir
                    target_path.mkdir(exist_ok=True)
                    
                    try:
                        shutil.move(str(item), str(target_path / item.name))
                        moved_count += 1
                    except Exception:
                        pass
                        
            return SkillResult.ok(self.name, f"Organized {moved_count} files in {folder}.")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
