"""Entry point for autonomous QA runs."""

from agents.orchestrator import Orchestrator
from config import ENV_PATH, TARGET_URL
from db.database import initialize_database
from reports.report_builder import build_report_data
from reports.html_report import render_html_report
from tools.browser_tool import close_browser, launch_browser
from tools.log_tool import log_step



async def run(target_url: str | None = None) -> dict:
    """Initialize services, run agents, and write the HTML report."""
    selected_url = target_url or TARGET_URL
    log_step("Initializing JSON history")
    initialize_database()
    log_step(f"Reading .env from: {ENV_PATH}")
    log_step(f"Target URL: {selected_url}")
    log_step("Launching Chromium")
    browser, page = await launch_browser()

    try:
        log_step("Starting QA agents")
        orchestrator = Orchestrator(page, selected_url)
        results = await orchestrator.run()
        log_step("Building report data")
        report_data = build_report_data(results, selected_url)
        log_step("Rendering HTML report")
        report_path = render_html_report(report_data)
        log_step(f"Report written to: {report_path}")
        return {"report_path": report_path, "report_data": report_data}
    finally:
        log_step("Closing Chromium")
        await close_browser(browser)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
