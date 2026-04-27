"""
WEDNESDAY Phase 5.2 — Verification Script
Run this from the project root to confirm the Skill Engine works.

Usage:
    python verify_phase5_2.py
"""

import sys

print("=" * 60)
print("  WEDNESDAY — Phase 5.2 Skill Engine Verification")
print("=" * 60)

passed = 0
failed = 0

def check(label: str, condition: bool, error: str = "") -> None:
    global passed, failed
    if condition:
        print(f"  ✅ {label}")
        passed += 1
    else:
        print(f"  ❌ {label}")
        if error:
            print(f"     └─ {error}")
        failed += 1


# ── Test 1: Skill Engine Discovery ───────────────────────────────
print("\n[1] Skill Engine Discovery")
try:
    from skills import discover_skills, get_skill
    
    skills = discover_skills()
    check(f"Discovered {len(skills)} skills", len(skills) > 0)
    
    open_app_skill = get_skill("open_app")
    check("open_app skill found", open_app_skill is not None)
    
except Exception as e:
    check("Skill Engine Discovery", False, str(e))


# ── Test 2: ISkill Interface Compliance ──────────────────────────
print("\n[2] ISkill Interface Compliance")
try:
    from skills import get_skill
    
    skill = get_skill("open_app")
    if skill:
        check("Has name property", getattr(skill, "name", None) == "open_app")
        check("Has description property", isinstance(getattr(skill, "description", None), str))
        check("Has parameters property", isinstance(getattr(skill, "parameters", None), dict))
        check("Has to_llm_schema method", callable(getattr(skill, "to_llm_schema", None)))
        
        schema = skill.to_llm_schema()
        check("Schema generates correctly", "name" in schema and "parameters" in schema)
    else:
        check("ISkill compliance tests", False, "Skill not found")
        
except Exception as e:
    check("ISkill Interface Compliance", False, str(e))


# ── Test 3: System Skills Loaded ─────────────────────────────────
print("\n[3] System Skills Availability")
try:
    from skills import get_skill
    
    expected_skills = [
        "open_app", "close_app", 
        "open_folder", "create_file", "delete_file", 
        "type_text", "hotkey", "press_key", 
        "open_settings", 
        "list_processes", "kill_process"
    ]
    
    for s in expected_skills:
        check(f"Skill '{s}' loaded", get_skill(s) is not None)
        
except Exception as e:
    check("System Skills Availability", False, str(e))


# ── Test 4: Legacy Registry Integration ──────────────────────────
print("\n[4] Legacy Registry Integration")
try:
    from tools import registry
    
    tools = registry.list_tools()
    check("Legacy registry populated from skills engine", "open_settings" in tools and "kill_process" in tools)
    
except Exception as e:
    check("Legacy Registry Integration", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 5.2 COMPLETE — Ready for Phase 5.3")
else:
    print("  ❌ Fix failures before proceeding to Phase 5.3")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
