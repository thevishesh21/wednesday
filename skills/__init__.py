"""
WEDNESDAY AI OS — Skills Engine
Auto-discovers and registers all subclasses of ISkill in the skills directory.
"""

import os
import importlib
import inspect
from pathlib import Path

from core.interfaces import ISkill
from core.logger import get_logger
# For Phase 5.2, we also push these into the old tools.registry
# so the existing executor can use them during the migration.
from tools import registry as legacy_registry

log = get_logger("skills.engine")

_skills = {}

def discover_skills():
    """Dynamically load all Skill classes from the skills directory."""
    skills_dir = Path(__file__).parent
    count = 0
    
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = Path(root).relative_to(skills_dir)
                module_name = f"skills.{rel_path}.{file[:-3]}".replace("\\", ".").replace("/", ".")
                # Clean up if rel_path is empty
                if str(rel_path) == ".":
                    module_name = f"skills.{file[:-3]}"
                    
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, ISkill) and obj is not ISkill:
                            skill_instance = obj()
                            _skills[skill_instance.name] = skill_instance
                            
                            # Add to legacy registry for backward compatibility
                            legacy_registry.register(
                                name=skill_instance.name,
                                func=lambda **kwargs: skill_instance.execute(**kwargs).result,
                                required_args=list(skill_instance.parameters.get("properties", {}).keys()),
                                description=skill_instance.description
                            )
                            count += 1
                except Exception as e:
                    log.error(f"Failed to load skill module {module_name}: {e}")
                    
    log.info(f"Loaded {count} skills into the engine.")
    return _skills

def get_skill(name: str) -> ISkill:
    return _skills.get(name)

def get_all_skills():
    return list(_skills.values())
