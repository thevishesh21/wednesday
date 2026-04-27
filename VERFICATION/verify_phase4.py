"""
WEDNESDAY Phase 4 — Verification Script
Run this from the project root to confirm the Agent Loop works.

Usage:
    python verify_phase4.py
"""

import sys
import asyncio
import os
from pathlib import Path

print("=" * 60)
print("  WEDNESDAY — Phase 4 Agent Loop Verification")
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


# ── Test 1: Agent Imports ────────────────────────────────────────
print("\n[1] Imports")
try:
    from agent.task_queue import task_queue, QueuedTask
    check("agent.task_queue imports", True)
except ImportError as e:
    check("agent.task_queue imports", False, str(e))

try:
    from agent.task_planner import generate_plan
    check("agent.task_planner imports", True)
except ImportError as e:
    check("agent.task_planner imports", False, str(e))

try:
    from agent.step_executor import StepExecutor
    check("agent.step_executor imports", True)
except ImportError as e:
    check("agent.step_executor imports", False, str(e))

try:
    from agent.error_recovery import execute_with_retry
    check("agent.error_recovery imports", True)
except ImportError as e:
    check("agent.error_recovery imports", False, str(e))

try:
    from agent.task_history import task_history
    check("agent.task_history imports", True)
except ImportError as e:
    check("agent.task_history imports", False, str(e))

try:
    from agent.agent_loop import agent_loop
    check("agent.agent_loop imports", True)
except ImportError as e:
    check("agent.agent_loop imports", False, str(e))


# ── Test 2: Task Queue Priority ──────────────────────────────────
print("\n[2] Task Queue")
try:
    from agent.task_queue import task_queue
    
    async def test_queue():
        id1 = await task_queue.put("task 1", priority=20)
        id2 = await task_queue.put("task 2 (urgent)", priority=5)
        
        check("Queue size is 2", task_queue.qsize == 2)
        
        # Should pop the urgent one first
        t1 = await task_queue.get()
        check("Highest priority task popped first", t1.priority == 5 and "urgent" in t1.raw_input)
        
        t2 = await task_queue.get()
        check("Lower priority task popped second", t2.priority == 20)
        
    asyncio.run(test_queue())
except Exception as e:
    check("Task Queue tests", False, str(e))


# ── Test 3: Step Executor Variable Binding ───────────────────────
print("\n[3] Step Executor Variable Binding")
try:
    from agent.step_executor import StepExecutor
    
    executor = StepExecutor()
    executor.state = {"url_result": "https://example.com"}
    
    bound_args = executor._bind_args({"url": "{url_result}", "other": "fixed"})
    check("Variable bound successfully", bound_args["url"] == "https://example.com")
    check("Static args left alone", bound_args["other"] == "fixed")
    
except Exception as e:
    check("Step Executor tests", False, str(e))


# ── Test 4: Task History DB ──────────────────────────────────────
print("\n[4] Task History SQLite Database")
try:
    import sqlite3
    from agent.task_history import task_history
    
    check("DB file exists", task_history.db_path.exists())
    
    # Write a test record
    task_history.log_task("test-123", "open notepad", "open_app", {"steps": []}, True)
    
    # Read it back
    with sqlite3.connect(task_history.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT raw_input, success FROM tasks WHERE task_id = 'test-123'")
        row = cursor.fetchone()
        
    check("Task logged and retrieved", row is not None and row[0] == "open notepad" and row[1] == 1)
    
    # Clean up test record
    with sqlite3.connect(task_history.db_path) as conn:
        conn.cursor().execute("DELETE FROM tasks WHERE task_id = 'test-123'")
        conn.commit()
        
except Exception as e:
    check("Task History tests", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 4 COMPLETE — Ready for Phase 5")
else:
    print("  ❌ Fix failures before proceeding to Phase 5")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
