"""
WEDNESDAY Phase 6 — Verification Script
Run this from the project root to confirm the UI Dashboard architecture.

Usage:
    python verify_phase6.py
"""

import sys

print("=" * 60)
print("  WEDNESDAY — Phase 6 UI Dashboard Verification")
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


# ── Test 1: UI Packages & Imports ────────────────────────────────
print("\n[1] UI Packages & Imports")
try:
    import ui
    check("ui package exists", True)
    
    from ui.state_bridge import UIStateBridge
    check("ui.state_bridge imports", True)
    
    from ui.panels.system_panel import SystemPanel
    check("ui.panels.system_panel imports", True)
    
    from ui.panels.widget_bar import WidgetBar
    check("ui.panels.widget_bar imports", True)
    
    from ui.animations.transition_fx import ColorTransitionFX
    check("ui.animations.transition_fx imports", True)
except ImportError as e:
    check("UI Imports", False, str(e))


# ── Test 2: Theme Extensions ─────────────────────────────────────
print("\n[2] Theme Extensions")
try:
    from gui.theme import STATE_QCOLORS, STATE_HEX, STATUS_TEXT
    
    for state in ["executing", "error", "complete"]:
        check(f"State '{state}' exists in QCOLORS", state in STATE_QCOLORS)
        check(f"State '{state}' exists in HEX", state in STATE_HEX)
        check(f"State '{state}' exists in STATUS_TEXT", state in STATUS_TEXT)
        
except Exception as e:
    check("Theme Extensions", False, str(e))


# ── Test 3: Animation Extensions ─────────────────────────────────
print("\n[3] Animation Extensions")
try:
    from gui.animations import _STATE_SPEEDS
    
    for state in ["executing", "error", "complete"]:
        check(f"State '{state}' speeds defined", state in _STATE_SPEEDS)
        
except Exception as e:
    check("Animation Extensions", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ PHASE 6 COMPLETE — Ready for Phase 7")
else:
    print("  ❌ Fix failures before proceeding to Phase 7")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
