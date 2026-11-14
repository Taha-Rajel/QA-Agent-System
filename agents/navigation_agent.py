"""Navigation agent for internal links, redirects, console errors, and history."""

from time import perf_counter
from urllib.parse import urlparse

from agents.helpers import fail, result
from config import TARGET_URL as DEFAULT_TARGET_URL
from tools.browser_tool import navigate
from tools.dom_tool import get_all_links
from tools.log_tool import log_step
from tools.screenshot_tool import full_page_shot


class NavigationAgent:
    name = "Navigation"

    def __init__(self, page, target_url: str | None = None):
        self.page = page
        self.target_url = target_url or DEFAULT_TARGET_URL
        self.console_errors = []
        self.page.on("console", self._record_console_error)

    async def run(self):
        """Execute navigation checks and return TestResult objects."""
        return [
            await self.visit_internal_links(),
            await self.test_history_buttons(),
            await self.test_refresh(),
        ]

    async def visit_internal_links(self):
        started = perf_counter()
        try:
            log_step("Navigation: collecting and visiting internal links")
            await navigate(self.page, self.target_url)
            links = self._internal_links(await get_all_links(self.page))
            failures = []

            for index, link in enumerate(links[:20], start=1):
                log_step(f"Navigation: visiting internal link {index}/{min(len(links), 20)}: {link}")
                self.console_errors.clear()
                response = await self.page.goto(link, wait_until="domcontentloaded")
                status_code = response.status if response else 0
                if status_code >= 400 or self.console_errors:
                    failures.append(f"{link} status={status_code} console_errors={len(self.console_errors)}")

            shot = await full_page_shot(self.page, "navigation_internal_links")
            status = "PASS" if not failures else "FAIL"
            detail = f"Visited {min(len(links), 20)} internal links." if not failures else "; ".join(failures[:5])
            return result(self.name, "visit all internal links", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "visit all internal links", exc, started)

    async def test_history_buttons(self):
        started = perf_counter()
        try:
            log_step("Navigation: testing browser back and forward")
            await navigate(self.page, self.target_url)
            links = self._internal_links(await get_all_links(self.page))
            if not links:
                return result(self.name, "browser back and forward", "PASS", "No internal links found; skipped.", started)

            await self.page.goto(links[0], wait_until="domcontentloaded")
            first_url = self.page.url
            log_step("Navigation: pressing browser back")
            await self.page.go_back(wait_until="domcontentloaded")
            back_url = self.page.url
            log_step("Navigation: pressing browser forward")
            await self.page.go_forward(wait_until="domcontentloaded")
            forward_url = self.page.url
            shot = await full_page_shot(self.page, "navigation_history")
            status = "PASS" if back_url != first_url and forward_url == first_url else "FAIL"
            detail = f"back={back_url}, forward={forward_url}"
            return result(self.name, "browser back and forward", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "browser back and forward", exc, started)

    async def test_refresh(self):
        started = perf_counter()
        try:
            log_step("Navigation: refreshing current page")
            before = self.page.url
            response = await self.page.reload(wait_until="domcontentloaded")
            after = self.page.url
            shot = await full_page_shot(self.page, "navigation_refresh")
            status_code = response.status if response else 0
            status = "PASS" if before == after and status_code < 400 else "FAIL"
            detail = f"Refresh status={status_code}, url_preserved={before == after}"
            return result(self.name, "refresh current page", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "refresh current page", exc, started)

    def _internal_links(self, links: list[str]) -> list[str]:
        target = urlparse(self.target_url)
        seen = set()
        internal = []
        for link in links:
            parsed = urlparse(link)
            clean = link.split("#", 1)[0]
            if parsed.netloc == target.netloc and clean not in seen:
                seen.add(clean)
                internal.append(clean)
        return internal

    def _record_console_error(self, message):
        if message.type == "error":
            self.console_errors.append(message.text)
