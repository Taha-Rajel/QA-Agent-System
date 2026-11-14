"""JSON history file initialization."""

import json

from config import DB_JSON_PATH


EMPTY_DATABASE = {
    "runs": [],
    "tests": [],
    "visuals": [],
}


def initialize_database() -> None:
    """Create the JSON history file on first run."""
    DB_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_JSON_PATH.exists():
        write_database(EMPTY_DATABASE.copy())


def read_database() -> dict:
    initialize_database()
    return json.loads(DB_JSON_PATH.read_text(encoding="utf-8"))


def write_database(data: dict) -> None:
    DB_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_JSON_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
