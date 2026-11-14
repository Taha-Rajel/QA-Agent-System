"""DOM querying helpers."""

from config import DEFAULT_TIMEOUT_MS
from tools.log_tool import log_step


async def get_all_links(page) -> list[str]:
    links = await page.eval_on_selector_all(
        "a[href]",
        "items => items.map(a => a.href).filter(Boolean)",
    )
    log_step(f"Collected {len(links)} links from the page")
    return links


async def element_exists(page, selector: str) -> bool:
    try:
        return await page.locator(selector).count() > 0
    except Exception:
        return False


async def get_text(page, selector: str) -> str:
    try:
        return await page.locator(selector).first.inner_text(timeout=DEFAULT_TIMEOUT_MS)
    except Exception:
        return ""


async def wait_for(page, selector: str, timeout: int | None = None) -> bool:
    try:
        await page.locator(selector).first.wait_for(
            state="visible",
            timeout=timeout or DEFAULT_TIMEOUT_MS,
        )
        return True
    except Exception:
        return False
