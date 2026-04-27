"""
WEDNESDAY AI OS — Open App Skill
"""
from typing import Any
from core.interfaces import ISkill, SkillResult
from tools.app_launcher import open_app, close_app

class OpenAppSkill(ISkill):
    @property
    def name(self) -> str:
        return "open_app"

    @property
    def description(self) -> str:
        return "Open a desktop application by name."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the application to open (e.g. notepad, chrome)"}
            },
            "required": ["name"]
        }

    def execute(self, **kwargs: Any) -> SkillResult:
        app_name = kwargs.get("name", "")
        if not app_name:
            return SkillResult.fail(self.name, "Application name not provided.")
        
        try:
            result = open_app(app_name)
            return SkillResult.ok(self.name, result)
        except Exception as e:
            return SkillResult.fail(self.name, str(e))

class CloseAppSkill(ISkill):
    @property
    def name(self) -> str:
        return "close_app"

    @property
    def description(self) -> str:
        return "Close a desktop application by name."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the application to close"}
            },
            "required": ["name"]
        }

    def execute(self, **kwargs: Any) -> SkillResult:
        app_name = kwargs.get("name", "")
        if not app_name:
            return SkillResult.fail(self.name, "Application name not provided.")
        
        try:
            result = close_app(app_name)
            return SkillResult.ok(self.name, result)
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
