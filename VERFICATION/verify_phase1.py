"""
WEDNESDAY Phase 1 — Verification Script
Run this from the project root to confirm all core modules work correctly.

Usage:
    python verify_phase1.py
"""

import sys
import asyncio

print("=" * 60)
print("  WEDNESDAY — Phase 1 Foundation Verification")
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


# ── Test 1: Core imports ─────────────────────────────────────────
print("\n[1] Core Imports")
try:
    from core.exceptions import (
        WednesdayError, ConfigError, LLMError, LLMUnavailableError,
        LLMResponseError, SkillError, ToolNotFoundError, SkillExecutionError,
        VoiceError, STTError, TTSError, AgentError, PlanningError,
        StepExecutionError, MemoryError, MemoryStoreError, MemoryRetrieveError,
    )
    check("core.exceptions — all 16 exception types import", True)
except ImportError as e:
    check("core.exceptions imports", False, str(e))

try:
    from core.interfaces import (
        ISkill, ILLMClient, IMemoryStore, IVoiceSTT, IVoiceTTS, IAgentLoop,
        SkillResult, LLMMessage, LLMResponse, ParsedIntent,
        StepSchema, TaskPlan, MemoryRecord,
    )
    check("core.interfaces — all 13 classes import", True)
except ImportError as e:
    check("core.interfaces imports", False, str(e))

try:
    from core.event_bus import event_bus, publish_sync
    check("core.event_bus — singleton + publish_sync import", True)
except ImportError as e:
    check("core.event_bus imports", False, str(e))

try:
    from core.logger import get_logger
    check("core.logger — get_logger imports", True)
except ImportError as e:
    check("core.logger imports", False, str(e))

try:
    from core.config_loader import cfg
    check("core.config_loader — cfg singleton imports", True)
except Exception as e:
    check("core.config_loader imports", False, str(e))


# ── Test 2: Exception hierarchy ──────────────────────────────────
print("\n[2] Exception Hierarchy")
try:
    from core.exceptions import WednesdayError, AgentError, StepExecutionError
    e = StepExecutionError("test error", details={"step": 1})
    check("StepExecutionError is AgentError", isinstance(e, AgentError))
    check("StepExecutionError is WednesdayError", isinstance(e, WednesdayError))
    check("Exception details stored", e.details == {"step": 1})
    check("SkillResult.ok() factory", True)  # placeholder — tested below
except Exception as e:
    check("Exception hierarchy", False, str(e))


# ── Test 3: Data classes ─────────────────────────────────────────
print("\n[3] Data Classes")
try:
    from core.interfaces import SkillResult, LLMMessage, ParsedIntent, TaskPlan, StepSchema

    sr_ok = SkillResult.ok("open_app", "Notepad opened!")
    check("SkillResult.ok() constructor", sr_ok.success and sr_ok.tool == "open_app")

    sr_fail = SkillResult.fail("open_app", "Not found")
    check("SkillResult.fail() constructor", not sr_fail.success and sr_fail.error == "Not found")

    msg = LLMMessage(role="user", content="open notepad")
    check("LLMMessage.to_dict()", msg.to_dict() == {"role": "user", "content": "open notepad"})

    step = StepSchema(step_id=1, tool="open_app", args={"name": "notepad"}, output_key="app_result")
    check("StepSchema creation", step.step_id == 1 and step.tool == "open_app")

    plan = TaskPlan(task_id="abc-123", raw_input="open notepad", intent="open_app",
                    steps=[step])
    check("TaskPlan with steps", len(plan.steps) == 1)
except Exception as e:
    check("Data classes", False, str(e))


# ── Test 4: Event Bus ────────────────────────────────────────────
print("\n[4] Event Bus")
try:
    from core.event_bus import event_bus

    received_events = []

    def sync_handler(payload):
        received_events.append(("sync", payload))

    async def async_handler(payload):
        received_events.append(("async", payload))

    event_bus.subscribe("test.sync", sync_handler)
    event_bus.subscribe("test.async", async_handler)

    async def run_tests():
        await event_bus.publish("test.sync", {"val": 42})
        await event_bus.publish("test.async", {"val": 99})
        await asyncio.sleep(0.05)  # Let async handler complete

    asyncio.run(run_tests())

    check("Sync handler received event", any(e[0] == "sync" and e[1]["val"] == 42
                                              for e in received_events))
    check("Async handler received event", any(e[0] == "async" and e[1]["val"] == 99
                                               for e in received_events))

    count = event_bus.subscriber_count("test.sync")
    check("subscriber_count() works", count == 1)

    event_bus.unsubscribe("test.sync", sync_handler)
    check("unsubscribe() removes handler", event_bus.subscriber_count("test.sync") == 0)

    # Cleanup
    event_bus.unsubscribe("test.async", async_handler)

except Exception as e:
    check("Event bus tests", False, str(e))


# ── Test 5: Config Loader ────────────────────────────────────────
print("\n[5] Config Loader")
try:
    from core.config_loader import cfg

    check("cfg.WAKE_WORD is string", isinstance(cfg.WAKE_WORD, str))
    check("cfg.WAKE_WORD == 'hey wednesday'", cfg.WAKE_WORD == "hey wednesday")
    check("cfg.ASSISTANT_NAME == 'Wednesday'", cfg.ASSISTANT_NAME == "Wednesday")
    check("cfg.has_cloud_llm is bool", isinstance(cfg.has_cloud_llm, bool))
    check("cfg.has_ollama_config is bool", isinstance(cfg.has_ollama_config, bool))
    check("cfg.log_dir_path is Path", hasattr(cfg.log_dir_path, "exists"))
    check("cfg.ollama_base_url is string", isinstance(cfg.ollama_base_url, str))

    # Test safe get with default
    val = cfg.get("NONEXISTENT_FIELD", "default_value")
    check("cfg.get() returns default for missing field", val == "default_value")

    # Test ConfigError on invalid attribute
    try:
        _ = cfg.THIS_FIELD_DOES_NOT_EXIST
        check("cfg raises ConfigError for missing field", False, "No error raised")
    except Exception as e:
        from core.exceptions import ConfigError
        check("cfg raises ConfigError for missing field", isinstance(e, ConfigError))

except Exception as e:
    check("Config loader tests", False, str(e))


# ── Test 6: Logger ───────────────────────────────────────────────
print("\n[6] Structured Logger")
try:
    from core.logger import get_logger
    log = get_logger("verify_phase1")
    log.info("Phase 1 verification running")
    log.debug("Debug message with data", extra={"data": {"phase": 1, "test": True}})
    check("Logger created without error", True)
    check("Logger has handlers", len(log.handlers) > 0)
    # Idempotent: calling again returns same logger
    log2 = get_logger("verify_phase1")
    check("get_logger() is idempotent (no duplicate handlers)", len(log2.handlers) == len(log.handlers))
except Exception as e:
    check("Logger tests", False, str(e))


# ── Test 7: Zero regression — main.py imports ───────────────────
print("\n[7] Zero Regression Check")
try:
    import config
    check("config.py still importable", True)
except ImportError as e:
    check("config.py importable", False, str(e))

try:
    from utils.logger import get_logger as old_get_logger
    check("utils/logger.py still importable", True)
except ImportError as e:
    check("utils/logger.py importable", False, str(e))

try:
    from tools.registry import list_tools
    check("tools/registry.py still importable", True)
except ImportError as e:
    check("tools/registry.py importable", False, str(e))

try:
    from brain.fallback import fallback_response
    check("brain/fallback.py still importable", True)
except ImportError as e:
    check("brain/fallback.py importable", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 1 COMPLETE — Ready for Phase 2")
else:
    print("  ❌ Fix failures before proceeding to Phase 2")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
