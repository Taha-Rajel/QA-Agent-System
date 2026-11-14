"""Central configuration for the QA agent system."""

from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=True)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

TARGET_URL = os.getenv("TARGET_URL", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TEST_EMAIL = os.getenv("TEST_EMAIL", "")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")
PLAYWRIGHT_HEADLESS = _env_bool("PLAYWRIGHT_HEADLESS", default=False)

DEFAULT_MODEL_NAME = "nvidia/nemotron-nano-12b-v2-vl:free"
MODEL_NAME = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

SCREENSHOT_ROOT = BASE_DIR / "screenshots" / "runs"
OUTPUT_DIR = BASE_DIR / "output"
DB_JSON_PATH = BASE_DIR / "db" / "qa_history.json"

DEFAULT_TIMEOUT_MS = 10_000
NAVIGATION_TIMEOUT_MS = 30_000
MOBILE_WIDTH = 375
MOBILE_HEIGHT = 812
