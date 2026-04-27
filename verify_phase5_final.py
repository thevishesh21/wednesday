"""
WEDNESDAY Phase 5 Final — Verification Script
Run this from the project root to confirm all web, productivity, and dev skills load correctly.

Usage:
    python verify_phase5_final.py
"""

import sys

print("=" * 60)
print("  WEDNESDAY — Phase 5 Final Skill Engine Verification")
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


# ── Test 1: Full Engine Discovery ────────────────────────────────
print("\n[1] Skill Engine Discovery (All Phases)")
try:
    from skills import discover_skills, get_skill
    
    skills = discover_skills()
    check(f"Discovered {len(skills)} total skills", len(skills) >= 20)
    
except Exception as e:
    check("Full Engine Discovery", False, str(e))


# ── Test 2: Web Skills Availability ──────────────────────────────
print("\n[2] Web Skills Availability")
try:
    expected = ["search_google", "search_youtube", "open_website", "get_weather"]
    for s in expected:
        check(f"Skill '{s}' loaded", get_skill(s) is not None)
except Exception as e:
    check("Web Skills Availability", False, str(e))


# ── Test 3: Productivity Skills Availability ─────────────────────
print("\n[3] Productivity Skills Availability")
try:
    expected = ["set_reminder", "list_reminders", "clear_reminders", "read_clipboard", "write_clipboard", "organize_folder"]
    for s in expected:
        check(f"Skill '{s}' loaded", get_skill(s) is not None)
except Exception as e:
    check("Productivity Skills Availability", False, str(e))


# ── Test 4: Dev Skills Availability ──────────────────────────────
print("\n[4] Dev Skills Availability")
try:
    expected = ["run_python", "git_status", "git_commit_push", "run_command"]
    for s in expected:
        check(f"Skill '{s}' loaded", get_skill(s) is not None)
except Exception as e:
    check("Dev Skills Availability", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ PHASE 5 FULLY COMPLETE — Ready for Phase 6")
else:
    print("  ❌ Fix failures before proceeding to Phase 6")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
