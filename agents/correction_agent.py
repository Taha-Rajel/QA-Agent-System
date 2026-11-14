"""Correction agent that turns QA issues into practical fix guidance."""

from time import perf_counter

from agents.helpers import result
from models import TestResult
from tools.log_tool import log_step


class CorrectionAgent:
    name = "Correction"

    async def run(self, results: list[TestResult]):
        """Return correction guidance for every failed or errored result."""
        log_step("Correction: reviewing failed and errored report results")
        issues = [item for item in results if item.status in {"FAIL", "ERROR"}]
        if not issues:
            return [self._no_issues_result()]
        return [self._correction_for(issue) for issue in issues]

    def _no_issues_result(self) -> TestResult:
        started = perf_counter()
        detail = (
            "No FAIL or ERROR items were found in this run. Keep the website monitored "
            "after future UI, route, authentication, or form changes."
        )
        return result(self.name, "correction summary", "INFO", detail, started)

    def _correction_for(self, issue: TestResult) -> TestResult:
        started = perf_counter()
        guidance = self._guidance_for(issue)
        detail_parts = [
            f"Issue detected: {issue.agent} - {issue.test_name} ({issue.status}).",
        ]
        if issue.detail:
            detail_parts.append(f"Report detail: {issue.detail}")
        detail_parts.append(f"How to correct it: {guidance}")
        return result(
            self.name,
            f"fix {issue.agent.lower()} - {issue.test_name}",
            "INFO",
            " ".join(detail_parts),
            started,
            issue.screenshot_path,
        )

    def _guidance_for(self, issue: TestResult) -> str:
        agent = issue.agent.lower()
        test_name = issue.test_name.lower()
        detail = issue.detail.lower()

        if issue.status == "ERROR":
            return (
                "First fix the automation/runtime error so the check can run again. "
                "Review the exception in the report detail, confirm selectors still match the page, "
                "and verify the target URL loads reliably."
            )

        if "openrouter_api_key" in detail or "vision check failed" in detail:
            return (
                "Configure a valid OPENROUTER_API_KEY in .env, confirm the selected vision model is available, "
                "then rerun the report so visual checks can produce real page feedback."
            )

        if agent == "ui":
            if "click visible buttons" in test_name:
                return (
                    "Review the clicked controls, connect missing click handlers or href targets, "
                    "and make sure each enabled control causes a clear state change, navigation, or visible feedback."
                )
            if "theme toggle" in test_name:
                return (
                    "Wire the theme control to the site theme state, update the page colors immediately, "
                    "persist the selected mode if needed, and expose the control with a clear label or aria attribute."
                )
            if "mobile" in test_name:
                return (
                    "Inspect the page at 375px width, replace fixed widths with responsive constraints, "
                    "avoid horizontal overflow, and stack or resize dense content for small screens."
                )
            return (
                "Check the screenshot for visible layout defects, missing assets, overflow, or unreadable text, "
                "then adjust the affected HTML/CSS and rerun the UI checks."
            )

        if agent == "auth":
            if "wrong password" in test_name:
                return (
                    "Add negative-login validation, keep the user on the login screen, "
                    "and show a visible error message, ideally using role='alert' or a clear error class."
                )
            if "logout" in test_name:
                return (
                    "Connect the logout control to session clearing, remove stored auth tokens/cookies, "
                    "and redirect the user back to a logged-out page."
                )
            if "protected route" in test_name:
                return (
                    "Guard protected routes on the client and server, check authentication before rendering private content, "
                    "and redirect logged-out users to the login page."
                )
            return (
                "Verify the login form selectors, configured test credentials, session creation, and post-login redirect flow."
            )

        if agent == "navigation":
            if "internal links" in test_name:
                return (
                    "Fix broken hrefs or missing routes, ensure internal pages return HTTP 200/3xx, "
                    "and resolve any JavaScript console errors raised during navigation."
                )
            if "back and forward" in test_name:
                return (
                    "Use real browser history entries for page changes, avoid replacing history unexpectedly, "
                    "and confirm back/forward restore the expected URL and content."
                )
            if "refresh" in test_name:
                return (
                    "Make routes reload-safe by serving the correct page on refresh, preserving the URL, "
                    "and avoiding server responses with 4xx or 5xx status codes."
                )

        if agent == "forms":
            if "empty" in test_name:
                return (
                    "Mark required fields, prevent empty submission, and display clear validation messages near the invalid inputs."
                )
            return (
                "Confirm the form accepts valid generated values, submit handlers run successfully, "
                "and users receive a visible success or next-step message."
            )

        return (
            "Use the report detail and screenshot to locate the failing page state, correct the related UI or behavior, "
            "then rerun the QA report to confirm the item is no longer FAIL."
        )
