"""
WEDNESDAY AI OS — Task Queue
Async priority queue for incoming tasks.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Optional

from core.logger import get_logger

log = get_logger("agent.task_queue")

@dataclass(order=True)
class QueuedTask:
    """A task waiting to be processed by the agent loop."""
    priority: int
    raw_input: str = field(compare=False)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))

class TaskQueue:
    """
    Manages pending tasks for the agent loop.
    Supports priority execution (e.g. system interrupts vs background tasks).
    """
    def __init__(self):
        self._queue: asyncio.PriorityQueue[QueuedTask] = asyncio.PriorityQueue()
        
    async def put(self, raw_input: str, priority: int = 10) -> str:
        """
        Add a command to the queue.
        Lower priority number = executes first.
        """
        task = QueuedTask(priority=priority, raw_input=raw_input)
        await self._queue.put(task)
        log.debug(f"Task queued: {task.task_id} (priority {priority})")
        return task.task_id
        
    async def get(self) -> QueuedTask:
        """Get the next highest-priority task."""
        task = await self._queue.get()
        return task
        
    def task_done(self) -> None:
        """Mark the last gotten task as complete."""
        self._queue.task_done()
        
    @property
    def qsize(self) -> int:
        return self._queue.qsize()

# Global task queue
task_queue = TaskQueue()
