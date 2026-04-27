"""
WEDNESDAY AI OS — Terminal Control Skill
"""
import subprocess
from typing import Any
from core.interfaces import ISkill, SkillResult

class RunTerminalCommandSkill(ISkill):
    @property
    def name(self) -> str: return "run_command"
    @property
    def description(self) -> str: return "Run a command in the system terminal (Powershell/CMD)."
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"}
            },
            "required": ["command"]
        }
        
    def execute(self, **kwargs: Any) -> SkillResult:
        command = kwargs.get("command", "")
        if not command:
            return SkillResult.fail(self.name, "No command provided.")
            
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = proc.stdout.strip()
            err = proc.stderr.strip()
            
            if proc.returncode != 0:
                return SkillResult.fail(self.name, err or "Command failed.")
                
            return SkillResult.ok(self.name, output or "Executed successfully.")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
