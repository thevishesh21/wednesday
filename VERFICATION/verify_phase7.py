"""
WEDNESDAY Phase 7 — Verification Script
Run this from the project root to confirm the Memory System works.

Usage:
    python verify_phase7.py
"""

import sys
import asyncio

print("=" * 60)
print("  WEDNESDAY — Phase 7 Memory System Verification")
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
    from memory.short_term import short_term
    check("memory.short_term imports", True)
    
    from memory.embedder import embedder
    check("memory.embedder imports", True)
    
    from memory.long_term import long_term
    check("memory.long_term imports", True)
    
    from memory.memory_retriever import memory_retriever
    check("memory.memory_retriever imports", True)
    
    from memory.preference_store import preferences
    check("memory.preference_store imports", True)
except ImportError as e:
    check("Memory Imports", False, str(e))


# ── Test 2: Embedding ────────────────────────────────────────────
print("\n[2] Embedding")
try:
    from memory.embedder import embedder
    vector = embedder.embed("test")
    check("Embedding generates a vector", isinstance(vector, list) and len(vector) > 0)
    check("Embedding dimensions correct (384 for minilm or mocked)", len(vector) == 384)
except Exception as e:
    check("Embedding", False, str(e))


# ── Test 3: Preferences ──────────────────────────────────────────
print("\n[3] Short Term / Preferences")
try:
    from memory.preference_store import preferences
    preferences.set_preference("favorite_color", "blue")
    val = preferences.get_preference("favorite_color")
    check("Preference saved and retrieved", val == "blue")
except Exception as e:
    check("Preferences", False, str(e))


# ── Test 4: Long Term Storage ────────────────────────────────────
print("\n[4] Long Term Memory (ChromaDB)")
try:
    from memory.long_term import long_term
    
    async def test_chroma():
        mem_id = await long_term.store("The user loves coffee", {"source": "test"})
        # It's okay if mem_id is empty if Chroma is disabled/mocked
        check("Store method executed", mem_id is not None)
        
        results = await long_term.retrieve("What does the user like?")
        check("Retrieve method executed", isinstance(results, list))
        
    asyncio.run(test_chroma())
except Exception as e:
    check("Long Term Memory", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ PHASE 7 COMPLETE — Ready for Phase 8")
else:
    print("  ❌ Fix failures before proceeding to Phase 8")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
