"""
Wednesday AI Assistant — Tool Registry
Central registry mapping tool names → functions with metadata.
Supports tool validation and safe-mode tagging.
"""

from utils.logger import get_logger

log = get_logger("registry")

# ── Internal registry store ─────────────────────────────────────
# Format: { "tool_name": { "func": callable, "args": [required_args], "dangerous": bool, "description": str } }
_tools = {}


def register(name: str, func, required_args: list = None,
             dangerous: bool = False, description: str = ""):
    """
    Register a tool function.

    Args:
        name:          Unique tool name (e.g. "open_app")
        func:          The callable to execute
        required_args: List of required argument names (for validation)
        dangerous:     If True, executor will ask for confirmation in safe mode
        description:   Human-readable description
    """
    _tools[name] = {
        "func": func,
        "args": required_args or [],
        "dangerous": dangerous,
        "description": description,
    }
    log.debug(f"Registered tool: {name} ({'⚠️ dangerous' if dangerous else 'safe'})")


def get_tool(name: str) -> dict | None:
    """Get tool info dict by name, or None if not found."""
    return _tools.get(name)


def execute(name: str, args: dict = None) -> dict:
    """
    Execute a registered tool by name.

    Args:
        name: Tool name
        args: Dict of arguments to pass to the function

    Returns:
        {"success": bool, "result": any, "error": str|None}
    """
    args = args or {}
    tool = _tools.get(name)

    if not tool:
        log.error(f"Tool not found: {name}")
        return {"success": False, "result": None, "error": f"Tool '{name}' not found"}

    try:
        result = tool["func"](**args)
        log.info(f"Tool '{name}' executed successfully.")
        return {"success": True, "result": result, "error": None}
    except TypeError as e:
        log.error(f"Tool '{name}' argument error: {e}")
        return {"success": False, "result": None, "error": f"Wrong arguments: {e}"}
    except Exception as e:
        log.error(f"Tool '{name}' execution failed: {e}")
        return {"success": False, "result": None, "error": str(e)}


def validate(name: str, args: dict = None) -> tuple[bool, str]:
    """
    Validate that a tool exists and has the required arguments.

    Returns:
        (is_valid, error_message)
    """
    args = args or {}
    tool = _tools.get(name)

    if not tool:
        return False, f"Tool '{name}' does not exist"

    missing = [a for a in tool["args"] if a not in args]
    if missing:
        return False, f"Missing required args for '{name}': {missing}"

    return True, ""


def is_dangerous(name: str) -> bool:
    """Check if a tool is tagged as dangerous."""
    tool = _tools.get(name)
    return tool.get("dangerous", False) if tool else False


def list_tools() -> list[str]:
    """Return list of all registered tool names."""
    return list(_tools.keys())


def get_all_tools_info() -> dict:
    """Return full registry info (for debugging)."""
    return {name: {"args": t["args"], "dangerous": t["dangerous"],
                   "description": t["description"]}
            for name, t in _tools.items()}
