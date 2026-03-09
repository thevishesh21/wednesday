"""
Wednesday - Personal AI Desktop Assistant
Main entry point.
"""

import sys
import os
import threading
import queue
import time
import logging

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from state import app_state, AssistantState
from brain.ai_brain import AIBrain
from brain.memory import ShortTermMemory, LongTermMemory
from brain.context import extract_facts, is_recall_query
from brain.personality_engine import PersonalityEngine
from brain.task_parser import TaskParser
from brain.context_memory import ContextMemory
from audio.listener import Listener
from audio.speaker import Speaker
from wake_word.detector import WakeWordDetector
from router.command_router import CommandRouter
from security.confirmations import ConfirmationManager
from skills import system_control, app_control, web_actions, file_control
from skills import clipboard, communication, reminders
from skills import screen_awareness, contact_manager, dictation, workflows
import plugins


logger = logging.getLogger("Wednesday")


class WednesdayAssistant:
    """Core assistant orchestrator."""

    def __init__(self, gui_signals=None):
        self.gui_signals = gui_signals
        self.speaker = Speaker()
        self.listener = Listener()
        self.wake_detector = WakeWordDetector()
        self.router = CommandRouter()
        self.brain = AIBrain()
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory()
        self.confirmations = ConfirmationManager()
        self.personality = PersonalityEngine()
        self.task_parser = TaskParser()
        self.context = ContextMemory()
        self._awake = False
        self._input_queue = queue.Queue()
        self._gui_input = False

        # Load plugins at startup
        plugins.load_plugins()

        logger.info("Wednesday Assistant initialized.")

    def start(self):
        """Start the assistant: greet and enter main loop."""
        self._greet()
        self._awake = True
        self._set_state(AssistantState.LISTENING)
        self._main_loop()

    def _greet(self):
        """Speak the greeting message."""
        logger.info("Speaking greeting.")
        self._set_state(AssistantState.SPEAKING)
        self._update_response(config.GREETING)
        self.speaker.speak(config.GREETING)

    def _main_loop(self):
        """Continuously listen and process commands."""
        while app_state.running:
            if not self._awake:
                self._set_state(AssistantState.SLEEPING)
                text = self._listen_quietly()
                if not text:
                    continue

                # Auto-wake on GUI text input (no wake word needed)
                if self._gui_input:
                    self._awake = True
                    self._set_state(AssistantState.LISTENING)
                    self._process_command(text)
                    continue

                if self.wake_detector.is_wake_word(text):
                    self._awake = True
                    remainder = self.wake_detector.strip_wake_word(text)
                    self._set_state(AssistantState.LISTENING)
                    greeting = self.personality.style_response("", "greeting")
                    self._update_response(greeting)
                    self.speaker.speak(greeting)
                    if remainder:
                        self._process_command(remainder)
                continue

            self._set_state(AssistantState.LISTENING)
            text = self._listen()

            if not text:
                continue

            if self.wake_detector.is_sleep_command(text):
                self._awake = False
                response = self.personality.style_response("", "farewell")
                self._update_response(response)
                self._set_state(AssistantState.SPEAKING)
                self.speaker.speak(response)
                continue

            self._process_command(text)

    def _process_command(self, text):
        """Process a single user command (may contain multi-step tasks)."""
        # Only emit transcript for mic input; GUI input is already in the chat
        if not self._gui_input:
            self._update_transcript(text)

        # --- Dictation mode: type everything into the active window ---
        if self.context.is_dictating:
            if text.lower().strip() in ("stop dictation", "end dictation", "stop typing"):
                self.context.is_dictating = False
                response = self.personality.style_response("Dictation stopped.", "done")
                self._respond(response)
                return
            result = dictation.type_text(text)
            return  # Don't speak during dictation

        # --- Pending confirmation ---
        if self.confirmations.has_pending():
            confirmed = self.confirmations.confirm(text)
            if confirmed:
                response = self._execute_action(confirmed["action"], {})
                response = self.personality.style_response(response, "done")
            else:
                response = "Cancelled."
            self._respond(response)
            return

        # --- Recall stored facts ---
        recall_key = is_recall_query(text)
        if recall_key:
            value = self.long_memory.get_fact(recall_key)
            if value:
                response = "Your {} is {}.".format(recall_key, value)
            else:
                response = "I do not know your {} yet.".format(recall_key)
            self._respond(response)
            return

        # --- Extract and store personal facts ---
        facts = extract_facts(text)
        for key, value in facts.items():
            self.long_memory.store_fact(key, value)

        # --- Multi-step task parsing ---
        tasks = self.task_parser.parse(text)

        if len(tasks) > 1:
            # Multi-step: process each sub-command sequentially
            all_responses = []
            for sub_cmd in tasks:
                resp = self._execute_single_command(sub_cmd)
                if resp:
                    all_responses.append(resp)
                time.sleep(0.5)  # brief pause between steps

            combined = " ".join(all_responses) if all_responses else "Sorry, I could not process that."
            styled = self.personality.style_response(combined, "done")
            self.short_memory.add_exchange(text, styled)
            self.context.record_command(text, styled)
            self._respond(styled)
        else:
            # Single command
            response = self._execute_single_command(text)
            if not response:
                response = "Sorry, I could not process that."
            self.short_memory.add_exchange(text, response)
            self.context.record_command(text, response)
            self._respond(response)

    def _execute_single_command(self, text):
        """Route and execute a single command, return styled response."""
        route = self.router.route(text)

        if route["type"] == "skill":
            action = route["action"]
            if self.confirmations.needs_confirmation(action):
                description = action.replace("_", " ")
                return self.personality.confirm_prompt(description)
            raw = self._execute_skill(route)
            return self.personality.style_response(raw, "action")
        else:
            self._set_state(AssistantState.THINKING)
            ctx_parts = []
            mem_context = self.long_memory.get_context_string()
            if mem_context:
                ctx_parts.append(mem_context)
            session_ctx = self.context.get_summary()
            if session_ctx:
                ctx_parts.append(session_ctx)
            context = "; ".join(ctx_parts)
            response = self.brain.ask(text, context=context)
            return response or "Sorry, I could not generate a response."

    def _execute_skill(self, route):
        """Execute a skill based on the route."""
        skill_name = route["skill"]
        action = route["action"]
        params = route.get("params", {})
        query = params.get("query", "")

        self._set_state(AssistantState.THINKING)

        try:
            if skill_name == "system_control":
                return self._execute_action(action, params)
            elif skill_name == "app_control":
                self.context.record_app(query)
                return app_control.open_app(query)
            elif skill_name == "web_actions":
                return self._execute_web_action(action, query)
            elif skill_name == "file_control":
                return self._execute_file_action(action, query)
            elif skill_name == "clipboard":
                return self._execute_clipboard_action(action)
            elif skill_name == "communication":
                return communication.send_email(to=query)
            elif skill_name == "reminders":
                return self._execute_reminder_action(action, query)
            elif skill_name == "screen_awareness":
                return screen_awareness.analyze_screen(query or "Describe what is on the screen.")
            elif skill_name == "dictation":
                return self._execute_dictation_action(action)
            elif skill_name == "workflows":
                return workflows.run_workflow(query)
            elif skill_name == "contact_manager":
                return self._execute_contact_action(action, query)
            else:
                return "I do not know how to handle {} yet.".format(skill_name)
        except Exception as e:
            return "Error executing command: {}".format(e)

    def _execute_action(self, action, params):
        """Execute a system control action."""
        actions = {
            "shutdown": system_control.shutdown,
            "restart": system_control.restart,
            "sleep": system_control.sleep,
            "lock": system_control.lock,
            "volume_up": system_control.volume_up,
            "volume_down": system_control.volume_down,
            "mute": system_control.mute,
            "brightness_up": system_control.brightness_up,
            "brightness_down": system_control.brightness_down,
            "open_task_manager": system_control.open_task_manager,
            "empty_recycle_bin": system_control.empty_recycle_bin,
        }
        fn = actions.get(action)
        if fn:
            return fn()
        return "Unknown action: {}".format(action)

    def _execute_web_action(self, action, query):
        if action in ("google_search", "open_youtube", "youtube_search"):
            self.context.record_search(query)
        if action == "open_website":
            self.context.record_website(query)
        actions = {
            "google_search": lambda: web_actions.google_search(query),
            "open_youtube": lambda: web_actions.open_youtube(),
            "youtube_search": lambda: web_actions.youtube_search(query),
            "open_website": lambda: web_actions.open_website(query),
        }
        fn = actions.get(action)
        return fn() if fn else "Unknown web action: {}".format(action)

    def _execute_file_action(self, action, query):
        self.context.record_file(query)
        actions = {
            "create_file": lambda: file_control.create_file(query),
            "open_file": lambda: file_control.open_file(query),
            "delete_file": lambda: file_control.delete_file(query),
            "rename_file": lambda: file_control.rename_file(query),
            "find_file": lambda: file_control.find_file(query),
            "open_folder": lambda: file_control.open_folder(query),
        }
        fn = actions.get(action)
        return fn() if fn else "Unknown file action: {}".format(action)

    def _execute_clipboard_action(self, action):
        actions = {
            "read_clipboard": lambda: clipboard.read_clipboard(),
            "summarize_clipboard": lambda: clipboard.summarize_clipboard(ai_brain=self.brain),
            "explain_clipboard": lambda: clipboard.explain_clipboard(ai_brain=self.brain),
            "rewrite_clipboard": lambda: clipboard.rewrite_clipboard(ai_brain=self.brain),
            "translate_clipboard": lambda: clipboard.translate_clipboard(ai_brain=self.brain),
        }
        fn = actions.get(action)
        return fn() if fn else "Unknown clipboard action."

    def _execute_reminder_action(self, action, query):
        if action == "set_reminder":
            return reminders.set_reminder(query)
        elif action == "list_reminders":
            return reminders.list_reminders()
        return "Unknown reminder action."

    def _execute_dictation_action(self, action):
        if action == "start_dictation":
            self.context.is_dictating = True
            return "Dictation mode started. I will type what you say. Say stop dictation to end."
        elif action == "stop_dictation":
            self.context.is_dictating = False
            return "Dictation mode stopped."
        return "Unknown dictation action."

    def _execute_contact_action(self, action, query):
        self.context.record_contact(query)
        if action == "list_contacts":
            return contact_manager.list_contacts()
        elif action == "find_contact":
            result = contact_manager.find_contact(query)
            return f"{query}: {result}" if result else f"No contact found for '{query}'."
        elif action == "add_contact":
            # For add, query would be "name value" but we need more info
            # Just store the name for now and inform user
            return f"To add a contact, say: add contact name email@example.com"
        elif action == "remove_contact":
            return contact_manager.remove_contact(query)
        elif action == "send_email_to_contact":
            return contact_manager.send_email_to_contact(query)
        return "Unknown contact action."

    def _respond(self, text):
        """Send response to user via TTS and GUI."""
        self._update_response(text)
        self._set_state(AssistantState.SPEAKING)
        self.speaker.speak(text)
        self._set_state(AssistantState.LISTENING)

    def submit_text(self, text):
        """Accept text input from the GUI."""
        self._input_queue.put(text)

    def _get_input(self) -> str | None:
        """Get input from GUI text box or microphone."""
        # Check GUI queue first (non-blocking)
        try:
            text = self._input_queue.get_nowait()
            if text:
                self._gui_input = True
                return text
        except queue.Empty:
            pass

        if self.listener.has_mic:
            # Try microphone (blocks for LISTEN_TIMEOUT)
            self._gui_input = False
            return self.listener.listen()
        else:
            # No mic — wait on GUI queue with short timeout
            try:
                self._gui_input = True
                return self._input_queue.get(timeout=0.5)
            except queue.Empty:
                return None

    def _listen(self):
        """Listen for a command via GUI or microphone."""
        return self._get_input()

    def _listen_quietly(self):
        """Listen for wake word via GUI or microphone."""
        return self._get_input()

    def _set_state(self, state):
        app_state.state = state
        if self.gui_signals:
            state_map = {
                AssistantState.SLEEPING: "sleeping",
                AssistantState.LISTENING: "listening",
                AssistantState.THINKING: "thinking",
                AssistantState.SPEAKING: "speaking",
                AssistantState.ERROR: "error",
            }
            try:
                self.gui_signals.state_changed.emit(state_map.get(state, "sleeping"))
            except RuntimeError:
                pass

    def _update_transcript(self, text):
        if self.gui_signals:
            try:
                self.gui_signals.transcript_update.emit(text)
            except RuntimeError:
                pass

    def _update_response(self, text):
        if self.gui_signals:
            try:
                self.gui_signals.response_update.emit(text)
            except RuntimeError:
                pass


def run():
    """Launch the Wednesday assistant with GUI."""
    from PySide6.QtWidgets import QApplication
    from gui.app import WednesdayWindow

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Wednesday")

    window = WednesdayWindow()
    window.show()

    assistant = WednesdayAssistant(gui_signals=window.signals)

    # Wire GUI text input to assistant
    window.signals.text_submitted.connect(assistant.submit_text)

    # Wire MIC button to wake assistant from sleep
    def on_mic_clicked():
        if not assistant._awake:
            assistant._awake = True

    window.signals.mic_clicked.connect(on_mic_clicked)

    def assistant_thread():
        try:
            assistant.start()
        except Exception as e:
            logger.error("Assistant error: %s", e, exc_info=True)

    thread = threading.Thread(target=assistant_thread, daemon=True)
    thread.start()

    def on_quit():
        app_state.running = False

    qt_app.aboutToQuit.connect(on_quit)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    run()
