"""Form agent for empty, partial, invalid, and valid form submissions."""

from time import perf_counter

from agents.helpers import fail, result
from config import TARGET_URL as DEFAULT_TARGET_URL
from tools.browser_tool import navigate
from tools.log_tool import log_step
from tools.screenshot_tool import full_page_shot


class FormAgent:
    name = "Forms"

    def __init__(self, page, visual_agent, target_url: str | None = None):
        self.page = page
        self.visual_agent = visual_agent
        self.target_url = target_url or DEFAULT_TARGET_URL

    async def run(self):
        """Execute form checks and return TestResult objects."""
        return [
            await self.submit_empty_forms(),
            await self.submit_filled_forms(),
        ]

    async def submit_empty_forms(self):
        started = perf_counter()
        try:
            log_step("Forms: checking empty form submissions")
            await navigate(self.page, self.target_url)
            form_count = await self.page.locator("form").count()
            if form_count == 0:
                return result(self.name, "submit empty forms", "PASS", "No forms found; skipped.", started)

            blocked_or_errors = 0
            attempted = 0
            skipped = 0
            for index in range(min(form_count, 5)):
                log_step(f"Forms: submitting empty form {index + 1}/{min(form_count, 5)}")
                await navigate(self.page, self.target_url)
                before = self.page.url
                form = self.page.locator("form").nth(index)
                submit = await self._visible_submit_control(form)
                if submit is None:
                    skipped += 1
                    continue

                await submit.click()
                attempted += 1
                await self.page.wait_for_timeout(700)
                if before == self.page.url or await self._validation_visible():
                    blocked_or_errors += 1

            if attempted == 0:
                detail = f"No visible submit controls found in {skipped} forms; skipped."
                return result(self.name, "submit empty forms", "PASS", detail, started)

            shot = await full_page_shot(self.page, "forms_empty_submit")
            status = "PASS" if blocked_or_errors else "FAIL"
            detail = (
                f"{blocked_or_errors}/{attempted} submitted forms blocked empty submit "
                f"or showed validation; skipped {skipped} forms without visible submit controls."
            )
            return result(self.name, "submit empty forms", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "submit empty forms", exc, started)

    async def submit_filled_forms(self):
        started = perf_counter()
        try:
            log_step("Forms: checking filled form submissions")
            await navigate(self.page, self.target_url)
            form_count = await self.page.locator("form").count()
            if form_count == 0:
                return result(self.name, "submit valid forms", "PASS", "No forms found; skipped.", started)

            attempted = 0
            for index in range(min(form_count, 5)):
                log_step(f"Forms: filling form {index + 1}/{min(form_count, 5)}")
                await navigate(self.page, self.target_url)
                form = self.page.locator("form").nth(index)
                await self._fill_form(form)
                submit = await self._visible_submit_control(form)
                if submit is not None:
                    log_step(f"Forms: submitting filled form {index + 1}/{min(form_count, 5)}")
                    await submit.click()
                    attempted += 1
                    await self.page.wait_for_timeout(700)

            if attempted == 0:
                return result(self.name, "submit valid forms", "PASS", "No visible submit controls found; skipped.", started)

            shot = await full_page_shot(self.page, "forms_valid_submit")
            visual = await self.visual_agent.evaluate(shot, "Page after submitting filled forms")
            status = "PASS" if attempted and visual.status == "PASS" else "FAIL"
            detail = f"Submitted {attempted} filled forms. {visual.reason}"
            return result(self.name, "submit valid forms", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "submit valid forms", exc, started)

    async def _visible_submit_control(self, form):
        submits = form.locator('button, input[type="submit"], input[type="image"]')
        for index in range(await submits.count()):
            submit = submits.nth(index)
            if await submit.is_visible():
                return submit
        return None

    async def _fill_form(self, form) -> None:
        inputs = form.locator("input, textarea, select")
        for index in range(await inputs.count()):
            log_step(f"Forms: filling field {index + 1}/{await inputs.count()}")
            field = inputs.nth(index)
            tag = await field.evaluate("el => el.tagName.toLowerCase()")
            field_type = (await field.get_attribute("type") or "text").lower()
            name = " ".join(filter(None, [await field.get_attribute("name"), await field.get_attribute("placeholder")])).lower()

            if field_type in {"hidden", "submit", "button", "checkbox", "radio", "file"}:
                continue
            if tag == "select":
                options = field.locator("option")
                if await options.count() > 1:
                    await field.select_option(index=1)
                continue
            if "email" in name or field_type == "email":
                await field.fill("qa@example.com")
            elif "phone" in name or "tel" in name:
                await field.fill("1234567890")
            elif field_type == "number":
                await field.fill("1")
            else:
                await field.fill("QA test value")

    async def _validation_visible(self) -> bool:
        css_errors = await self.page.locator('[role="alert"], .error, .invalid, .validation').count()
        body_text = (await self.page.locator("body").inner_text()).lower()
        return css_errors > 0 or any(word in body_text for word in ["required", "invalid", "error"])
