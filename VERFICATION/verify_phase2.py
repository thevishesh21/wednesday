"""
WEDNESDAY Phase 2 — Verification Script
Run this from the project root to confirm all brain layer modules work correctly.

Usage:
    python verify_phase2.py
"""

import sys
import asyncio
import os

print("=" * 60)
print("  WEDNESDAY — Phase 2 Brain Layer Verification")
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


# ── Test 1: Core/Brain Imports ───────────────────────────────────
print("\n[1] Imports")
try:
    from brain.prompt_templates import INTENT_PARSER_PROMPT, TASK_PLANNER_PROMPT
    check("brain.prompt_templates imports", True)
except ImportError as e:
    check("brain.prompt_templates imports", False, str(e))

try:
    from brain.tool_registry import get_all_schemas, get_schema
    check("brain.tool_registry imports", True)
except ImportError as e:
    check("brain.tool_registry imports", False, str(e))

try:
    from brain.context_manager import ContextManager
    check("brain.context_manager imports", True)
except ImportError as e:
    check("brain.context_manager imports", False, str(e))

try:
    from brain.llm_client import OllamaClient, OpenRouterClient, get_llm_client
    check("brain.llm_client imports", True)
except ImportError as e:
    check("brain.llm_client imports", False, str(e))

try:
    from brain.intent_parser import parse
    check("brain.intent_parser imports", True)
except ImportError as e:
    check("brain.intent_parser imports", False, str(e))


# ── Test 2: Tool Registry ────────────────────────────────────────
print("\n[2] Tool Schema Registry")
try:
    from brain.tool_registry import get_all_schemas, get_schema
    schemas = get_all_schemas()
    check(f"Loaded {len(schemas)} tool schemas", len(schemas) > 0)
    
    app_schema = get_schema("open_app")
    check("open_app schema has 'name'", "name" in app_schema)
    check("open_app schema has 'parameters'", "parameters" in app_schema)
    check("open_app requires 'name'", "name" in app_schema["parameters"]["required"])
    
    try:
        get_schema("this_tool_does_not_exist")
        check("get_schema raises ToolNotFoundError on miss", False, "No error raised")
    except Exception as e:
        from core.exceptions import ToolNotFoundError
        check("get_schema raises ToolNotFoundError on miss", isinstance(e, ToolNotFoundError))
        
except Exception as e:
    check("Tool registry tests", False, str(e))


# ── Test 3: Context Manager ──────────────────────────────────────
print("\n[3] Context Manager")
try:
    from brain.context_manager import ContextManager
    ctx = ContextManager(system_prompt="You are AI")
    
    msgs = ctx.get_messages()
    check("Initializes with system prompt", len(msgs) == 1 and msgs[0].role == "system")
    
    ctx.add_message("user", "Hello")
    ctx.add_message("assistant", "Hi there")
    check("Adds messages correctly", len(ctx.get_messages()) == 3)
    
    tokens = ctx.token_estimate()
    check("Token estimate > 0", tokens > 0)
    
    ctx.clear()
    check("clear() preserves system prompt", len(ctx.get_messages()) == 1)
    
    # Test trimming
    for i in range(10):
        ctx.add_message("user", "x" * 100) # ~25 tokens each
    
    # Force trim to small limit
    ctx.trim(max_tokens=100)
    trimmed_msgs = ctx.get_messages()
    check("trim() reduces message count", len(trimmed_msgs) < 11)
    check("trim() preserves system prompt", trimmed_msgs[0].role == "system")
    
except Exception as e:
    check("Context manager tests", False, str(e))


# ── Test 4: LLM Client Availability ──────────────────────────────
print("\n[4] LLM Client Initialization")
try:
    from brain.llm_client import get_llm_client, OllamaClient, OpenRouterClient
    
    async def test_llm():
        # Just test availability checks, don't make real calls to save money/time
        ollama = OllamaClient()
        o_avail = await ollama.is_available()
        print(f"    ├─ Ollama available: {o_avail}")
        
        openrouter = OpenRouterClient()
        r_avail = await openrouter.is_available()
        print(f"    ├─ OpenRouter available: {r_avail}")
        
        try:
            client = await get_llm_client()
            check(f"get_llm_client() returned {type(client).__name__}", client is not None)
            return True
        except Exception as e:
            from core.exceptions import LLMUnavailableError
            if isinstance(e, LLMUnavailableError):
                check("get_llm_client() raised LLMUnavailableError (expected if no keys/Ollama)", True)
                return True
            raise e
            
    success = asyncio.run(test_llm())
    
except Exception as e:
    check("LLM Client tests", False, str(e))


# ── Test 5: Intent Parser Fast Path ──────────────────────────────
print("\n[5] Intent Parser (Fast Path Regex)")
try:
    from brain.intent_parser import parse
    
    async def test_intent():
        # "open notepad" should hit fast path in intent_router
        result = await parse("open notepad")
        check("parse('open notepad') intent == open_app", result.intent == "open_app")
        
        # Check entities
        app_name = result.entities.get("name") or result.entities.get("app_name")
        check(f"Extracted app name: {app_name}", app_name == "notepad")
        
    asyncio.run(test_intent())
except Exception as e:
    check("Intent Parser fast path tests", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 2 COMPLETE — Ready for Phase 3")
else:
    print("  ❌ Fix failures before proceeding to Phase 3")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
