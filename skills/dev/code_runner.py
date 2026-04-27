"""
WEDNESDAY AI OS — Code Runner Skill
Executes Python scripts safely.
"""
import tempfile
import subprocess
import os
from typing import Any
from core.interfaces import ISkill, SkillResult

class RunPythonSkill(ISkill):
    @property
    def name(self) -> str: return "run_python"
    @property
    def description(self) -> str: return "Run Python code and return the output."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"code": {"type": "string", "description": "Python code to execute"}}, "required": ["code"]}
        
    def execute(self, **kwargs: Any) -> SkillResult:
        code = kwargs.get("code", "")
        if not code:
            return SkillResult.fail(self.name, "No code provided.")
            
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as f:
                f.write(code)
                script_path = f.name
                
            proc = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=10)
            os.remove(script_path)
            
            output = proc.stdout.strip()
            err = proc.stderr.strip()
            
            if proc.returncode != 0:
                return SkillResult.fail(self.name, f"Error: {err}")
            
            return SkillResult.ok(self.name, output if output else "Executed successfully (no output).")
            
        except subprocess.TimeoutExpired:
            if os.path.exists(script_path): os.remove(script_path)
            return SkillResult.fail(self.name, "Execution timed out after 10 seconds.")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
