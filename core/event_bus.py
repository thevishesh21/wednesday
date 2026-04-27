"""
WEDNESDAY AI OS — Async Event Bus
Central pub/sub message bus. Every module communicates through events.

This is the nervous system of WEDNESDAY — it replaces the fragile
gui/bridge.py monkey-patch with a clean, testable, thread-safe bus.

Usage:
    # Subscribe (in any module)
    from core.event_bus import event_bus
    event_bus.subscribe("agent.task_complete", my_handler)

    # Publish async (in async context)
    await event_bus.publish("agent.task_complete", {"task_id": "...", "success": True})

    # Publish sync (from Qt threads, reminder loop, etc.)
    from core.event_bus import publish_sync
    publish_sync("voice.wake_detected", {})

Event catalogue:
    voice.wake_detected       — Wake word heard; payload: {}
    voice.transcript_ready    — STT done; payload: {text, language, confidence}
    voice.speaking_start      — TTS started; payload: {text}
    voice.speaking_end        — TTS finished; payload: {}
    agent.task_received       — Command accepted; payload: {task_id, raw_input}
    agent.plan_ready          — Steps produced; payload: {task_id, step_count}
    agent.step_started        — Step executing; payload: {task_id, step, tool}
    agent.step_done           — Step finished; payload: {task_id, step, success, result}
    agent.task_complete       — All done; payload: {task_id, success, summary}
    agent.error               — Task failed; payload: {task_id, step, error, recoverable}
    system.state_changed      — Orb state update; payload: {state}
    memory.stored             — Memory written; payload: {id, source}
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import defaultdict
from typing import Any, Callable

log = logging.getLogger("core.event_bus")


# ═════════════════════════════════════════════════════════════════
#  Event Bus
# ═════════════════════════════════════════════════════════════════

class EventBus:
    """
    Thread-safe async pub/sub event bus.

    Handlers can be either:
      - async def handlers: awaited directly
      - regular def handlers: called synchronously in the event loop

    Publishing is non-blocking — all subscribers are notified
    without the publisher waiting for them to finish.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── Subscription Management ───────────────────────────────────

    def subscribe(self, event: str, handler: Callable) -> None:
        """
        Register a handler for a named event.

        Args:
            event:   The event name (e.g. "agent.task_complete").
            handler: Callable invoked with the event payload dict.
                     May be async def or regular def.

        Example:
            event_bus.subscribe("voice.wake_detected", on_wake)
        """
        with self._lock:
            if handler not in self._subscribers[event]:
                self._subscribers[event].append(handler)
                log.debug(f"Subscribed '{handler.__name__}' to '{event}'")

    def unsubscribe(self, event: str, handler: Callable) -> None:
        """
        Remove a handler from a named event.

        Args:
            event:   The event name.
            handler: The exact handler callable to remove.
        """
        with self._lock:
            subscribers = self._subscribers.get(event, [])
            if handler in subscribers:
                subscribers.remove(handler)
                log.debug(f"Unsubscribed '{handler.__name__}' from '{event}'")

    # ── Publishing ────────────────────────────────────────────────

    async def publish(self, event: str, payload: dict | None = None) -> None:
        """
        Publish an event to all registered subscribers (async version).

        Handlers are called concurrently — no handler blocks another.
        Exceptions in handlers are logged but do not propagate to the publisher.

        Args:
            event:   The event name.
            payload: Optional dict of event data.

        Example:
            await event_bus.publish("agent.task_complete",
                                    {"task_id": "abc", "success": True})
        """
        payload = payload or {}
        with self._lock:
            handlers = list(self._subscribers.get(event, []))

        if not handlers:
            log.debug(f"Event '{event}' published — no subscribers")
            return

        log.debug(f"Publishing '{event}' to {len(handlers)} subscriber(s)")

        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(
                        self._safe_async_call(handler, payload, event)
                    ))
                else:
                    self._safe_sync_call(handler, payload, event)
            except Exception as exc:
                log.error(f"Error dispatching '{event}' to '{handler.__name__}': {exc}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def publish_nowait(self, event: str, payload: dict | None = None) -> None:
        """
        Fire-and-forget publish from synchronous code (Qt threads, etc.).

        Schedules the event on the running event loop without blocking.
        If no event loop is running, falls back to calling sync handlers only.

        Args:
            event:   The event name.
            payload: Optional dict of event data.
        """
        payload = payload or {}
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(
                    lambda: asyncio.ensure_future(self.publish(event, payload))
                )
            else:
                # No running loop — call sync handlers directly
                self._call_sync_handlers(event, payload)
        except RuntimeError:
            self._call_sync_handlers(event, payload)

    # ── Internal Helpers ──────────────────────────────────────────

    async def _safe_async_call(
        self, handler: Callable, payload: dict, event: str
    ) -> None:
        """Await an async handler; log but don't propagate exceptions."""
        try:
            await handler(payload)
        except Exception as exc:
            log.error(
                f"Async handler '{handler.__name__}' raised on event '{event}': {exc}",
                exc_info=True,
            )

    def _safe_sync_call(
        self, handler: Callable, payload: dict, event: str
    ) -> None:
        """Call a sync handler; log but don't propagate exceptions."""
        try:
            handler(payload)
        except Exception as exc:
            log.error(
                f"Sync handler '{handler.__name__}' raised on event '{event}': {exc}",
                exc_info=True,
            )

    def _call_sync_handlers(self, event: str, payload: dict) -> None:
        """Call only synchronous handlers (used when no event loop is running)."""
        with self._lock:
            handlers = list(self._subscribers.get(event, []))
        for handler in handlers:
            if not asyncio.iscoroutinefunction(handler):
                self._safe_sync_call(handler, payload, event)

    # ── Introspection ─────────────────────────────────────────────

    def list_events(self) -> list[str]:
        """Return all event names that have at least one subscriber."""
        with self._lock:
            return [e for e, h in self._subscribers.items() if h]

    def subscriber_count(self, event: str) -> int:
        """Return the number of handlers subscribed to an event."""
        with self._lock:
            return len(self._subscribers.get(event, []))

    def clear(self) -> None:
        """Remove all subscriptions. Used in testing."""
        with self._lock:
            self._subscribers.clear()
        log.debug("Event bus cleared.")


# ═════════════════════════════════════════════════════════════════
#  Global Singleton
# ═════════════════════════════════════════════════════════════════

#: The single shared EventBus instance for the entire WEDNESDAY system.
#: Import this everywhere: ``from core.event_bus import event_bus``
event_bus: EventBus = EventBus()


# ═════════════════════════════════════════════════════════════════
#  Convenience: sync publish for use outside async contexts
# ═════════════════════════════════════════════════════════════════

def publish_sync(event: str, payload: dict | None = None) -> None:
    """
    Thread-safe synchronous publish for use from Qt threads, reminder loops,
    or any non-async code.

    Args:
        event:   The event name.
        payload: Optional dict of event data.

    Example:
        # Inside a Qt slot or background thread:
        publish_sync("voice.wake_detected", {})
    """
    event_bus.publish_nowait(event, payload or {})
