"""
WEDNESDAY AI OS — File Explorer Skills
"""
import os
import subprocess
from typing import Any
from core.interfaces import ISkill, SkillResult
from tools.file_manager import create_file, read_file, delete_file, list_files

class OpenFolderSkill(ISkill):
    @property
    def name(self) -> str:
        return "open_folder"

    @property
    def description(self) -> str:
        return "Open a specific folder in Windows File Explorer."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the folder"}
            },
            "required": ["path"]
        }

    def execute(self, **kwargs: Any) -> SkillResult:
        path = kwargs.get("path", "")
        if not path or not os.path.isdir(path):
            return SkillResult.fail(self.name, f"Invalid directory path: {path}")
        
        try:
            # explorer.exe is Windows specific
            subprocess.Popen(['explorer', os.path.realpath(path)])
            return SkillResult.ok(self.name, f"Opened folder: {path}")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))

class CreateFileSkill(ISkill):
    @property
    def name(self) -> str:
        return "create_file"
    @property
    def description(self) -> str: return "Create a new file."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = create_file(kwargs.get("path", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class ReadFileSkill(ISkill):
    @property
    def name(self) -> str: return "read_file"
    @property
    def description(self) -> str: return "Read file contents."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = read_file(kwargs.get("path", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class DeleteFileSkill(ISkill):
    @property
    def name(self) -> str: return "delete_file"
    @property
    def description(self) -> str: return "Delete a file."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = delete_file(kwargs.get("path", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class ListFilesSkill(ISkill):
    @property
    def name(self) -> str: return "list_files"
    @property
    def description(self) -> str: return "List files in the current directory."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = list_files()
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))
