"""
Wednesday - Personal AI Desktop Assistant
Main entry point.
"""

import sys
import os
import threading
import time
import logging

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from state import app_state, AssistantState
from brain.ai_brain import AIBrain
from brain.memory import ShortTermMemory, LongTermMemory
from brain.context import extract_facts, is_recall_query
from audio.listener import Listener
from audio.speaker import Speaker
from wake_word.detector import WakeWordDetector
from router.command_router import CommandRouter
from security.confirmations import ConfirmationManager
from skills import system_control, app_control, web_actions, file_control
from skills import clipboard, communication, reminders


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
        self._awake = False
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
                if text and self.wake_detector.is_wake_word(text):
                    self._awake = True
                    remainder = self.wake_detector.strip_wake_word(text)
                    self._set_state(AssistantState.LISTENING)
                    self._update_response("I am listening.")
                    self.speaker.speak("I am listening.")
                    if remainder:
                        self._process_command(remainder)
                continue

            self._set_state(AssistantState.LISTENING)
            text = self._listen()

            if not text:
                continue

            if self.wake_detector.is_sleep_command(text):
                self._awake = False
                response = "Going to sleep. Say Hey Wednesday to wake me up."
                self._update_response(response)
                self._set_state(AssistantState.SPEAKING)
                self.speaker.speak(response)
                continue

            self._process_command(text)

    def _process_command(self, text):
        """Process a single user command."""
        self._update_transcript(text)

        if self.confirmations.has_pending():
            confirmed = self.confirmations.confirm(text)
            if confirmed:
                response = self._execute_action(confirmed["action"], {})
            else:
                response = "Cancelled."
            self._respond(response)
            return

        recall_key = is_recall_query(text)
        if recall_key:
            value = self.long_memory.get_fact(recall_key)
            if value:
                response = "Your {} is {}.".format(recall_key, value)
            else:
                response = "I do not know your {} yet.".format(recall_key)
            self._respond(response)
            return

        facts = extract_facts(text)
        for key, value in facts.items():
            self.long_memory.store_fact(key, value)

        route = self.router.route(text)

        if route["type"] == "skill":
            action = route["action"]
            if self.confirmations.needs_confirmation(action):
                description = action.replace("_", " ")
                prompt = self.confirmations.request_confirmation(action, description)
                self._respond(prompt)
                return
            response = self._execute_skill(route)
        else:
            self._set_state(AssistantState.THINKING)
            context = self.long_memory.get_context_string()
            response = self.brain.ask(text, context=context)

        self.short_memory.add_exchange(text, response)
        self._respond(response)

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
        }
        fn = actions.get(action)
        if fn:
            return fn()
        return "Unknown action: {}".format(action)

    def _execute_web_action(self, action, query):
        actions = {
            "google_search": lambda: web_actions.google_search(query),
            "open_youtube": lambda: web_actions.open_youtube(),
            "youtube_search": lambda: web_actions.youtube_search(query),
            "open_website": lambda: web_actions.open_website(query),
        }
        fn = actions.get(action)
        return fn() if fn else "Unknown web action: {}".format(action)

    def _execute_file_action(self, action, query):
        actions = {
            "create_file": lambda: file_control.create_file(query),
            "open_file": lambda: file_control.open_file(query),
            "delete_file": lambda: file_control.delete_file(query),
        }
        fn = actions.get(action)
        return fn() if fn else "Unknown file action: {}".format(action)

    def _execute_clipboard_action(self, action):
        if action == "read_clipboard":
            return clipboard.read_clipboard()
        elif action == "summarize_clipboard":
            return clipboard.summarize_clipboard(ai_brain=self.brain)
        return "Unknown clipboard action."

    def _execute_reminder_action(self, action, query):
        if action == "set_reminder":
            return reminders.set_reminder(query)
        elif action == "list_reminders":
            return reminders.list_reminders()
        return "Unknown reminder action."

    def _respond(self, text):
        """Send response to user via TTS and GUI."""
        self._update_response(text)
        self._set_state(AssistantState.SPEAKING)
        self.speaker.speak(text)
        self._set_state(AssistantState.LISTENING)

    def _listen(self):
        """Listen for a command with full timeout."""
        return self.listener.listen()

    def _listen_quietly(self):
        """Listen for wake word."""
        return self.listener.listen()

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
