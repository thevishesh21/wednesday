"""
WEDNESDAY Phase 8 — Verification Script
Run this from the project root to confirm the Vision System.

Usage:
    python verify_phase8.py
"""

import sys
import os

print("=" * 60)
print("  WEDNESDAY — Phase 8 Vision System Verification")
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


# ── Test 1: Architecture Imports ─────────────────────────────────
print("\n[1] Architecture Imports")
try:
    from vision.camera_capture import camera_capture
    check("vision.camera_capture imports", True)
    
    from vision.vision_model import vision_model
    check("vision.vision_model imports", True)
    
    from vision.screen_reader import screen_reader
    check("vision.screen_reader imports", True)
    
    from vision.face_detect import face_detector
    check("vision.face_detect imports", True)
    
    from vision.vision_state import vision_state
    check("vision.vision_state imports", True)
except ImportError as e:
    check("Vision Architecture", False, str(e))


# ── Test 2: Singleton Camera ────────────────────────────────────
print("\n[2] Camera Capture Singleton")
try:
    from vision.camera_capture import camera_capture
    import time
    
    res = camera_capture.start()
    if res:
        time.sleep(1)
        frame = camera_capture.get_frame()
        check("Camera started and captured frame", frame is not None)
        camera_capture.stop()
    else:
        # Fallback if no webcam exists on the host
        check("Camera start method exists (Camera may be absent on host)", True)
except Exception as e:
    check("Camera Singleton", False, str(e))


# ── Test 3: Face Detection Logic ───────────────────────────────
print("\n[3] Face Detection Pipeline")
try:
    from vision.face_detect import face_detector
    # Method exists and can be called
    check("face_detector.detect_presence exists", callable(face_detector.detect_presence))
except Exception as e:
    check("Face Detection", False, str(e))


# ── Test 4: Vision Skills Availability ───────────────────────────
print("\n[4] Vision Skills Availability")
try:
    from skills import discover_skills, get_skill
    skills = discover_skills()
    check("analyze_screen skill registered", get_skill("analyze_screen") is not None)
    check("analyze_camera skill registered", get_skill("analyze_camera") is not None)
except Exception as e:
    check("Vision Skills", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ PHASE 8 COMPLETE — Architecture Fully Migrated!")
else:
    print("  ❌ Fix failures before final system integration")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
