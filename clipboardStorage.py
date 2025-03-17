import os
import json

# Where you want to store your history:
HISTORY_FILE = os.path.expanduser("~/.config/clipboard_history.json")


def load_history_from_file():
    """Load clipboard history from a JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history_to_file(history_list):
    """Save clipboard history to a JSON file."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_list, f)
    except IOError:
        pass
