"""
WEDNESDAY AI OS — Git Helper Skills
"""
import subprocess
import os
from typing import Any
from core.interfaces import ISkill, SkillResult

def _run_git(args: list[str], cwd: str = ".") -> SkillResult:
    try:
        proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
        if proc.returncode != 0:
            return SkillResult.fail("git", proc.stderr.strip() or proc.stdout.strip())
        return SkillResult.ok("git", proc.stdout.strip() or "Success")
    except FileNotFoundError:
        return SkillResult.fail("git", "Git is not installed or not in PATH.")
    except Exception as e:
        return SkillResult.fail("git", str(e))

class GitStatusSkill(ISkill):
    @property
    def name(self) -> str: return "git_status"
    @property
    def description(self) -> str: return "Get the git status of a repository."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"repo_path": {"type": "string", "description": "Path to the git repo. Defaults to current directory."}}}
    def execute(self, **kwargs: Any) -> SkillResult:
        cwd = kwargs.get("repo_path", ".")
        return _run_git(["status"], cwd=cwd)

class GitCommitPushSkill(ISkill):
    @property
    def name(self) -> str: return "git_commit_push"
    @property
    def description(self) -> str: return "Commit all changes and push to the remote."
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "repo_path": {"type": "string", "description": "Repo path"}
            },
            "required": ["message"]
        }
    def execute(self, **kwargs: Any) -> SkillResult:
        msg = kwargs.get("message", "")
        cwd = kwargs.get("repo_path", ".")
        
        # Add all
        res = _run_git(["add", "."], cwd=cwd)
        if not res.success: return res
        
        # Commit
        res = _run_git(["commit", "-m", msg], cwd=cwd)
        # It's okay if commit fails because there are no changes
        
        # Push
        res = _run_git(["push"], cwd=cwd)
        return res
