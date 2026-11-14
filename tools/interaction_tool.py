"""Consistent interaction wrappers for Playwright selectors."""

from config import DEFAULT_TIMEOUT_MS
from tools.log_tool import log_step


async def click(page, selector: str) -> bool:
    try:
        log_step(f"Chromium clicking {selector}")
        item = page.locator(selector).first
        await item.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
        await item.click()
        return True
    except Exception:
        log_step(f"Chromium could not click {selector}")
        return False


async def type_text(page, selector: str, text: str) -> bool:
    try:
        log_step(f"Chromium typing into {selector}")
        item = page.locator(selector).first
        await item.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
        await item.fill(text)
        return True
    except Exception:
        log_step(f"Chromium could not type into {selector}")
        return False


async def hover(page, selector: str) -> bool:
    try:
        log_step(f"Chromium hovering {selector}")
        item = page.locator(selector).first
        await item.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
        await item.hover()
        return True
    except Exception:
        log_step(f"Chromium could not hover {selector}")
        return False


async def scroll_to(page, selector: str) -> bool:
    try:
        log_step(f"Chromium scrolling to {selector}")
        item = page.locator(selector).first
        await item.wait_for(state="attached", timeout=DEFAULT_TIMEOUT_MS)
        await item.scroll_into_view_if_needed()
        return True
    except Exception:
        log_step(f"Chromium could not scroll to {selector}")
        return False
