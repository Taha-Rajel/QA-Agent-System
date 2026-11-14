"""Screenshot helpers."""

from datetime import datetime
import re

from config import SCREENSHOT_ROOT
from tools.log_tool import log_step


RUN_SCREENSHOT_DIR = SCREENSHOT_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name.strip().lower())
    return cleaned[:80] or "screenshot"


async def full_page_shot(page, name: str) -> str:
    """Capture a full-page screenshot and return its path."""
    RUN_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = RUN_SCREENSHOT_DIR / f"{_safe_name(name)}.png"
    log_step(f"Capturing full-page screenshot: {path.name}")
    await page.screenshot(path=str(path), full_page=True)
    return str(path)


async def element_shot(page, selector: str, name: str) -> str:
    """Capture an element screenshot and return its path."""
    RUN_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = RUN_SCREENSHOT_DIR / f"{_safe_name(name)}.png"
    log_step(f"Capturing element screenshot: {selector} -> {path.name}")
    await page.locator(selector).first.screenshot(path=str(path))
    return str(path)
