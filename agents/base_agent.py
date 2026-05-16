"""
agents/base_agent.py
---------------------
Abstract base class for all Wednesday agents.
STUB — Full implementation in Phase 6.
"""
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, task: str, context: dict = None) -> str:
        """Execute the agent's task and return a result string."""
        ...
