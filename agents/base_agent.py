"""agents/base_agent.py"""
from abc import ABC, abstractmethod
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, task: str, context: dict = None) -> str: ...
