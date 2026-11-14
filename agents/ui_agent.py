"""UI agent for buttons, theme toggles, screenshots, and mobile layout."""

from time import perf_counter

from agents.helpers import fail, result
from config import MOBILE_HEIGHT, MOBILE_WIDTH, TARGET_URL as DEFAULT_TARGET_URL
from tools.browser_tool import navigate
from tools.interaction_tool import click
from tools.log_tool import log_step
from tools.screenshot_tool import full_page_shot


class UIAgent:
    name = "UI"

    def __init__(self, page, visual_agent, target_url: str | None = None):
        self.page = page
        self.visual_agent = visual_agent
        self.target_url = target_url or DEFAULT_TARGET_URL

    async def run(self):
        """Execute UI checks and return TestResult objects."""
        return [
            await self.check_homepage_visual(),
            await self.click_visible_buttons(),
            await self.check_theme_toggle(),
            await self.check_mobile_layout(),
        ]

    async def check_homepage_visual(self):
        started = perf_counter()
        try:
            log_step("UI: checking homepage visual state")
            await navigate(self.page, self.target_url)
            shot = await full_page_shot(self.page, "ui_homepage")
            visual = await self.visual_agent.evaluate(shot, "Homepage after first load")
            return result(self.name, "homepage visual check", visual.status, visual.reason, started, shot)
        except Exception as exc:
            return fail(self.name, "homepage visual check", exc, started)

    async def click_visible_buttons(self):
        started = perf_counter()
        try:
            log_step("UI: finding visible buttons and clickable controls")
            buttons = await self._tag_clickable_elements()
            clicked = 0
            changed = 0

            for index, button in enumerate(buttons[:8]):
                log_step(f"UI: testing control {index + 1}/{min(len(buttons), 8)}: {button}")
                await navigate(self.page, self.target_url)
                await self._tag_clickable_elements()
                before = await self._page_state()
                did_click = await click(self.page, f'[data-qa-click-index="{index}"]')
                await self.page.wait_for_timeout(700)
                after = await self._page_state()

                if did_click:
                    clicked += 1
                if did_click and before != after:
                    changed += 1

            status = "PASS" if clicked == 0 or changed > 0 else "FAIL"
            detail = f"Clicked {clicked} visible controls; {changed} caused a visible state or URL change."
            shot = await full_page_shot(self.page, "ui_after_button_clicks")
            return result(self.name, "click visible buttons", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "click visible buttons", exc, started)

    async def check_theme_toggle(self):
        started = perf_counter()
        try:
            log_step("UI: looking for theme toggle")
            await navigate(self.page, self.target_url)
            selector = await self._find_theme_toggle()
            if not selector:
                return result(self.name, "theme toggle", "PASS", "No theme toggle found; optional check skipped.", started)

            before = await self._page_state()
            await click(self.page, selector)
            await self.page.wait_for_timeout(700)
            shot = await full_page_shot(self.page, "ui_theme_toggle")
            visual = await self.visual_agent.evaluate(shot, "Page after theme toggle")
            status = "PASS" if before != await self._page_state() and visual.status == "PASS" else "FAIL"
            return result(self.name, "theme toggle", status, visual.reason, started, shot)
        except Exception as exc:
            return fail(self.name, "theme toggle", exc, started)

    async def check_mobile_layout(self):
        started = perf_counter()
        try:
            log_step(f"UI: resizing Chromium to {MOBILE_WIDTH}x{MOBILE_HEIGHT}")
            await self.page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
            await navigate(self.page, self.target_url)
            shot = await full_page_shot(self.page, "ui_mobile_375")
            visual = await self.visual_agent.evaluate(shot, "Mobile layout at 375px width")
            return result(self.name, "mobile layout at 375px", visual.status, visual.reason, started, shot)
        except Exception as exc:
            return fail(self.name, "mobile layout at 375px", exc, started)
        finally:
            log_step("UI: restoring Chromium viewport to 1280x900")
            await self.page.set_viewport_size({"width": 1280, "height": 900})

    async def _tag_clickable_elements(self):
        return await self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll(
                'button, input[type="button"], input[type="submit"], a[role="button"], .btn'
            ))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
            })
            .map((el, index) => {
                el.setAttribute('data-qa-click-index', String(index));
                return (el.innerText || el.value || el.ariaLabel || el.id || el.className || 'control').trim();
            })
            """
        )

    async def _find_theme_toggle(self):
        return await self.page.evaluate(
            """
            () => {
                const words = ['theme', 'dark', 'light'];
                const items = Array.from(document.querySelectorAll('button, input, [role="switch"], [aria-label]'));
                const found = items.find(el => words.some(word =>
                    `${el.innerText} ${el.value} ${el.ariaLabel} ${el.id} ${el.className}`.toLowerCase().includes(word)
                ));
                if (!found) return null;
                found.setAttribute('data-qa-theme-toggle', 'true');
                return '[data-qa-theme-toggle="true"]';
            }
            """
        )

    async def _page_state(self):
        return await self.page.evaluate(
            "() => ({ url: location.href, title: document.title, text: document.body.innerText.slice(0, 5000) })"
        )
