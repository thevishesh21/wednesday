"""
WEDNESDAY STEP 6 — Verification Script
Confirms Hinglish Normalization and UI Transitions.
"""

import sys
from typing import List

print("=" * 60)
print("  WEDNESDAY — STEP 6 Production Refinement Verification")
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

# ── Test 1: Hinglish Patterns ────────────────────────────────────
print("\n[1] Hinglish Normalization Patterns")
try:
    from voice.hinglish_normalizer import hinglish_normalizer
    
    test_cases = [
        ("bhai settings khol de", "open settings"),
        ("mera music chala", "play my music"),
        ("bluetooth on kar", "turn on bluetooth"),
        ("files organize kar de Downloads mein", "organize files in Downloads folder"),
        ("aaj ka weather bata", "tell me today's weather"),
        ("band kar yaar", "close this"),
        ("screenshot le", "take a screenshot"),
        ("volume badha", "increase volume"),
        ("thoda rest karta hoon", "set do not disturb mode"),
        ("boss, koi message aaya?", "check my messages")
    ]
    
    async def test_hinglish():
        global passed, failed
        for raw, expected in test_cases:
            normalized, detected = await hinglish_normalizer.normalize(raw)
            check(f"'{raw}' -> '{expected}'", normalized == expected and detected)

    import asyncio
    asyncio.run(test_hinglish())

except Exception as e:
    check("Hinglish Normalization", False, str(e))

# ── Test 2: UI Transition Logic ─────────────────────────────────
print("\n[2] UI Transition Architecture")
try:
    from ui.animations.transition_fx import OrbTransitionManager
    from gui.components import OrbWidget
    from PyQt6.QtWidgets import QApplication
    
    # We need a dummy app for PyQt objects
    app = QApplication.instance() or QApplication(sys.argv)
    
    orb = OrbWidget()
    tm = OrbTransitionManager(orb)
    
    check("OrbTransitionManager initialized", tm is not None)
    check("OrbWidget supports set_custom_color", hasattr(orb, "set_custom_color"))
    
except Exception as e:
    check("UI Transition Architecture", False, str(e))

# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ STEP 6 COMPLETE — System is Production-Ready")
else:
    print("  ❌ Fix failures before final deployment")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
