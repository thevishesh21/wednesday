"""
WEDNESDAY AI OS — Process Manager Skill
List and kill stuck apps via psutil.
"""
from typing import Any
from core.interfaces import ISkill, SkillResult

class ListProcessesSkill(ISkill):
    @property
    def name(self) -> str: return "list_processes"
    
    @property
    def description(self) -> str: return "List top 10 running processes by memory usage."
    
    @property
    def parameters(self) -> dict: return {"type": "object", "properties": {}}
    
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by memory usage
            processes = sorted(processes, key=lambda p: p['memory_info'].rss if p['memory_info'] else 0, reverse=True)
            top = processes[:10]
            
            res = [f"{p['name']} (PID: {p['pid']}, Mem: {p['memory_info'].rss / 1024 / 1024:.1f}MB)" for p in top]
            return SkillResult.ok(self.name, "\n".join(res))
        except Exception as e:
            return SkillResult.fail(self.name, str(e))

class KillProcessSkill(ISkill):
    @property
    def name(self) -> str: return "kill_process"
    
    @property
    def description(self) -> str: return "Kill a running process by name (e.g. chrome.exe) or PID."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {
                "process_name": {"type": "string", "description": "Name of the process to kill"}
            },
            "required": ["process_name"]
        }
    
    def execute(self, **kwargs: Any) -> SkillResult:
        proc_name = kwargs.get("process_name", "")
        if not proc_name:
            return SkillResult.fail(self.name, "Process name not provided.")
            
        try:
            import psutil
            killed = 0
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc_name.lower() in proc.info['name'].lower():
                    try:
                        proc.kill()
                        killed += 1
                    except psutil.AccessDenied:
                        return SkillResult.fail(self.name, f"Access denied. Cannot kill {proc.info['name']}.")
            
            if killed > 0:
                return SkillResult.ok(self.name, f"Killed {killed} instances of {proc_name}.")
            else:
                return SkillResult.fail(self.name, f"No process found matching {proc_name}.")
        except Exception as e:
            return SkillResult.fail(self.name, str(e))
