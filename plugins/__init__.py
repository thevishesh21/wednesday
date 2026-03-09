"""
Wednesday - Plugin System
Auto-discovers and loads plugins from the plugins/ directory.
Each plugin is a Python module with an optional `handle(command) -> str` function.
"""

import importlib
import os
import logging

import config

logger = logging.getLogger("Wednesday")

_loaded_plugins = {}


def discover_plugins() -> list[str]:
    """Scan the plugins directory and return a list of module names."""
    plugin_dir = config.PLUGIN_DIR
    if not os.path.isdir(plugin_dir):
        os.makedirs(plugin_dir, exist_ok=True)
        return []

    modules = []
    for fname in os.listdir(plugin_dir):
        if fname.endswith(".py") and not fname.startswith("_"):
            modules.append(fname[:-3])
    return modules


def load_plugins():
    """Load all discovered plugins."""
    global _loaded_plugins
    _loaded_plugins = {}

    for mod_name in discover_plugins():
        try:
            module = importlib.import_module(f"plugins.{mod_name}")
            _loaded_plugins[mod_name] = module
            logger.info("[Plugins] Loaded plugin: %s", mod_name)
        except Exception as e:
            logger.error("[Plugins] Failed to load '%s': %s", mod_name, e)


def get_plugin(name: str):
    """Get a loaded plugin by name."""
    return _loaded_plugins.get(name)


def list_plugins() -> list[str]:
    """Return names of loaded plugins."""
    return list(_loaded_plugins.keys())


def run_plugin_command(plugin_name: str, command: str = "") -> str:
    """Run a command on a specific plugin.

    Plugins should expose a `handle(command: str) -> str` function.
    """
    plugin = _loaded_plugins.get(plugin_name)
    if not plugin:
        return f"Plugin '{plugin_name}' is not loaded."

    handler = getattr(plugin, "handle", None)
    if not handler:
        return f"Plugin '{plugin_name}' does not have a handle() function."

    try:
        return handler(command)
    except Exception as e:
        return f"Plugin '{plugin_name}' error: {e}"
