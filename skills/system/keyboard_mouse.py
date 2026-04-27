"""
WEDNESDAY AI OS — Keyboard & Mouse Skills
"""
from typing import Any
from core.interfaces import ISkill, SkillResult
from tools.automation import type_text, hotkey, press_key, mouse_click

class TypeTextSkill(ISkill):
    @property
    def name(self) -> str: return "type_text"
    @property
    def description(self) -> str: return "Type text via keyboard."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = type_text(kwargs.get("text", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class HotkeySkill(ISkill):
    @property
    def name(self) -> str: return "hotkey"
    @property
    def description(self) -> str: return "Press a keyboard shortcut (e.g. ctrl, c)."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"keys": {"type": "string", "description": "Comma separated keys"}}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            # Our existing hotkey tool takes *args but maybe we can just pass them
            keys = kwargs.get("keys", "").split(",")
            keys = [k.strip() for k in keys if k.strip()]
            import pyautogui
            pyautogui.hotkey(*keys)
            return SkillResult.ok(self.name, f"Pressed hotkey {keys}")
        except Exception as e: return SkillResult.fail(self.name, str(e))

class PressKeySkill(ISkill):
    @property
    def name(self) -> str: return "press_key"
    @property
    def description(self) -> str: return "Press a single key (e.g. enter)."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = press_key(kwargs.get("key", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class MouseClickSkill(ISkill):
    @property
    def name(self) -> str: return "mouse_click"
    @property
    def description(self) -> str: return "Click the mouse at current position."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = mouse_click()
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))
