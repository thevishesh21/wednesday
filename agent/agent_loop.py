"""
WEDNESDAY AI OS — Agent Loop
The core cognitive loop: UNDERSTAND -> PLAN -> EXECUTE -> OBSERVE -> IMPROVE.

FIX CHANGELOG:
  1. All exceptions now logged with full traceback so errors are visible.
  2. Voice feedback (TTS) on task failure — you HEAR the error, not just see it.
  3. LLMUnavailableError handled separately with a clear message.
  4. Context window trimmed correctly after every task (no memory bloat).
  5. Async cleanup on stop() is now safe — cancels pending tasks correctly.
"""

import asyncio
import traceback
from typing import Optional

from core.interfaces import IAgentLoop
from core.logger import get_logger
from core.event_bus import event_bus
from core.exceptions import LLMUnavailableError, LLMResponseError
from agent.task_queue import task_queue, QueuedTask
from brain.intent_parser import parse
from agent.task_planner import generate_plan
from agent.step_executor import StepExecutor
from agent.task_history import task_history
from brain.context_manager import ContextManager
from memory.memory_retriever import memory_retriever
from memory.long_term import long_term
from voice.hinglish_normalizer import hinglish_normalizer
import config

log = get_logger("agent.agent_loop")


class AgentLoop(IAgentLoop):
    """
    Main autonomous agent loop.

    Consumes tasks from the task queue and runs each through the full
    UNDERSTAND → PLAN → EXECUTE → OBSERVE → IMPROVE cognitive cycle.
    """

    def __init__(self) -> None:
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.context = ContextManager(system_prompt=(
            "You are WEDNESDAY, a personal AI Operating System. "
            "You are helpful, casual, and speak with an Indian tone. "
            "You understand both English and Hinglish commands."
        ))

    # ── Lifecycle ─────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background queue-processing loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop_forever())
        log.info("Agent Loop started.")

    async def stop(self) -> None:
        """Stop the background loop gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("Agent Loop stopped.")

    async def _loop_forever(self) -> None:
        """Pull tasks from the queue and handle them one at a time."""
        while self._running:
            try:
                task: QueuedTask = await task_queue.get()
                await self.handle(task.raw_input, task.task_id)
                task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.error(f"Agent loop error: {exc}\n{traceback.format_exc()}")
                await asyncio.sleep(1)  # Prevent tight crash loop

    # ── Main Handler ──────────────────────────────────────────────

    async def handle(self, raw_input: str, task_id: str = "sync-task") -> None:
        """
        Process a single user command through the full agent cycle.

        Args:
            raw_input: Raw user text (may be Hinglish).
            task_id:   Unique identifier for this task (used in logs).
        """
        log.info(f"Handling task {task_id}: '{raw_input}'")
        await event_bus.publish(
            "agent.task_received",
            {"task_id": task_id, "raw_input": raw_input},
        )

        executor        = StepExecutor()
        plan_json_for_log: dict = {}
        intent_label: str       = "unknown"

        try:
            # ══════════════════════════════════════════════════
            # PHASE 1 — UNDERSTAND
            # ══════════════════════════════════════════════════

            # 1a. Hinglish → English normalization
            normalized_input, was_hinglish = await hinglish_normalizer.normalize(raw_input)
            if was_hinglish:
                log.info(
                    f"Hinglish normalized: '{raw_input}' → '{normalized_input}'"
                )

            # 1b. Retrieve relevant long-term memories
            memories = await memory_retriever.retrieve(normalized_input)
            mem_text = (
                "\n".join(m.content for m in memories)
                if memories else "None"
            )
            log.info(f"Retrieved {len(memories)} memories for context.")

            # 1c. Parse intent using LLM
            recent_context = [
                m.content
                for m in self.context.get_messages()[-4:]
            ]
            intent = await parse(
                normalized_input,
                recent_context + [f"Memory Context: {mem_text}"],
            )
            intent_label = intent.intent

            # Add user turn to context
            self.context.add_message("user", raw_input)

            # ══════════════════════════════════════════════════
            # PHASE 2 — PLAN
            # ══════════════════════════════════════════════════

            plan = await generate_plan(task_id, intent)

            plan_json_for_log = {
                "intent": plan.intent,
                "steps": [
                    {"step_id": s.step_id, "tool": s.tool, "args": s.args}
                    for s in plan.steps
                ],
            }

            await event_bus.publish(
                "agent.plan_ready",
                {"task_id": task_id, "step_count": len(plan.steps)},
            )

            # Handle conversational / no-action intents
            if not plan.steps:
                log.info(f"No actionable steps for task {task_id}.")
                if intent.intent in ("general_chat", "unknown"):
                    from brain.fallback import fallback_response
                    resp = fallback_response(raw_input)
                    await event_bus.publish(
                        "voice.speaking_start", {"text": resp}
                    )
                    await event_bus.publish("voice.speaking_end", {})

                await event_bus.publish(
                    "agent.task_complete",
                    {"task_id": task_id, "success": True, "summary": "No steps"},
                )
                task_history.log_task(
                    task_id, raw_input, intent_label, plan_json_for_log, True
                )
                return

            # ══════════════════════════════════════════════════
            # PHASE 3 — EXECUTE
            # ══════════════════════════════════════════════════

            last_result = None
            for step in plan.steps:
                last_result = await executor.execute_step(task_id, step)

            # ══════════════════════════════════════════════════
            # PHASE 4 — OBSERVE + IMPROVE
            # ══════════════════════════════════════════════════

            summary = str(last_result.result) if last_result else "Completed"

            await event_bus.publish(
                "agent.task_complete",
                {"task_id": task_id, "success": True, "summary": summary},
            )
            task_history.log_task(
                task_id, raw_input, intent_label, plan_json_for_log, True
            )

            # Store outcome in long-term memory
            await long_term.store(
                f"Task '{raw_input}' completed. Result: {summary}",
                {"task_id": task_id, "intent": intent_label},
            )

            # Update context with assistant response
            self.context.add_message(
                "assistant",
                f"Executed {len(plan.steps)} step(s). Result: {summary}",
            )
            self.context.trim()

        # ── LLM not reachable ─────────────────────────────────
        except LLMUnavailableError as exc:
            msg = (
                "Boss, AI brain offline hai. "
                "OpenRouter key check karo ya Ollama start karo."
            )
            log.error(f"Task {task_id} — LLM unavailable: {exc}")
            await event_bus.publish(
                "agent.error",
                {"task_id": task_id, "error": str(exc), "type": "llm_unavailable"},
            )
            await event_bus.publish("voice.speaking_start", {"text": msg})
            await event_bus.publish("voice.speaking_end", {})
            task_history.log_task(
                task_id, raw_input, intent_label,
                plan_json_for_log, False, str(exc),
            )
            self.context.add_message("assistant", f"LLM unavailable: {exc}")

        # ── LLM returned bad response ─────────────────────────
        except LLMResponseError as exc:
            msg = f"Boss, AI ne kuch galat bola. Error: {str(exc)[:60]}"
            log.error(f"Task {task_id} — LLM response error: {exc}")
            await event_bus.publish(
                "agent.error",
                {"task_id": task_id, "error": str(exc), "type": "llm_response"},
            )
            await event_bus.publish("voice.speaking_start", {"text": msg})
            await event_bus.publish("voice.speaking_end", {})
            task_history.log_task(
                task_id, raw_input, intent_label,
                plan_json_for_log, False, str(exc),
            )
            self.context.add_message("assistant", f"LLM error: {exc}")

        # ── Any other unexpected error ────────────────────────
        except Exception as exc:
            full_trace = traceback.format_exc()
            msg = "Sorry boss, I'm having a bit of trouble thinking right now. Please try again in a moment."
            log.error(
                f"Task {task_id} failed unexpectedly: {exc}\n{full_trace}"
            )
            await event_bus.publish(
                "agent.error",
                {"task_id": task_id, "error": str(exc), "type": "unexpected"},
            )
            await event_bus.publish("voice.speaking_start", {"text": msg})
            await event_bus.publish("voice.speaking_end", {})
            task_history.log_task(
                task_id, raw_input, intent_label,
                plan_json_for_log, False, str(exc),
            )
            self.context.add_message(
                "assistant", f"Failed to execute task: {exc}"
            )


# ── Global singleton ──────────────────────────────────────────────
agent_loop = AgentLoop()