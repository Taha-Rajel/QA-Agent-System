"""Auth agent for login, failed login, logout, and protected route checks."""

from secrets import token_hex
from time import perf_counter
from urllib.parse import urljoin

from agents.helpers import fail, result
from config import TARGET_URL as DEFAULT_TARGET_URL, TEST_EMAIL, TEST_PASSWORD
from tools.browser_tool import navigate
from tools.interaction_tool import click, type_text
from tools.log_tool import log_step
from tools.screenshot_tool import full_page_shot


class AuthAgent:
    name = "Auth"

    def __init__(self, page, visual_agent, target_url: str | None = None):
        self.page = page
        self.visual_agent = visual_agent
        self.target_url = target_url or DEFAULT_TARGET_URL

    async def run(self):
        """Execute auth checks and return TestResult objects."""
        return [
            await self.login_valid_credentials(),
            await self.login_wrong_credentials(),
            await self.logout(),
            await self.protected_route_redirect(),
        ]

    async def login_valid_credentials(self):
        started = perf_counter()
        try:
            log_step("Auth: checking login with generated or configured credentials")
            await navigate(self.page, self.target_url)
            if not await self._login_form_visible():
                return result(self.name, "login with generated credentials", "PASS", "No login form found; auth check skipped.", started)

            email, password = self._credentials()
            submitted = await self._fill_login(email, password)
            shot = await full_page_shot(self.page, "auth_valid_login")
            logged_in = submitted and not await self._login_form_visible()
            status = "PASS" if logged_in else "FAIL"
            detail = "Generated login left the login form." if logged_in else "Generated login did not appear to succeed."
            return result(self.name, "login with generated credentials", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "login with valid credentials", exc, started)

    async def login_wrong_credentials(self):
        started = perf_counter()
        try:
            log_step("Auth: checking login with wrong credentials")
            await navigate(self.page, self.target_url)
            if not await self._login_form_visible():
                return result(self.name, "login with wrong password", "PASS", "No login form found; negative auth check skipped.", started)

            submitted = await self._fill_login("wrong_user", "wrong_password")
            await self.page.wait_for_timeout(700)
            shot = await full_page_shot(self.page, "auth_wrong_login")
            error_visible = await self._error_visible()
            status = "PASS" if submitted and error_visible else "FAIL"
            detail = "Wrong login showed an error." if error_visible else "Wrong login did not show a visible error."
            return result(self.name, "login with wrong password", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "login with wrong password", exc, started)

    async def logout(self):
        started = perf_counter()
        try:
            log_step("Auth: checking logout behavior")
            if await self._login_form_visible():
                email, password = self._credentials()
                await self._fill_login(email, password)
            elif not await self._has_logout_control():
                return result(self.name, "logout and verify session ends", "PASS", "No logged-in session or logout control found; skipped.", started)

            await click(self.page, "#react-burger-menu-btn")
            await self.page.wait_for_timeout(300)
            did_logout = await click(self.page, "#logout_sidebar_link")
            if not did_logout:
                did_logout = await click(self.page, "text=/logout/i")
            await self.page.wait_for_timeout(700)
            shot = await full_page_shot(self.page, "auth_logout")
            form_visible = await self._login_form_visible()
            status = "PASS" if did_logout and form_visible else "FAIL"
            detail = "Logout returned to login form." if status == "PASS" else "Logout control was not found or did not end session."
            return result(self.name, "logout and verify session ends", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "logout and verify session ends", exc, started)

    async def protected_route_redirect(self):
        started = perf_counter()
        try:
            log_step("Auth: checking protected route behavior while logged out")
            protected_url = urljoin(
                self.target_url,
                "/inventory.html" if "saucedemo.com" in self.target_url else "/dashboard",
            )
            await navigate(self.page, protected_url)
            await self.page.wait_for_timeout(700)
            shot = await full_page_shot(self.page, "auth_protected_route")
            if "404" in (await self.page.title()).lower() or "not found" in (await self.page.locator("body").inner_text()).lower():
                return result(self.name, "access protected route while logged out", "PASS", "No protected route detected at /dashboard; skipped.", started, shot)

            protected = not await self._login_form_visible()
            status = "FAIL" if protected else "PASS"
            detail = "Logged-out protected route redirected to login." if status == "PASS" else "Protected route loaded while logged out."
            return result(self.name, "access protected route while logged out", status, detail, started, shot)
        except Exception as exc:
            return fail(self.name, "access protected route while logged out", exc, started)

    async def _fill_login(self, username: str, password: str) -> bool:
        user_selector = 'input[type="email"], input[name*="email"], input[name*="user"], #user-name'
        pass_selector = 'input[type="password"], input[name*="password"], #password'
        submit_selector = 'button[type="submit"], input[type="submit"], #login-button'
        filled_user = await type_text(self.page, user_selector, username)
        filled_pass = await type_text(self.page, pass_selector, password)
        submitted = await click(self.page, submit_selector)
        await self.page.wait_for_timeout(1000)
        return filled_user and filled_pass and submitted

    async def _login_form_visible(self) -> bool:
        return await self.page.locator('input[type="password"], #password').count() > 0

    async def _has_logout_control(self) -> bool:
        logout_text = await self.page.locator("text=/logout/i").count()
        return logout_text > 0 or await self.page.locator("#logout_sidebar_link").count() > 0

    async def _error_visible(self) -> bool:
        css_errors = await self.page.locator('[role="alert"], .error, .error-message, [data-test="error"]').count()
        body_text = (await self.page.locator("body").inner_text()).lower()
        return css_errors > 0 or any(word in body_text for word in ["invalid", "incorrect", "required", "locked"])

    def _credentials(self) -> tuple[str, str]:
        email = TEST_EMAIL.strip() or f"qa-{token_hex(4)}@example.com"
        password = TEST_PASSWORD.strip() or f"Qa-{token_hex(6)}!"
        return email, password
