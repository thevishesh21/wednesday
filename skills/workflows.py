"""
Wednesday - Automation Workflows Skill
Predefined and user-configurable automation workflows.
Example: "Start work mode" opens VS Code, browser, Slack, etc.
"""

import json
import os
import time
import logging

import config
from skills import app_control, web_actions

logger = logging.getLogger("Wednesday")

# Built-in workflows (always available)
BUILTIN_WORKFLOWS = {
    "work mode": {
        "description": "Open work apps",
        "steps": [
            {"action": "open_app", "target": "chrome"},
            {"action": "open_app", "target": "vscode"},
            {"action": "open_app", "target": "outlook"},
        ],
    },
    "study mode": {
        "description": "Open study apps",
        "steps": [
            {"action": "open_app", "target": "chrome"},
            {"action": "open_website", "target": "https://www.youtube.com"},
            {"action": "open_app", "target": "notepad"},
        ],
    },
    "chill mode": {
        "description": "Open entertainment",
        "steps": [
            {"action": "open_app", "target": "spotify"},
            {"action": "open_website", "target": "https://www.youtube.com"},
        ],
    },
}


def _load_custom_workflows() -> dict:
    """Load user-defined workflows from JSON."""
    if os.path.exists(config.WORKFLOWS_FILE):
        try:
            with open(config.WORKFLOWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_custom_workflows(workflows: dict):
    os.makedirs(os.path.dirname(config.WORKFLOWS_FILE), exist_ok=True)
    try:
        with open(config.WORKFLOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(workflows, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error("[Workflows] Failed to save: %s", e)


def _get_all_workflows() -> dict:
    """Merge built-in and custom workflows."""
    merged = dict(BUILTIN_WORKFLOWS)
    merged.update(_load_custom_workflows())
    return merged


def run_workflow(name: str) -> str:
    """Execute a named workflow."""
    workflows = _get_all_workflows()
    key = name.lower().strip()

    if key not in workflows:
        available = ", ".join(workflows.keys())
        return f"I don't have a workflow called '{name}'. Available: {available}"

    workflow = workflows[key]
    steps = workflow.get("steps", [])
    results = []

    for step in steps:
        action = step.get("action", "")
        target = step.get("target", "")

        if action == "open_app":
            results.append(app_control.open_app(target))
        elif action == "open_website":
            results.append(web_actions.open_website(target))
        elif action == "google_search":
            results.append(web_actions.google_search(target))
        else:
            results.append(f"Unknown workflow step: {action}")

        time.sleep(1)  # brief pause between steps

    description = workflow.get("description", name)
    return f"Started {description}. Opened {len(steps)} items."


def list_workflows() -> str:
    """List all available workflows."""
    workflows = _get_all_workflows()
    if not workflows:
        return "No workflows configured."
    lines = [f"{name}: {w.get('description', 'No description')}"
             for name, w in workflows.items()]
    return "Available workflows: " + "; ".join(lines)
