"""Playwright browser lifecycle helpers."""

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from config import NAVIGATION_TIMEOUT_MS, PLAYWRIGHT_HEADLESS
from tools.log_tool import log_step


NETWORK_IDLE_TIMEOUT_MS = 5_000


async def launch_browser():
    """Launch Chromium and return a browser/page pair."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
    browser._qa_playwright = playwright
    page = await browser.new_page()
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
    page.set_default_timeout(NAVIGATION_TIMEOUT_MS)
    mode = "headless" if PLAYWRIGHT_HEADLESS else "visible"
    log_step(f"Chromium browser opened ({mode})")
    return browser, page


async def navigate(page, url: str):
    """Navigate to a URL, tolerating pages that never become fully network-idle."""
    log_step(f"Chromium navigating to {url}")
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        log_step("Network did not become idle; continuing after DOM loaded")
    log_step(f"Chromium loaded {page.url}")


async def close_browser(browser):
    """Close the browser and Playwright runtime."""
    playwright = getattr(browser, "_qa_playwright", None)
    await browser.close()
    if playwright:
        await playwright.stop()
    log_step("Chromium browser closed")
