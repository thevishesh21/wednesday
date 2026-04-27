"""
Wednesday AI Assistant — Main Entry Point
Integrates all 9 phases: Voice, Tools, AI Brain, Executor,
Vision, Memory, Reminders, Proactive Conversation, Gesture Control.

Usage:
    python main.py
"""

import sys
import random
from utils.logger import get_logger
from voice.speaker import speak, greet, is_tts_available
from voice.listener import listen, is_mic_available, check_microphone
from voice.wake_word import is_wake_word, strip_wake_word
from brain.intent_router import route as intent_route
from brain.planner import plan_task
from brain.fallback import fallback_response
from brain.conversation import update_interaction, conversation_loop
from executor.executor import run_plan
from tools import registry
from tools.app_launcher import open_app, close_app
from tools.browser import open_website, search_google, search_youtube
from tools.automation import (type_text, hotkey, press_key, mouse_click,
                              move_mouse, scroll, screenshot_position)
from tools.file_manager import create_file, read_file, delete_file, list_files
from vision.screenshot import take_screenshot
from vision.ocr import read_screen_text, is_ocr_available
from memory.memory import save as mem_save, recall as mem_recall, list_all as mem_list, forget as mem_forget
from reminders.reminder import (parse_reminder_command, list_reminders,
                                clear_reminders, reminder_loop)
from gesture.gesture_mapper import gesture_loop
from utils.thread_manager import thread_manager
from state import state
import config

log = get_logger("main")

# ── Natural response templates ──────────────────────────────────
_NO_COMMAND = [
    "Boss, kuch suna nahi. Ek baar phir bolo na?",
    "Arre, kuch bola nahi aapne! Dubara try karo, boss.",
    "Main sun rahi thi, par kuch catch nahi hua. Phir se boliye?",
]


# ═════════════════════════════════════════════════════════════════
#  Tool Registration  (runs once at startup)
# ═════════════════════════════════════════════════════════════════

def _register_all_tools() -> None:
    """Register every tool in the system with the central registry."""

    # ── App Launcher ─────────────────────────────────────────
    registry.register("open_app", open_app, ["name"],
                      description="Open a desktop application")
    registry.register("close_app", close_app, ["name"], dangerous=True,
                      description="Close an application")

    # ── Browser ──────────────────────────────────────────────
    registry.register("open_website", open_website, ["url"],
                      description="Open a website")
    registry.register("search_google", search_google, ["query"],
                      description="Search Google")
    registry.register("search_youtube", search_youtube, ["query"],
                      description="Search YouTube")

    # ── Automation ───────────────────────────────────────────
    registry.register("type_text", type_text, ["text"],
                      description="Type text via keyboard")
    registry.register("hotkey", hotkey, [], dangerous=True,
                      description="Press keyboard shortcut")
    registry.register("press_key", press_key, ["key"], dangerous=True,
                      description="Press a key")
    registry.register("mouse_click", mouse_click, [],
                      description="Click the mouse")
    registry.register("move_mouse", move_mouse, ["x", "y"],
                      description="Move mouse cursor")
    registry.register("scroll", scroll, ["amount"],
                      description="Scroll up/down")
    registry.register("screenshot_position", screenshot_position, [],
                      description="Get mouse position")

    # ── File Manager ─────────────────────────────────────────
    registry.register("create_file", create_file, ["path"],
                      description="Create a file")
    registry.register("read_file", read_file, ["path"],
                      description="Read a file")
    registry.register("delete_file", delete_file, ["path"], dangerous=True,
                      description="Delete a file")
    registry.register("list_files", list_files, [],
                      description="List files in directory")

    # ── Vision ───────────────────────────────────────────────
    registry.register("take_screenshot", take_screenshot, [],
                      description="Take a screenshot")
    registry.register("read_screen_text", read_screen_text, [],
                      description="Read text from screen via OCR")

    # ── Memory ───────────────────────────────────────────────
    registry.register("mem_save", mem_save, ["key", "value"],
                      description="Save to memory")
    registry.register("mem_recall", mem_recall, ["key"],
                      description="Recall from memory")
    registry.register("mem_list", mem_list, [],
                      description="List all memory items")
    registry.register("mem_forget", mem_forget, ["key"],
                      description="Forget a memory item")

    # ── Reminders ────────────────────────────────────────────
    registry.register("set_reminder", parse_reminder_command, ["command"],
                      description="Set a reminder")
    registry.register("list_reminders", list_reminders, [],
                      description="List pending reminders")
    registry.register("clear_reminders", clear_reminders, [],
                      description="Clear all reminders")

    # ── Speak response (used by planner/fallback) ────────────
    registry.register("speak_response", speak, ["text"],
                      description="Speak a response")

    count = len(registry.list_tools())
    log.info(f"✅ {count} tools registered.")


# ═════════════════════════════════════════════════════════════════
#  Command Processing Pipeline
# ═════════════════════════════════════════════════════════════════

def process_command(command: str) -> None:
    """
    Full command processing pipeline:
    1. Check built-in commands (memory, reminders, vision, gesture)
    2. Try intent router shortcuts (O(1) keyword matching)
    3. Try AI planner (LLM-based multi-step planning)
    4. Fall back to rule-based engine
    """
    log.info(f"Processing: {command}")
    update_interaction()

    # ── 1. Built-in commands (bypass everything) ─────────────
    handled = _handle_builtin(command)
    if handled:
        state.update(command, tool="builtin", result=handled)
        return

    # ── 1.5 AI Agent Loop (Phase 4) ──────────────────────────
    try:
        from agent.agent_loop import agent_loop
        import asyncio
        # Run the async handle method synchronously for now
        # until the whole system becomes async in later phases
        asyncio.run(agent_loop.handle(command))
        return
    except Exception as e:
        log.warning(f"Agent loop failed: {e}. Falling back to legacy routing.")

    # ── 2. Intent router shortcuts ───────────────────────────
    steps = intent_route(command)
    if steps:
        speak("Working on it, boss!")
        results = run_plan(steps)
        _report_results(results)
        tool_name = steps[0].get("tool", "")
        state.update(command, tool=tool_name,
                     result=str(results[-1].get("result", "")))
        return

    # ── 3. AI planner (if API keys configured) ───────────────
    if config.OPENROUTER_API_KEY or config.HUGGINGFACE_API_KEY:
        speak("Soch rahi hoon, boss...")
        plan = plan_task(command)

        if "steps" in plan:
            results = run_plan(plan["steps"])
            _report_results(results)
            state.update(command, tool="ai_plan", result="executed")
            return
        elif "speak" in plan:
            speak(plan["speak"])
            state.update(command, tool="ai_brain", result=plan["speak"])
            return

    # ── 4. Rule-based fallback ───────────────────────────────
    fb = fallback_response(command)
    if "steps" in fb:
        results = run_plan(fb["steps"])
        _report_results(results)
        state.update(command, tool="fallback", result="executed")
    elif "speak" in fb:
        speak(fb["speak"])
        state.update(command, tool="fallback", result=fb["speak"])


def _handle_builtin(command: str) -> str | None:
    """Handle built-in commands that don't need routing."""
    cmd = command.lower().strip()

    # ── Memory commands ──────────────────────────────────────
    if cmd.startswith("remember") or cmd.startswith("yaad rakh"):
        # Parse "remember my name is Vishesh" → key=name, value=Vishesh
        parts = cmd.replace("remember", "").replace("yaad rakh", "").strip()
        if " is " in parts:
            key, value = parts.split(" is ", 1)
            result = mem_save(key.strip(), value.strip())
            speak(result)
            return result
        elif " hai " in parts:
            key, value = parts.split(" hai ", 1)
            result = mem_save(key.strip(), value.strip())
            speak(result)
            return result

    if cmd.startswith("what is my") or cmd.startswith("mera "):
        key = cmd.replace("what is my", "").replace("mera ", "").replace("kya hai", "").strip()
        result = mem_recall(key)
        speak(result)
        return result

    if cmd == "list memory" or cmd == "memory list":
        result = mem_list()
        speak(result)
        return result

    # ── Reminder commands ────────────────────────────────────
    if "remind" in cmd:
        result = parse_reminder_command(cmd)
        speak(result)
        return result

    if cmd in ["list reminders", "show reminders", "pending reminders"]:
        result = list_reminders()
        speak(result)
        return result

    if cmd in ["clear reminders", "delete reminders"]:
        result = clear_reminders()
        speak(result)
        return result

    # ── Vision commands ──────────────────────────────────────
    if cmd in ["take screenshot", "screenshot", "screen capture"]:
        speak("Screenshot le rahi hoon, boss!")
        result = take_screenshot()
        speak(f"Done! Saved: {result}")
        return result

    if cmd in ["read screen", "screen text", "ocr", "what is on my screen"]:
        speak("Screen padh rahi hoon, boss...")
        result = read_screen_text()
        speak(result)
        return result

    # ── Gesture control toggle ───────────────────────────────
    if cmd in ["start gesture", "gesture on", "hand control on"]:
        if not thread_manager.is_running("gesture"):
            thread_manager.start("gesture")
            speak("Gesture control ON, boss! Haath se mouse chalao!")
            return "gesture started"
        speak("Gesture control already running, boss!")
        return "already running"

    if cmd in ["stop gesture", "gesture off", "hand control off"]:
        thread_manager.stop("gesture")
        speak("Gesture control OFF, boss!")
        return "gesture stopped"

    # ── System info ──────────────────────────────────────────
    if cmd in ["list tools", "available tools", "what can you do"]:
        tools = registry.list_tools()
        speak(f"Boss, mere paas {len(tools)} tools hain: {', '.join(tools[:10])}")
        return f"{len(tools)} tools"

    if cmd in ["status", "thread status"]:
        status = thread_manager.status()
        info = " | ".join([f"{k}: {'✅' if v else '❌'}" for k, v in status.items()])
        speak(f"Thread status: {info}")
        return info

    return None  # Not a built-in


def _report_results(results: list[dict]) -> None:
    """Speak a summary of execution results — never fake success."""
    if not results:
        speak("Kuch execute nahi ho paaya, boss.")
        return

    success = sum(1 for r in results if r.get("success"))
    total = len(results)

    for r in results:
        log.info(f"[DEBUG] Tool result: success={r.get('success')} | output={r.get('result', r.get('error', 'None'))}")

    if total == 1:
        r = results[0]
        if r["success"]:
            # Double-check the result text isn't a failure message
            result_text = str(r.get("result", ""))
            if result_text.startswith("FAILED:"):
                speak("Sorry boss, I couldn't complete that.")
            else:
                speak(f"Done! {result_text}")
        else:
            speak("Sorry boss, I couldn't complete that.")
    elif success == total:
        speak(f"Sab {total} steps complete, boss!")
    elif success > 0:
        speak(f"{success}/{total} steps done. Kuch fail ho gaye, boss.")
    else:
        speak("Sorry boss, I couldn't complete that.")


# ═════════════════════════════════════════════════════════════════
#  Startup Health Checks
# ═════════════════════════════════════════════════════════════════

def startup_checks() -> None:
    """Run diagnostics before entering the main loop."""
    log.info("=" * 55)
    log.info(f"  {config.ASSISTANT_NAME} AI Assistant — Booting Up")
    log.info("=" * 55)

    # TTS
    log.info(f"{'✅' if is_tts_available() else '⚠️'} TTS engine     : "
             f"{'OK' if is_tts_available() else 'FAILED (console mode)'}")

    # Microphone
    if is_mic_available():
        mic_info = check_microphone()
        count = len(mic_info.get("devices", []))
        log.info(f"✅ Microphone      : OK ({count} device(s))")
    else:
        log.warning("⚠️  Microphone      : NOT FOUND (text mode)")

    # Input mode
    mode_map = {
        "voice": "🎤 Voice",
        "text": "⌨️  Text",
        "auto": "🎤 Voice (⌨️ fallback)" if is_mic_available() else "⌨️  Text (auto)",
    }
    log.info(f"📡 Input mode     : {mode_map.get(config.INPUT_MODE, config.INPUT_MODE)}")

    # AI Brain
    ai_status = "configured" if (config.OPENROUTER_API_KEY or config.HUGGINGFACE_API_KEY) else "offline (fallback mode)"
    log.info(f"🧠 AI Brain       : {ai_status}")

    # OCR
    log.info(f"{'✅' if is_ocr_available() else '⚠️'} OCR (Tesseract) : "
             f"{'available' if is_ocr_available() else 'not installed'}")

    # Tools
    tool_count = len(registry.list_tools())
    log.info(f"🔧 Tools loaded   : {tool_count}")

    log.info("-" * 55)
    log.info(f"  Say '{config.WAKE_WORD}' or type it to activate!")
    log.info("-" * 55)


# ═════════════════════════════════════════════════════════════════
#  Background Thread Setup
# ═════════════════════════════════════════════════════════════════

def _start_background_threads() -> None:
    """Register and start all background loops."""
    # Reminder loop
    thread_manager.register("reminder", reminder_loop)
    thread_manager.start("reminder")

    # Proactive conversation loop
    if config.PROACTIVE_ENABLED:
        thread_manager.register("conversation", conversation_loop)
        thread_manager.start("conversation")

    # Gesture control (registered but NOT started — user activates via voice)
    thread_manager.register("gesture", gesture_loop)

    log.info(f"Background threads: {thread_manager.status()}")


# ═════════════════════════════════════════════════════════════════
#  Main Voice Loop
# ═════════════════════════════════════════════════════════════════

def main():
    """
    Main entry point:
    1. Register tools  →  2. Run health checks  →  3. Start threads
    4. Enter voice/text loop  →  5. Process commands
    """
    # ── Boot up ──────────────────────────────────────────────
    _register_all_tools()
    startup_checks()
    _start_background_threads()

    speak(f"Hello boss! {config.ASSISTANT_NAME} is online. "
          f"Say '{config.WAKE_WORD}' to activate!")

    while True:
        try:
            # ── Listen for wake word ─────────────────────────
            text = listen()

            if not text:
                continue

            # ── Check wake word ──────────────────────────────
            if is_wake_word(text):
                greet()
                update_interaction()

                # Extract command from wake word phrase
                command = strip_wake_word(text)

                if not command:
                    speak("Bataiye boss, kya karna hai?")
                    command = listen(timeout=8, phrase_limit=15)

                if command:
                    process_command(command)
                else:
                    speak(random.choice(_NO_COMMAND))

            else:
                log.debug(f"Ignored (no wake word): {text}")

        except KeyboardInterrupt:
            shutdown()
        except Exception as e:
            log.error(f"Main loop error: {e}")
            speak("Kuch gadbad ho gayi, boss. Phir se try karti hoon.")
            continue


def shutdown():
    """Graceful shutdown — stop all threads and exit."""
    log.info("Shutting down...")
    thread_manager.stop_all()
    speak("Bye boss! Wednesday signing off. 😊")
    log.info("Wednesday stopped.")


# ═════════════════════════════════════════════════════════════════
#  GUI Mode  (JARVIS interface — default)
# ═════════════════════════════════════════════════════════════════

def main_gui():
    """
    Launch the JARVIS-style GUI.
    Boots backend (tools, health checks, threads) then opens the
    PyQt6 window.  The GUI drives voice + commands via its own
    worker threads; the CLI loop is NOT started.
    """
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFont
    except ImportError:
        log.error("PyQt6 not installed. Run:  pip install PyQt6")
        log.info("Falling back to CLI mode...")
        main()
        return

    # 1. Boot backend
    _register_all_tools()
    startup_checks()
    _start_background_threads()

    # 2. Patch speak() so it emits to the GUI chat panel
    from gui.bridge import AssistantBridge
    bridge = AssistantBridge.instance()
    bridge.patch_backend()

    # 3. Launch Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Wednesday AI")
    app.setFont(QFont("Segoe UI", 12))

    from gui.app import WednesdayGUI
    window = WednesdayGUI()
    window.show()

    log.info("GUI launched — JARVIS mode active.")
    exit_code = app.exec()

    # 4. Clean shutdown when window is closed
    shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    if "--cli" in sys.argv:
        main()          # Original terminal voice loop
    else:
        main_gui()      # JARVIS GUI (default)
