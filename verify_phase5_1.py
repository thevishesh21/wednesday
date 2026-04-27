"""
WEDNESDAY Phase 5.1 — Verification Script
Run this from the project root to confirm OS hooks work.

Usage:
    python verify_phase5_1.py
"""

import sys
import os

print("=" * 60)
print("  WEDNESDAY — Phase 5.1 System Integration Verification")
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


# ── Test 1: Imports ──────────────────────────────────────────────
print("\n[1] Imports")
try:
    from system.windows_api import is_admin
    check("system.windows_api imports", True)
except ImportError as e:
    check("system.windows_api imports", False, str(e))

try:
    from system.permissions import permissions
    check("system.permissions imports", True)
except ImportError as e:
    check("system.permissions imports", False, str(e))

try:
    from system.startup_manager import startup_manager
    check("system.startup_manager imports", True)
except ImportError as e:
    check("system.startup_manager imports", False, str(e))

try:
    from system.hotkey_listener import hotkey_listener
    check("system.hotkey_listener imports", True)
except ImportError as e:
    check("system.hotkey_listener imports", False, str(e))

try:
    from system.tray_icon import tray_icon
    check("system.tray_icon imports", True)
except ImportError as e:
    check("system.tray_icon imports", False, str(e))


# ── Test 2: System Permissions ───────────────────────────────────
print("\n[2] Permissions")
try:
    from system.permissions import permissions
    from system.windows_api import is_admin
    
    print(f"     Admin Privileges: {'Yes' if is_admin() else 'No'}")
    check("Admin check executes without error", True)
    
    print(f"     Network Access: {'Yes' if permissions.check_network_access() else 'No'}")
    check("Network check executes without error", True)
    
except Exception as e:
    check("Permissions tests", False, str(e))


# ── Test 3: Startup Manager ──────────────────────────────────────
print("\n[3] Startup Manager")
try:
    from system.startup_manager import startup_manager
    
    # Just checking status, don't actually modify registry during verify
    is_reg = startup_manager.is_registered()
    print(f"     Currently in Startup: {'Yes' if is_reg else 'No'}")
    check("Startup check executes without error", True)
    
except Exception as e:
    check("Startup Manager tests", False, str(e))


# ── Test 4: Threads Instantiation ────────────────────────────────
print("\n[4] Threads Instantiation")
try:
    from system.hotkey_listener import hotkey_listener
    from system.tray_icon import tray_icon
    
    check("HotkeyListener instantiated", hotkey_listener is not None)
    check("TrayIcon instantiated", tray_icon is not None)
    
except Exception as e:
    check("Threads tests", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 5.1 COMPLETE — Ready for Phase 5.2")
else:
    print("  ❌ Fix failures before proceeding to Phase 5.2")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
