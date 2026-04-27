"""
WEDNESDAY AI OS — Reminder Skills
"""
from typing import Any
from core.interfaces import ISkill, SkillResult
from reminders.reminder import parse_reminder_command, list_reminders, clear_reminders

class SetReminderSkill(ISkill):
    @property
    def name(self) -> str: return "set_reminder"
    @property
    def description(self) -> str: return "Set a reminder."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"command": {"type": "string", "description": "e.g. remind me to call mom in 10 minutes"}}, "required": ["command"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = parse_reminder_command(kwargs.get("command", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class ListRemindersSkill(ISkill):
    @property
    def name(self) -> str: return "list_reminders"
    @property
    def description(self) -> str: return "List all pending reminders."
    @property
    def parameters(self) -> dict: return {"type": "object", "properties": {}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = list_reminders()
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class ClearRemindersSkill(ISkill):
    @property
    def name(self) -> str: return "clear_reminders"
    @property
    def description(self) -> str: return "Clear all pending reminders."
    @property
    def parameters(self) -> dict: return {"type": "object", "properties": {}}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = clear_reminders()
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))
