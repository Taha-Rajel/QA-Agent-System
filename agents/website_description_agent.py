"""Website description agent for a short purpose summary."""

from time import perf_counter
from urllib.parse import urlparse

from agents.helpers import fail, result
from config import TARGET_URL as DEFAULT_TARGET_URL
from tools.browser_tool import navigate
from tools.log_tool import log_step


class WebsiteDescriptionAgent:
    name = "Website Description"

    def __init__(self, page, target_url: str | None = None):
        self.page = page
        self.target_url = target_url or DEFAULT_TARGET_URL

    async def run(self):
        """Describe the target website before the QA checks run."""
        return [await self.describe_website()]

    async def describe_website(self):
        started = perf_counter()
        try:
            log_step("Website Description: reading page purpose signals")
            await navigate(self.page, self.target_url)
            page_summary = await self._collect_page_summary()
            detail = self._build_description(page_summary)
            return result(self.name, "short website description", "INFO", detail, started)
        except Exception as exc:
            return fail(self.name, "short website description", exc, started)

    async def _collect_page_summary(self) -> dict:
        return await self.page.evaluate(
            """
            () => {
                const clean = value => (value || '').replace(/\\s+/g, ' ').trim();
                const metaDescription = document.querySelector('meta[name="description"], meta[property="og:description"]');
                const headings = Array.from(document.querySelectorAll('h1, h2'))
                    .map(element => clean(element.innerText))
                    .filter(Boolean)
                    .slice(0, 5);
                return {
                    url: location.href,
                    title: clean(document.title),
                    metaDescription: clean(metaDescription && metaDescription.content),
                    headings,
                    bodyText: clean(document.body ? document.body.innerText : '').slice(0, 2500),
                    linkCount: document.querySelectorAll('a[href]').length,
                    formCount: document.querySelectorAll('form').length,
                    buttonCount: document.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                };
            }
            """
        )

    def _build_description(self, page_summary: dict) -> str:
        url = page_summary.get("url") or self.target_url
        title = page_summary.get("title") or urlparse(url).netloc or "this website"
        meta_description = page_summary.get("metaDescription") or ""
        headings = page_summary.get("headings") or []
        body_text = page_summary.get("bodyText") or ""
        source_text = " ".join([title, meta_description, " ".join(headings), body_text]).lower()
        role = self._infer_role(source_text, page_summary)

        signals = []
        if title:
            signals.append(f"title is '{title}'")
        if headings:
            signals.append(f"main headings include {', '.join(headings[:3])}")
        if page_summary.get("formCount", 0):
            signals.append(f"{page_summary['formCount']} form(s)")
        if page_summary.get("buttonCount", 0):
            signals.append(f"{page_summary['buttonCount']} button/control(s)")
        if page_summary.get("linkCount", 0):
            signals.append(f"{page_summary['linkCount']} link(s)")

        reason = "; ".join(signals[:4]) or "the visible page text and structure"
        return f"Role: {role}. Reason: {reason}."

    def _infer_role(self, source_text: str, page_summary: dict) -> str:
        keyword_roles = [
            (("shop", "store", "cart", "checkout", "product", "price", "inventory"), "an e-commerce or product browsing website"),
            (("login", "sign in", "account", "password", "logout"), "an authentication or account access website"),
            (("dashboard", "analytics", "admin", "report", "metric"), "a dashboard or management website"),
            (("article", "blog", "news", "post"), "a content or publishing website"),
            (("portfolio", "project", "resume", "work"), "a portfolio or project showcase website"),
            (("contact", "service", "company", "about", "booking"), "a business or service information website"),
            (("signup", "register", "subscribe", "form"), "a signup or data collection website"),
        ]
        for keywords, role in keyword_roles:
            if any(keyword in source_text for keyword in keywords):
                return role
        if page_summary.get("formCount", 0):
            return "a website that collects visitor input through forms"
        return "a website that presents information and lets visitors navigate its content"
