"""
WEDNESDAY AI OS — Settings Navigation Skill
Opens specific Windows settings pages using URI schemes.
"""
import subprocess
from typing import Any
from core.interfaces import ISkill, SkillResult

# Common Windows ms-settings URIs
_SETTINGS_MAP = {
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "wifi": "ms-settings:network-wifi",
    "bluetooth": "ms-settings:bluetooth",
    "update": "ms-settings:windowsupdate",
    "about": "ms-settings:about",
    "apps": "ms-settings:appsfeatures",
    "privacy": "ms-settings:privacy"
}

class OpenSettingsSkill(ISkill):
    @property
    def name(self) -> str:
        return "open_settings"

    @property
    def description(self) -> str:
        return f"Open a specific Windows settings page. Options: {', '.join(_SETTINGS_MAP.keys())}"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string", 
                    "description": "Category of settings to open"
                }
            },
            "required": ["category"]
        }

    def execute(self, **kwargs: Any) -> SkillResult:
        category = kwargs.get("category", "").lower()
        
        if not category:
            # Open general settings
            subprocess.Popen(['start', 'ms-settings:'], shell=True)
            return SkillResult.ok(self.name, "Opened Windows Settings.")
            
        uri = _SETTINGS_MAP.get(category)
        if not uri:
            return SkillResult.fail(self.name, f"Unknown settings category: {category}")
            
        try:
            subprocess.Popen(['start', uri], shell=True)
            return SkillResult.ok(self.name, f"Opened Windows Settings: {category}")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
