"""
WEDNESDAY AI OS — Tool Schema Registry
Reads registered tools and exposes JSON Schema definitions for LLM function calling.
This is separate from execution (which happens in tools/registry.py or skills/).
"""

from typing import Any
from core.logger import get_logger
from core.exceptions import ToolNotFoundError

# In a real migration, this would import from tools.registry to wrap existing tools,
# or skills.__init__ for the new skills architecture. For Phase 2, we simulate
# the schema generation for the existing tools to allow the task planner to work.

log = get_logger("brain.tool_registry")

_schemas: dict[str, dict[str, Any]] = {}

def register_schema(name: str, description: str, parameters: dict[str, Any]) -> None:
    """Manually register a tool schema."""
    _schemas[name] = {
        "name": name,
        "description": description,
        "parameters": parameters
    }
    log.debug(f"Registered schema for tool '{name}'")

def get_schema(name: str) -> dict[str, Any]:
    """Get the schema for a specific tool. Raises ToolNotFoundError if missing."""
    if name not in _schemas:
        raise ToolNotFoundError(f"Schema for tool '{name}' not found")
    return _schemas[name]

def get_all_schemas() -> list[dict[str, Any]]:
    """Return a list of all registered tool schemas."""
    return list(_schemas.values())

# ── Phase 2 Bootstrapping ────────────────────────────────────────

def _bootstrap_existing_tools() -> None:
    """
    Temporary helper to register schemas for the tools that already exist
    in tools/registry.py, so the LLM knows about them before Phase 5.
    """
    register_schema(
        name="open_app",
        description="Opens a desktop application or specific website by name.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the app to open (e.g., 'notepad', 'chrome', 'youtube')"}
            },
            "required": ["name"]
        }
    )
    register_schema(
        name="close_app",
        description="Closes a desktop application by name.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the app to close"}
            },
            "required": ["name"]
        }
    )
    register_schema(
        name="search_web",
        description="Performs a web search using the default browser.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    )
    register_schema(
        name="type_text",
        description="Types text using the keyboard.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to type"}
            },
            "required": ["text"]
        }
    )
    register_schema(
        name="press_hotkey",
        description="Presses a keyboard shortcut.",
        parameters={
            "type": "object",
            "properties": {
                "keys": {"type": "string", "description": "Comma-separated list of keys (e.g., 'ctrl,c', 'win,d')"}
            },
            "required": ["keys"]
        }
    )
    register_schema(
        name="create_file",
        description="Creates a new file with optional content.",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name of the file to create"},
                "content": {"type": "string", "description": "Optional content to write to the file"}
            },
            "required": ["filename"]
        }
    )
    register_schema(
        name="set_reminder",
        description="Sets a reminder for a specific time or duration.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to remind the user about"},
                "minutes": {"type": "integer", "description": "Minutes from now (e.g., 5)"},
                "at_time": {"type": "string", "description": "Specific time (e.g., '3:00 PM')"}
            },
            "required": ["text"]
        }
    )

# Run bootstrap on import
_bootstrap_existing_tools()
