"""
WEDNESDAY AI OS — Clipboard Manager Skill
"""
import pyperclip
from typing import Any
from core.interfaces import ISkill, SkillResult

class ReadClipboardSkill(ISkill):
    @property
    def name(self) -> str: return "read_clipboard"
    @property
    def description(self) -> str: return "Get current text from the clipboard."
    @property
    def parameters(self) -> dict: return {"type": "object", "properties": {}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            return SkillResult.ok(self.name, pyperclip.paste())
        except Exception as e: return SkillResult.fail(self.name, str(e))

class WriteClipboardSkill(ISkill):
    @property
    def name(self) -> str: return "write_clipboard"
    @property
    def description(self) -> str: return "Copy text to the clipboard."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        text = kwargs.get("text", "")
        if not text:
            return SkillResult.fail(self.name, "No text provided.")
        try:
            pyperclip.copy(text)
            return SkillResult.ok(self.name, "Copied to clipboard.")
        except Exception as e: return SkillResult.fail(self.name, str(e))
