"""
Wednesday - Contact Manager Skill
Manages a simple contacts database and enables sending emails to contacts.
"""

import json
import os
import logging

import config

logger = logging.getLogger("Wednesday")


def _load_contacts() -> dict:
    """Load contacts from JSON file."""
    if os.path.exists(config.CONTACTS_FILE):
        try:
            with open(config.CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_contacts(contacts: dict):
    """Save contacts to JSON file."""
    os.makedirs(os.path.dirname(config.CONTACTS_FILE), exist_ok=True)
    try:
        with open(config.CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error("[ContactManager] Failed to save contacts: %s", e)


def find_contact(name: str) -> str | None:
    """Look up a contact by name (case-insensitive). Returns the value or None."""
    contacts = _load_contacts()
    return contacts.get(name.lower().strip())


def add_contact(name: str, value: str) -> str:
    """Add or update a contact."""
    contacts = _load_contacts()
    contacts[name.lower().strip()] = value.strip()
    _save_contacts(contacts)
    return f"Contact '{name}' saved as {value}."


def remove_contact(name: str) -> str:
    """Remove a contact."""
    contacts = _load_contacts()
    key = name.lower().strip()
    if key in contacts:
        del contacts[key]
        _save_contacts(contacts)
        return f"Contact '{name}' removed."
    return f"Contact '{name}' not found."


def list_contacts() -> str:
    """List all contacts."""
    contacts = _load_contacts()
    if not contacts:
        return "You have no contacts saved."
    lines = [f"{name}: {value}" for name, value in contacts.items()]
    return "Your contacts: " + ", ".join(lines)


def send_email_to_contact(name: str, body: str = "") -> str:
    """Resolve a contact name and send email."""
    from skills.communication import send_email

    contact_value = find_contact(name)
    if not contact_value:
        return f"I don't have a contact named '{name}'. You can add one by saying 'add contact {name}'."

    if "@" not in contact_value:
        return f"The contact '{name}' has a phone number, not an email address."

    return send_email(to=contact_value, body=body)
